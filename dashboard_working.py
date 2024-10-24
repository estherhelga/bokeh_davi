import pandas as pd
from bokeh.plotting import figure, curdoc
from bokeh.models import ColumnDataSource, HoverTool, Select, MultiChoice, Div
from bokeh.layouts import column
from itertools import cycle

# Load necessary columns including the "win" column (which contains TRUE/FALSE)
columns_to_load = ["champion", "max_cs_advantage_on_lane_opponent", "max_level_lead_lane_opponent", "lane_opponent", "win"]
df = pd.read_csv("scatterplot_filtered_data.csv", usecols=columns_to_load)

# Filter opponents with at least 15 games
opponent_counts = df['lane_opponent'].value_counts()
df_filtered = df[df['lane_opponent'].isin(opponent_counts[opponent_counts >= 15].index)]

# Check and convert data types
df_filtered['max_cs_advantage_on_lane_opponent'] = pd.to_numeric(df_filtered['max_cs_advantage_on_lane_opponent'], errors='coerce')
df_filtered['max_level_lead_lane_opponent'] = pd.to_numeric(df_filtered['max_level_lead_lane_opponent'], errors='coerce')
df_filtered['win'] = df_filtered['win'].map({True: 'Win', False: 'Loss'})  # Map TRUE to 'Win' and FALSE to 'Loss'

# Create a ColumnDataSource for dynamic updates
source = ColumnDataSource(data=dict())

# Champion selection widget
champion_select = Select(title="Select Your Champion:", value="Aatrox", options=list(df_filtered['champion'].unique()))

# MultiChoice dropdown widget for selecting opponent champions (sorted alphabetically)
opponent_options = sorted(list(df_filtered['lane_opponent'].unique()))  # Sort opponents alphabetically
opponent_dropdown = MultiChoice(value=[], options=opponent_options, title="Select Opponent Champions (max 3)")
warning_div = Div(text="")  # Div to show a warning if more than 3 selections

# Create the scatter plot for max_cs_advantage_on_lane_opponent vs. max_level_lead_lane_opponent
p1 = figure(title="Max CS Advantage vs. Max Level Lead", 
            x_axis_label="Max Level Lead on Lane Opponent", 
            y_axis_label="Max CS Advantage on Lane Opponent", 
            width=900, height=600)

# Add hover tool for the scatter plot
hover1 = HoverTool(tooltips=[("Champion", "@champion"), 
                             ("Opponent", "@lane_opponent"),
                             ("Max CS Advantage", "@max_cs_advantage_on_lane_opponent"), 
                             ("Max Level Lead", "@max_level_lead_lane_opponent"),
                             ("Game Outcome", "@win")])
p1.add_tools(hover1)

# Define a color palette for up to 3 selected opponents
colors = cycle(["blue", "green", "orange"])

# Initial scatter plot
scatter = p1.scatter(x='max_level_lead_lane_opponent', y='max_cs_advantage_on_lane_opponent', 
                     source=source, size=8, color='color', marker='shape', fill_alpha=0.6)

# Function to update the plot colors and shapes based on selected champion, opponent champions, and win/loss
def update_plots(attr, old, new):
    selected_champion = champion_select.value  # Get selected champion
    selected_opponents = opponent_dropdown.value  # Get selected opponents
    
    # Check if more than 3 opponents are selected
    if len(selected_opponents) > 3:
        warning_div.text = '<p style="color:red;">You can select a maximum of 3 opponents.</p>'
        return
    else:
        warning_div.text = ""  # Clear warning if less than or equal to 3 opponents selected

    # Filter data for the selected champion
    selected_data = df_filtered[df_filtered["champion"] == selected_champion]
    
    if not selected_data.empty:
        color_column = []
        shape_column = []

        # Assign unique colors to each selected opponent
        opponent_color_map = {opponent: next(colors) for opponent in selected_opponents}

        # Loop through the selected champion's data to set the colors and shapes
        for index, row in selected_data.iterrows():
            if row['lane_opponent'] in selected_opponents:
                # Assign color based on opponent and shape based on win/loss
                color_column.append(opponent_color_map[row['lane_opponent']])
                if row['win'] == 'Win':
                    shape_column.append('triangle')  # Wins as triangles
                else:
                    shape_column.append('square')  # Losses as squares
            else:
                color_column.append('gray')  # Non-highlighted matches remain gray
                shape_column.append('circle')  # Non-highlighted matches are circles
        
        # Update the data source with filtered data for the selected champion
        source.data = {
            'max_cs_advantage_on_lane_opponent': selected_data['max_cs_advantage_on_lane_opponent'],
            'max_level_lead_lane_opponent': selected_data['max_level_lead_lane_opponent'],
            'champion': selected_data['champion'],
            'lane_opponent': selected_data['lane_opponent'],
            'color': color_column,  # Add color column to the source
            'shape': shape_column,  # Add shape column for wins/losses
            'win': selected_data['win'],  # Add win column for tooltip
        }

# Set initial data for the plots before displaying them
update_plots(None, None, "Aatrox")

# Call update_plots whenever the champion or opponent selection changes
champion_select.on_change('value', update_plots)
opponent_dropdown.on_change('value', update_plots)

# Layout with a warning message for when too many opponents are selected
curdoc().add_root(column(champion_select, opponent_dropdown, warning_div, p1))

