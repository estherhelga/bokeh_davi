import pandas as pd
from bokeh.plotting import figure, curdoc
from bokeh.models import ColumnDataSource, HoverTool, MultiSelect, Select, Slider, Span, Legend, LegendItem
from bokeh.layouts import column, row

# Load data
columns_to_load = ["champion", "team_position", "win", "side", "ally_1", "ally_2", "ally_3", "ally_4", "ally_5"]
df = pd.read_csv("cleaned_data.csv", usecols=columns_to_load)

# Ensure 'win' column is boolean
df['win'] = df['win'].astype(bool)

# Define mapping from roles to ally columns
role_column_map = {
    "TOP": ["ally_2", "ally_3", "ally_4", "ally_5"],      # Exclude TOP (ally_1)
    "JUNGLE": ["ally_1", "ally_3", "ally_4", "ally_5"],   # Exclude JUNGLE (ally_2)
    "MID": ["ally_1", "ally_2", "ally_4", "ally_5"],      # Exclude MID (ally_3)
    "ADC": ["ally_1", "ally_2", "ally_3", "ally_5"],      # Exclude ADC (ally_4)
    "SUP": ["ally_1", "ally_2", "ally_3", "ally_4"]       # Exclude SUP (ally_5)
}

# Mapping of ally column numbers to roles
ally_role_map = {
    "1": "TOP", "2": "Jungle", "3": "Mid", "4": "ADC", "5": "Support"
}

# Define initial champion, role, ally role, and minimum games
initial_champion = "Aatrox"
initial_role = "TOP"
initial_ally_role = "Jungle"  # Default ally role to Jungle
initial_min_games = 30        # Minimum games threshold

# Function to calculate average win rate for the chosen champion
def calculate_champion_average_win_rate(champion):
    champion_df = df[df['champion'] == champion]
    avg_win_rate = champion_df['win'].mean() * 100  # Convert to percentage
    print(f"Average win rate for {champion}: {avg_win_rate:.2f}%")
    return avg_win_rate

# Calculate win rates based on selected champion, role, ally role, and min games
def calculate_win_rates(champion, role, ally_role, min_games, avg_win_rate):
    print(f"Calculating win rates for Champion: {champion}, Role: {role}, Ally Role: {ally_role}, Min Games: {min_games}")
    # Step 1: Filter for games where the player is using the selected champion and in the specified role
    filtered_df = df[(df['champion'] == champion) & (df['team_position'] == role)]
    
    # Step 2: Identify the relevant ally column based on the selected ally role
    ally_column = [col for col, r in ally_role_map.items() if r == ally_role]
    if ally_column:
        ally_column = f"ally_{ally_column[0]}"  # e.g., ally_2 for Jungle role
    else:
        return pd.DataFrame()  # Return an empty DataFrame if no valid ally role is selected
    
    # Step 3: Filter out games where the selected champion appears in the ally role
    filtered_df = filtered_df[filtered_df[ally_column] != champion]
    
    # Step 4: Calculate win rate specifically for the ally champion in this role
    # Group by the specific ally role column, only counting games where this ally role is filled by a given champion
    ally_win_rates = (
        filtered_df
        .groupby(ally_column)['win']
        .agg(['mean', 'size'])  # Mean win rate and number of games
        .reset_index()
    )
    
    # Step 5: Prepare columns and filter by minimum games
    ally_win_rates.columns = ['ally_champion', 'win_rate', 'n_games']
    ally_win_rates['win_rate_percent'] = (ally_win_rates['win_rate'] * 100).round(2)
    ally_win_rates['role'] = ally_role  # Store the ally role information
    
    # Step 6: Assign color based on win rate relative to champion average
    ally_win_rates['color'] = ally_win_rates['win_rate_percent'].apply(lambda x: '#2b93b6' if x >= avg_win_rate else '#e54635')
    print("Data prepared with color column:", ally_win_rates.head())
    
    # Step 7: Filter allies with at least min_games
    ally_win_rates = ally_win_rates[ally_win_rates['n_games'] >= min_games]
    
    # Step 8: Sort by win rate for clarity
    ally_win_rates = ally_win_rates.drop_duplicates(subset=['ally_champion']).sort_values(by="win_rate", ascending=False)
    return ally_win_rates

# Calculate the champion's average win rate
champion_avg_win_rate = calculate_champion_average_win_rate(initial_champion)

# Calculate initial win rates and select the top 10 allies with at least 30 games
initial_win_rates = calculate_win_rates(initial_champion, initial_role, initial_ally_role, initial_min_games, champion_avg_win_rate)
top_10_allies = initial_win_rates.head(10)  # Select top 10 allies
source = ColumnDataSource(top_10_allies)  # Initialize the data source with top 10 allies

# Create figure
p = figure(x_range=list(top_10_allies['ally_champion'].unique()), height=400,
           title=f"Win Rate with {initial_ally_role} Allies as {initial_champion} ({initial_role})",
           toolbar_location=None, tools="")

# Plot bars with dynamic colors
vbar = p.vbar(x='ally_champion', top='win_rate_percent', width=0.5, source=source, line_color="white", fill_color='color')

# Add HoverTool
hover = HoverTool(tooltips=[("Win Rate", "@win_rate_percent%"), ("Games Played", "@n_games")])
p.add_tools(hover)

# Set y-axis properties and ensure average win rate is always shown
p.y_range.start = 0
p.y_range.end = 100
p.yaxis.axis_label = "Win Rate (%)"

# Add a dashed line at the champion's average win rate to show the threshold
midline = Span(location=champion_avg_win_rate, dimension='width', line_color='black', line_dash='dashed', line_width=2)
p.add_layout(midline)

# Add an invisible line for the "Average Win Rate" legend entry
avg_line_glyph = p.line(x=[0, 1], y=[champion_avg_win_rate, champion_avg_win_rate], 
                        line_color="black", line_dash="dashed", line_width=2, visible=False)

# Keep the above and below average win rate bars invisible for the legend
above_avg_glyph = p.vbar(x=[0], top=[champion_avg_win_rate], fill_color='#2b93b6', line_color='#2b93b6', width=0.1, visible=False)
below_avg_glyph = p.vbar(x=[0], top=[champion_avg_win_rate], fill_color='#e54635', line_color='#e54635', width=0.1, visible=False)

# Configure the legend items with the line for "Average Win Rate"
legend_items = [
    LegendItem(label="Average Win Rate", renderers=[avg_line_glyph]),  # Use line for dashed line
    LegendItem(label="Above Average Win Rate", renderers=[above_avg_glyph]),
    LegendItem(label="Below Average Win Rate", renderers=[below_avg_glyph])
]
legend = Legend(items=legend_items, location="top_right", label_text_font_size="10pt")

p.add_layout(legend)

# Rotate x-axis labels
p.xaxis.major_label_orientation = 0.785  # Rotate labels by 45 degrees (0.785 radians)

# Champion, Role, and Ally Role Selection Widgets
champion_select = Select(title="Select Your Champion:", value=initial_champion,
                         options=sorted(df['champion'].unique().tolist()))
role_select = Select(title="Select Your Role:", value=initial_role, options=list(role_column_map.keys()))
ally_role_select = Select(title="Select Ally Role:", value=initial_ally_role, options=list(ally_role_map.values()))

# Minimum Games Slider
min_games_slider = Slider(title="Minimum Games", value=initial_min_games, start=10, end=100, step=10)

# Ally MultiSelect widget initialized with top 10 allies
ally_select = MultiSelect(title="Select Allies:", value=top_10_allies['ally_champion'].tolist(),
                          options=list(initial_win_rates['ally_champion'].unique()))

# Update plot based on selected champion, role, ally role, min games, and allies
def update_plot(attr, old, new):
    selected_champion = champion_select.value
    selected_role = role_select.value
    selected_ally_role = ally_role_select.value
    min_games = min_games_slider.value
    avg_win_rate = calculate_champion_average_win_rate(selected_champion)
    selected_win_rates = calculate_win_rates(selected_champion, selected_role, selected_ally_role, min_games, avg_win_rate)
    
    # Update ally selection options and data based on champion, role, ally role, and min games
    unique_allies = list(selected_win_rates['ally_champion'].unique())
    ally_select.options = unique_allies  # Update ally options
    
    # Default to top 10 allies if there are no selections made
    if not ally_select.value:
        top_10_allies = selected_win_rates.head(10)
        ally_select.value = top_10_allies['ally_champion'].tolist()
    
    # Filter data for selected allies
    selected_allies = ally_select.value
    filtered_data = selected_win_rates[selected_win_rates['ally_champion'].isin(selected_allies)]
    
    # Update data source and x_range factors, ensuring unique values
    source.data = ColumnDataSource.from_df(filtered_data)
    p.x_range.factors = list(filtered_data['ally_champion'].unique())  # Ensure x_range is unique
    p.title.text = f"Win Rate with {selected_ally_role} Allies as {selected_champion} ({selected_role})"
    
    # Update the dashed line for the average win rate
    midline.location = avg_win_rate

# Attach callback to selectors
champion_select.on_change('value', update_plot)
role_select.on_change('value', update_plot)
ally_role_select.on_change('value', update_plot)
min_games_slider.on_change('value', update_plot)
ally_select.on_change('value', update_plot)

# Layout setup with additional ally role selector and minimum games slider
layout = column(champion_select, role_select, ally_role_select, min_games_slider, ally_select, p)

# Add layout to document
curdoc().add_root(layout)



