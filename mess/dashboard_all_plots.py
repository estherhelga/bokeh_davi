import pandas as pd
from tqdm import tqdm
from bokeh.plotting import figure, curdoc
from bokeh.layouts import column, row
from bokeh.models import HoverTool, Select, ColumnDataSource, FactorRange

# Load only necessary columns
columns_to_load = ["win", "team_position", "champion", "lane_opponent", "kills", "deaths", "assists", "gold_earned", "total_minions_killed", "max_cs_advantage_on_lane_opponent", "ally_1", "ally_2", "ally_3", "ally_4", "enemy_1", "enemy_2", "enemy_3", "enemy_4", "enemy_5"]
df = pd.read_csv("combined_matches.csv", usecols=columns_to_load)
df['win'] = df['win'].astype(int)

tqdm.pandas()  # Enable tqdm for pandas
df = pd.read_csv("combined_matches.csv", usecols=columns_to_load, engine='python').progress_apply(lambda x: x)  # engine='python' necessary to apply tqdm
df['win'] = df['win'].astype(int)

# Check column names to ensure they match what is being used in the plot
print("Available columns:", df.columns)

# Create a ColumnDataSource for dynamic updates
source = ColumnDataSource(data=dict())

# Champion selection widget
champion_select = Select(title="Select Champion:", value="Aatrox", options=["Aatrox", "Camille", "Gnar"])

# Initial figure for the bar chart, now with FactorRange for categorical axis
p3 = figure(title="Champion Win Rates", x_axis_label="Champion", y_axis_label="Win Rate (%)", width=600, height=400, x_range=FactorRange())

# Initial renderers to avoid "missing renderer" warnings
r3 = p3.vbar(x='champion', top='win', width=0.9, source=source)

# Function to update the plots
def update_plots(attr, old, new):
    selected_champion = champion_select.value
    # Filter the data for the selected champion
    selected_data = df[df["champion"] == selected_champion]

    if not selected_data.empty:
        # Prepare data for ColumnDataSource (Ensure values are lists)
        source_data = {
            'deaths': selected_data['deaths'].tolist(),   # Ensure values are lists
            'kills': selected_data['kills'].tolist(),     # Ensure values are lists
            'champion': selected_data['champion'].tolist() # Ensure values are lists
        }
        source.data = source_data  # Update the source with filtered data
        
        # Print limited data for debugging
        print("Updated source data (sample):", {k: v[:5] for k, v in source_data.items()})  # Limiting the print output for readability
        
        # Update the bar chart for win rates
        champion_win_rates = selected_data.groupby('champion')['win'].mean() * 100
        p3.x_range.factors = list(champion_win_rates.index)

        # Update the ColumnDataSource for the bar chart
        new_win_source = ColumnDataSource(data=dict(champion=champion_win_rates.index, win=champion_win_rates.values))
        r3.data_source.data = dict(new_win_source.data)
    else:
        print("No data available for the selected champion")

# Create the scatter plot for kills vs. deaths
p1 = figure(title="Kills vs. Deaths", x_axis_label="Deaths", y_axis_label="Kills", width=600, height=400)
p1.scatter(x='deaths', y='kills', source=source, size=8, color="blue", alpha=0.6)

# Add hover tool for the scatter plot
hover1 = HoverTool(tooltips=[("Champion", "@champion"), ("Kills", "@kills"), ("Deaths", "@deaths")])
p1.add_tools(hover1)

# Create another empty figure for future data plots, e.g., Gold Distribution
p2 = figure(title="Distribution of Gold Earned", x_axis_label="Gold Earned", y_axis_label="Frequency", width=600, height=400)

# Set initial data for the plots before displaying them
update_plots(None, None, "Aatrox")

# Call update_plots whenever the champion selection changes
champion_select.on_change('value', update_plots)

# Layout and show
layout = column(champion_select, row(p1, p2), p3)
curdoc().add_root(layout)
