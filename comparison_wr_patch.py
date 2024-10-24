import pandas as pd
from bokeh.io import curdoc
from bokeh.layouts import column, row
from bokeh.models import ColumnDataSource, Select, HoverTool
from bokeh.plotting import figure
from bokeh.transform import dodge

# Load the filtered data from CSV
file_path = 'filtered_patch_data.csv'  # Ensure this is the correct path to your CSV
data = pd.read_csv(file_path)

# Function to correctly format patch numbers (e.g., 14.2 -> 14.02)
def format_patch(patch):
    parts = str(patch).split(".")
    if len(parts) > 1 and len(parts[1]) == 1:  # If there is one digit after the dot, pad with a zero
        return f"{parts[0]}.{parts[1].zfill(2)}"
    return patch

# Apply the patch formatting
data['game_version'] = data['game_version'].apply(format_patch)

# Convert to numeric for sorting purposes after formatting
data['game_version'] = pd.to_numeric(data['game_version'], errors='coerce')

# Filter for game versions between 14.11 and 14.19
filtered_data = data[(data['game_version'] >= 14.11) & (data['game_version'] <= 14.19)]

# Prepare initial data for the first champion (Aatrox)
champion = 'Aatrox'
champion_data = filtered_data[filtered_data['champion'] == champion]

# Group by patch and sum wins and losses to ensure unique patches
grouped_data = champion_data.groupby('game_version').agg({'wins': 'sum', 'losses': 'sum'}).reset_index()

# Calculate total games and win rates (win rate as percentage)
grouped_data['total_games'] = grouped_data['wins'] + grouped_data['losses']
grouped_data['win_rate'] = (grouped_data['wins'] / grouped_data['total_games']) * 100
grouped_data['loss_rate'] = 100 - grouped_data['win_rate']  # Loss rate is complementary to win rate

# Filter out patches with fewer than 20 total games
grouped_data = grouped_data[grouped_data['total_games'] >= 20]

# Sort patches numerically
grouped_data = grouped_data.sort_values('game_version')

# Convert patches back to strings for proper display in the plot
grouped_data['game_version'] = grouped_data['game_version'].astype(str)

# Create a ColumnDataSource for the initial data
source = ColumnDataSource(data=dict(
    patch=grouped_data['game_version'],
    win_rate=grouped_data['win_rate'],
    loss_rate=grouped_data['loss_rate'],
    total_games=grouped_data['total_games'],  # Add total games to the source
    champion=[champion] * len(grouped_data)  # Add the champion name to the source
))

# Create the figure for the bar chart (now using percentages)
p = figure(x_range=source.data['patch'], height=400, title=f"Win/Loss Percentage per Patch for {champion}",
           toolbar_location=None, tools="", width=800, y_range=(0, 100))

# Add bars for win rate and loss rate, using dodge to place them next to each other
win_bars = p.vbar(x=dodge('patch', -0.15, range=p.x_range), top='win_rate', width=0.3, source=source, color="green", legend_label="Win Rate (%)")
loss_bars = p.vbar(x=dodge('patch', 0.15, range=p.x_range), top='loss_rate', width=0.3, source=source, color="red", legend_label="Loss Rate (%)")

# Set plot properties
p.x_range.range_padding = 0.05
p.xgrid.grid_line_color = None
p.legend.location = "top_left"
p.legend.orientation = "horizontal"
p.yaxis.axis_label = "Win/Loss Percentage"
p.xaxis.axis_label = "Patch"

# Add HoverTool specifically for win bars (showing win rate and total games)
hover_wins = HoverTool(renderers=[win_bars])
hover_wins.tooltips = [("Patch", "@patch"), ("Champion", "@champion"), ("Win Rate (%)", "@win_rate{0.0}%"), ("Total Games", "@total_games")]

# Add HoverTool specifically for loss bars (showing loss rate and total games)
hover_losses = HoverTool(renderers=[loss_bars])
hover_losses.tooltips = [("Patch", "@patch"), ("Champion", "@champion"), ("Loss Rate (%)", "@loss_rate{0.0}%"), ("Total Games", "@total_games")]

# Add the hover tools to the plot
p.add_tools(hover_wins, hover_losses)

# Extract unique lane opponents from the dataset to dynamically populate the enemy dropdown
unique_lane_opponents = sorted(filtered_data['lane_opponent'].unique())
enemy_select = Select(title="Select Enemy Champion", value="None", options=["None"] + unique_lane_opponents)

# Line plot for specific matchup winrate
line_source = ColumnDataSource(data=dict(patch=[], winrate_vs_enemy=[]))
line = p.line(x='patch', y='winrate_vs_enemy', source=line_source, color="blue", line_width=2, legend_label="Win Rate vs Enemy (%)")

# Dropdown menu to select the champion
champion_select = Select(title="Select Champion", value="Aatrox", options=sorted(filtered_data['champion'].unique()))

# Callback function to update the plot when a different champion or enemy is selected
def update_plot(attr, old, new):
    selected_champion = champion_select.value
    selected_enemy = enemy_select.value
    
    # Filter data for selected champion
    new_data = filtered_data[filtered_data['champion'] == selected_champion]
    
    # Group the data by patch and sum the wins/losses
    new_grouped_data = new_data.groupby('game_version').agg({'wins': 'sum', 'losses': 'sum'}).reset_index()

    # Calculate total games and win rates
    new_grouped_data['total_games'] = new_grouped_data['wins'] + new_grouped_data['losses']
    new_grouped_data['win_rate'] = (new_grouped_data['wins'] / new_grouped_data['total_games']) * 100
    new_grouped_data['loss_rate'] = 100 - new_grouped_data['win_rate']

    # Filter out patches with fewer than 20 total games
    new_grouped_data = new_grouped_data[new_grouped_data['total_games'] >= 20]

    # Sort patches numerically
    new_grouped_data = new_grouped_data.sort_values('game_version')

    # Convert patches back to strings for the plot
    new_grouped_data['game_version'] = new_grouped_data['game_version'].astype(str)

    # Update the ColumnDataSource with new data
    source.data = dict(
        patch=new_grouped_data['game_version'],
        win_rate=new_grouped_data['win_rate'],
        loss_rate=new_grouped_data['loss_rate'],
        total_games=new_grouped_data['total_games'],
        champion=[selected_champion] * len(new_grouped_data)
    )
    
    # Update plot title
    p.title.text = f"Win/Loss Percentage per Patch for {selected_champion}"
    
    # Update x_range (patches) to fit new data
    p.x_range.factors = list(new_grouped_data['game_version'])

    # If an enemy champion is selected, update the line chart with matchup-specific data
    if selected_enemy != "None":
        enemy_data = new_data[new_data['lane_opponent'] == selected_enemy]  # Filter for matchup-specific data
        if not enemy_data.empty:
            enemy_grouped_data = enemy_data.groupby('game_version').agg({'wins': 'sum', 'losses': 'sum'}).reset_index()
            enemy_grouped_data['total_games'] = enemy_grouped_data['wins'] + enemy_grouped_data['losses']
            enemy_grouped_data['winrate_vs_enemy'] = (enemy_grouped_data['wins'] / enemy_grouped_data['total_games']) * 100
            
            # Update line chart for the specific matchup
            line_source.data = dict(
                patch=enemy_grouped_data['game_version'].astype(str),
                winrate_vs_enemy=enemy_grouped_data['winrate_vs_enemy']
            )
        else:
            line_source.data = dict(patch=[], winrate_vs_enemy=[])
    else:
        line_source.data = dict(patch=[], winrate_vs_enemy=[])

# Attach the callback to both dropdowns
champion_select.on_change("value", update_plot)
enemy_select.on_change("value", update_plot)

# Layout and add to document
layout = column(row(champion_select, enemy_select), p)
curdoc().add_root(layout)
curdoc().title = "Patch Win/Loss Percentage with Matchup Overlay"

