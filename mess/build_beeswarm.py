import pandas as pd
from bokeh.plotting import figure, curdoc
from bokeh.models import ColumnDataSource, HoverTool, Select
from bokeh.layouts import column

# Corrected file paths
cleaned_data_path = 'cleaned_data.csv'
items_data_path = 'items.csv'

cleaned_data = pd.read_csv(cleaned_data_path)
items_data = pd.read_csv(items_data_path)

# Filter for full items from the items dataset
full_items = items_data[items_data['Category'] == 'Full Item']['Item'].tolist()

# Melt the item columns in cleaned data for analysis
item_columns = ['item0', 'item1', 'item2', 'item3', 'item4', 'item5', 'item6']
cleaned_data[item_columns] = cleaned_data[item_columns].astype(str)  # Ensure consistent string type

# Helper function to filter data by champion and role
def filter_data_by_champion_and_role(df, champion, role):
    filtered_df = df[(df['champion'] == champion) & (df['team_position'] == role)]
    melted_items = filtered_df.melt(
        id_vars=['win'], 
        value_vars=item_columns, 
        value_name='item'
    )
    filtered_full_items = melted_items[melted_items['item'].isin(full_items)]
    return filtered_full_items

# Swarm layout calculation function
def calculate_swarm_layout(data, y_column, size_column):
    """
    Calculate x positions for a swarm plot, spreading out points to avoid overlap.
    """
    positions = []
    for _, row in data.iterrows():
        y = row[y_column]
        size = row[size_column] / 100  # Scale size for collision detection
        x = 0
        # Avoid overlaps by checking existing points
        while any(
            abs(existing_y - y) < size and abs(existing_x - x) < size
            for existing_x, existing_y in positions
        ):
            x += 0.2  # Increment x to avoid overlap
        positions.append((x, y))
    return pd.DataFrame({'x': [x for x, _ in positions], 'y': [y for _, y in positions]})

# Function to update the plot based on dropdown selections
def update_plot(attr, old, new):
    selected_champion = champion_select.value
    selected_role = role_select.value
    print(f"Selected Champion: {selected_champion}, Role: {selected_role}")
    
    filtered_data = filter_data_by_champion_and_role(cleaned_data, selected_champion, selected_role)
    print(f"Filtered Data Size: {filtered_data.shape}")
    
    # Recalculate frequencies and win rate for the filtered data
    total_count = len(filtered_data)
    item_stats = filtered_data.groupby('item').agg(
        count=('win', 'size'),
        win_rate=('win', 'mean')
    ).reset_index()

    if total_count > 0:
        item_stats['frequency'] = (item_stats['count'] / total_count) * 100  # Convert to percentage
    else:
        item_stats['frequency'] = 0

    item_stats['size'] = (item_stats['win_rate'] - 0.5).abs() * 100

    # Apply swarm layout to calculate x-coordinates
    swarm_positions = calculate_swarm_layout(item_stats, 'frequency', 'size')
    item_stats['x'] = swarm_positions['x']

    # Update the data source
    source.data = {
        'item': item_stats['item'],
        'frequency': item_stats['frequency'],
        'win_rate': item_stats['win_rate'],
        'size': item_stats['size'],
        'x': item_stats['x']
    }

# Get unique champions and roles
unique_champions = cleaned_data['champion'].unique().tolist()
unique_roles = cleaned_data['team_position'].unique().tolist()

# Dropdowns for champion and role
champion_select = Select(title="Champion", value=unique_champions[0], options=unique_champions)
role_select = Select(title="Role", value=unique_roles[0], options=unique_roles)

# Add callbacks for dropdown menus
champion_select.on_change("value", update_plot)
role_select.on_change("value", update_plot)

# Initial data for the first champion and role
initial_champion = champion_select.value
initial_role = role_select.value
initial_data = filter_data_by_champion_and_role(cleaned_data, initial_champion, initial_role)

# Recalculate frequencies and win rate for the initial data
total_count = len(initial_data)
initial_item_stats = initial_data.groupby('item').agg(
    count=('win', 'size'),
    win_rate=('win', 'mean')
).reset_index()

if total_count > 0:
    initial_item_stats['frequency'] = (initial_item_stats['count'] / total_count) * 100  # Convert to percentage
else:
    initial_item_stats['frequency'] = 0

initial_item_stats['size'] = (initial_item_stats['win_rate'] - 0.5).abs() * 100

# Apply swarm layout for the initial plot
swarm_positions = calculate_swarm_layout(initial_item_stats, 'frequency', 'size')
initial_item_stats['x'] = swarm_positions['x']

# Create a ColumnDataSource
source = ColumnDataSource(initial_item_stats)

# Create the figure
plot = figure(
    title="Full Items by Champion and Role (Swarm Layout)",
    x_axis_label='X Coordinate (Swarm Layout)',
    y_axis_label='Frequency (%)',
    tools="pan,box_zoom,reset,save",
    width=800,
    height=600,
    y_range=(0, 100)  # Fixed range for frequencies
)

# Add scatter glyphs to the plot with swarm layout
plot.circle(
    x='x',  # Use swarm-calculated x-coordinates
    y='frequency',
    size='size',
    source=source,
    fill_alpha=0.6,
    line_color=None
)

# Add hover tool
hover = HoverTool(tooltips=[
    ("Item", "@item"),
    ("Frequency (%)", "@frequency{0.00}%"),
    ("Win Rate", "@win_rate{0.00%}")
])
plot.add_tools(hover)

# Layout for the dropdowns and the plot
layout = column(champion_select, role_select, plot)

# Add layout to Bokeh document
curdoc().add_root(layout)
