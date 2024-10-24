import pandas as pd
from bokeh.plotting import figure, curdoc
from bokeh.models import ColumnDataSource, HoverTool, Select, MultiChoice, Div
from bokeh.layouts import column

# Load the filtered dataset (which has been filtered to have at least 20 games)
df = pd.read_csv("scatterplot_filtered_data.csv")

# Calculate win rates and game count for each champion-opponent pair (as percentage)
win_rates = df.groupby(['champion', 'lane_opponent'])['win'].agg(['sum', 'count'])
win_rates['win_rate'] = (win_rates['sum'] / win_rates['count']) * 100  # Multiply by 100 to convert to percentage
win_rates.rename(columns={'count': 'game_count'}, inplace=True)

# Merge the win rates and game count back into the filtered DataFrame
df = df.merge(win_rates[['win_rate', 'game_count']], on=['champion', 'lane_opponent'], how='left')

# Create a ColumnDataSource for dynamic updates
source = ColumnDataSource(data=dict())

# Champion selection widget
champion_select = Select(title="Select Your Champion:", value="Aatrox", options=list(df['champion'].unique()))

# Opponent dropdown widget (sorted alphabetically)
valid_opponents = df['lane_opponent'].unique().tolist()
opponent_dropdown = MultiChoice(value=[], options=sorted(valid_opponents), title="Select Opponent Champions (max 3)")

# Warning div to show when more than 3 opponents are selected (inline style for red text)
warning_div = Div(text="<span style='color: red;'>You can select a maximum of 3 opponents.</span>")
warning_div.text = ""  # Initially empty

# X-axis dropdown for selecting which metric to plot
x_axis_options = ['max_level_lead_lane_opponent', 'max_cs_advantage_on_lane_opponent', 'lane_minions_first_10_minutes']
x_axis_select = Select(title="Select X-axis metric:", value='max_level_lead_lane_opponent', options=x_axis_options)

# Create the scatter plot for win_rate vs. chosen X-axis
p1 = figure(title="Win Rate vs. Selected Metric", 
            x_axis_label="Max Level Lead on Lane Opponent",  # Will update dynamically
            y_axis_label="Win Rate (%)",  # Update to show win rate as percentage
            width=900, height=600)

# Set y-axis limits from 0 to 100 to reflect percentage
p1.y_range.start = 0
p1.y_range.end = 100

# Create the scatter glyph for the plot (initially empty)
scatter = p1.scatter(x='x_value', y='win_rate', source=source, color='color', size=8, alpha=0.6)

# Add hover tool for the scatter plot
hover1 = HoverTool(tooltips=[("Champion", "@champion"), 
                             ("Opponent", "@lane_opponent"),
                             ("X Value", "@x_value"),
                             ("Win Rate", "@win_rate"),
                             ("Games Played", "@game_count")])
p1.add_tools(hover1)

# Function to update the plot based on selected options
def update_plots(attr, old, new):
    selected_champion = champion_select.value  # Get selected champion
    selected_opponents = opponent_dropdown.value  # Get selected opponents
    selected_x_axis = x_axis_select.value  # Get selected x-axis metric

    # Filter data for the selected champion
    selected_data = df[df["champion"] == selected_champion]

    # If no opponents are selected, show all data in gray
    if not selected_opponents:
        color_column = ['gray'] * len(selected_data)
        x_values = selected_data[selected_x_axis].values
    else:
        color_column = []
        x_values = selected_data[selected_x_axis].values

        # Assign colors to selected opponents: RED, BLUE, PURPLE (up to 3 opponents)
        color_map = ['red', 'blue', 'purple']
        
        # Avoid out of index range error by assigning color only for available opponents
        opponent_colors = {opponent: color_map[i] for i, opponent in enumerate(selected_opponents[:3])}

        # Assign colors to data points
        for index, row in selected_data.iterrows():
            if row['lane_opponent'] in selected_opponents:
                # Use the color mapping for selected opponents
                color_column.append(opponent_colors.get(row['lane_opponent'], 'gray'))
            else:
                # Non-highlighted matches remain gray
                color_column.append('gray')

    # Update the data source with filtered data for the selected champion and opponents
    source.data = {
        'x_value': x_values,
        'win_rate': selected_data['win_rate'],  # Win rate as percentage
        'champion': selected_data['champion'],
        'lane_opponent': selected_data['lane_opponent'],
        'color': color_column,  # Add color column to the source
        'game_count': selected_data['game_count'],
    }

    # Update the x-axis label dynamically based on the selected metric
    p1.xaxis.axis_label = selected_x_axis.replace('_', ' ').title()

# Function to enforce opponent selection limit
def validate_opponent_selection(attr, old, new):
    if len(opponent_dropdown.value) > 3:
        warning_div.text = "<span style='color: red;'>You can select a maximum of 3 opponents.</span>"
        # Keep the first 3 selected opponents and discard the rest
        opponent_dropdown.value = opponent_dropdown.value[:3]
    else:
        warning_div.text = ""  # Clear the warning if selections are valid
    update_plots(attr, old, new)

# Set initial data for the plots before displaying them
update_plots(None, None, "Aatrox")

# Call update_plots whenever the champion, opponent, or X-axis metric changes
champion_select.on_change('value', update_plots)
opponent_dropdown.on_change('value', validate_opponent_selection)
x_axis_select.on_change('value', update_plots)

# Layout with a warning message for when too many opponents are selected
curdoc().add_root(column(champion_select, opponent_dropdown, x_axis_select, warning_div, p1))
