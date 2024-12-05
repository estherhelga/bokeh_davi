import pandas as pd
from bokeh.plotting import figure, show
from bokeh.models import ColumnDataSource, LinearColorMapper, ColorBar, HoverTool, Select, TextInput
from bokeh.layouts import column, row
from bokeh.io import curdoc
from bokeh.palettes import RdYlGn11

# -------------------------------------------------------------------------------- #
# Load Data                                                                        #
# -------------------------------------------------------------------------------- #

# Load preprocessed heatmap data
file_path = 'heatmap_data.csv'
heatmap_data = pd.read_csv(file_path)

# Ensure data structure
if heatmap_data.empty or not {'champion', 'lane_opponent', 'n_games'}.issubset(heatmap_data.columns):
    raise ValueError("Heatmap data is missing necessary columns or is empty.")

# Define metrics and labels
metrics = [
    "winrate",  # Add winrate as the first metric
    "normalized_lane_minions_first_10_minutes",
    "normalized_max_cs_advantage_on_lane_opponent",
    "normalized_max_level_lead_lane_opponent",
    "normalized_turret_plates_taken",
    "normalized_solo_kills",
    "normalized_deaths",
]

raw_metrics = [
    "winrate",
    "lane_minions_first_10_minutes",
    "max_cs_advantage_on_lane_opponent",
    "max_level_lead_lane_opponent",
    "turret_plates_taken",
    "solo_kills",
    "deaths",
]

metric_labels = [
    "Winrate",  # Label for winrate
    "CS First 10m",
    "CS Advantage",
    "Level Lead",
    "Turret Plates",
    "Solo Kills",
    "Deaths",
]

# Map metric labels to metrics
metric_map = dict(zip(metric_labels, metrics))
raw_metric_map = dict(zip(metric_labels, raw_metrics))

# -------------------------------------------------------------------------------- #
# Prepare Heatmap Data                                                             #
# -------------------------------------------------------------------------------- #

# Filter initial data for the first champion
default_champion = heatmap_data['champion'].unique()[0]
filtered_data = heatmap_data[heatmap_data['champion'] == default_champion]

# Create the initial ColumnDataSource for the heatmap
source = ColumnDataSource(data={
    "lane_opponent": [],
    "metric": [],
    "value": [],
    "raw_value": [],  # Add raw values for tooltip
    "n_games": [],  # Add number of games for tooltip
})

# Define color mappers for each metric
color_mappers = {
    "winrate": LinearColorMapper(palette=RdYlGn11[::-1], low=0, high=1),
    "normalized_lane_minions_first_10_minutes": LinearColorMapper(palette=RdYlGn11[::-1], low=0, high=1),
    "normalized_max_cs_advantage_on_lane_opponent": LinearColorMapper(palette=RdYlGn11[::-1], low=0, high=1),
    "normalized_max_level_lead_lane_opponent": LinearColorMapper(palette=RdYlGn11[::-1], low=0, high=1),
    "normalized_turret_plates_taken": LinearColorMapper(palette=RdYlGn11[::-1], low=0, high=1),
    "normalized_solo_kills": LinearColorMapper(palette=RdYlGn11[::-1], low=0, high=1),
    "normalized_deaths": LinearColorMapper(palette=RdYlGn11, low=1, high=0),  # Non-reversed colormap for Deaths
}

# -------------------------------------------------------------------------------- #
# Create Heatmap                                                                   #
# -------------------------------------------------------------------------------- #

# Create a figure for the heatmap
p = figure(
    title=f"Performance Metrics Against Opponents ({default_champion})",
    x_range=metric_labels,
    y_range=list(filtered_data['lane_opponent'].unique()),
    x_axis_label="Metrics",
    y_axis_label="Opponents",
    toolbar_location=None,
    tools=""
)

# Add rectangles for heatmap with dynamic colormappers
p.rect(
    x="metric",
    y="lane_opponent",
    width=1,
    height=1,
    source=source,
    fill_color={"field": "value", "transform": color_mappers["winrate"]},  # Placeholder, dynamically updated
    line_color=None
)

# Add a color bar for reference
color_bar = ColorBar(
    color_mapper=color_mappers["winrate"],  # Placeholder, dynamically updated
    label_standoff=12,
    location=(0, 0),
    orientation="vertical"
)
p.add_layout(color_bar, "right")

# Add hover tool for interactivity
hover = HoverTool(
    tooltips=[
        ("Metric", "@metric"),
        ("Opponent", "@lane_opponent"),
        ("Normalized Value", "@value{0.2f}"),
        ("Mean Value", "@raw_value{0.2f}"),
        ("Number of Games", "@n_games"),  # Show number of games
    ]
)
p.add_tools(hover)

# -------------------------------------------------------------------------------- #
# Dynamic Updates                                                                  #
# -------------------------------------------------------------------------------- #

def update_heatmap(attr, old, new):
    """
    Update the heatmap based on the selected champion and minimum games threshold.
    Normalize metrics dynamically for the selected champion.
    """
    selected_champion = champion_select.value
    selected_sort_metric = metric_map[sort_select.value]  # Metric to sort by
    min_games = int(min_games_input.value) if min_games_input.value.isdigit() else 50

    # Filter data for the selected champion and minimum games
    updated_data = heatmap_data[
        (heatmap_data['champion'] == selected_champion) & 
        (heatmap_data['n_games'] >= min_games)
    ]

    # Sort the data by the selected metric
    updated_data = updated_data.sort_values(by=selected_sort_metric, ascending=False)

    # Prepare data for Bokeh's ColumnDataSource
    new_source_data = {
        "lane_opponent": [],
        "metric": [],
        "value": [],
        "raw_value": [],  # Add raw metric values
        "n_games": [],  # Add number of games
    }

    for metric, label in zip(metrics, metric_labels):
        raw_metric = raw_metric_map[label]  # Get the corresponding raw metric
        if metric == "winrate":
            # Use winrate directly (already normalized)
            for _, row in updated_data.iterrows():
                new_source_data["lane_opponent"].append(row["lane_opponent"])
                new_source_data["metric"].append(label)
                new_source_data["value"].append(row["winrate"])
                new_source_data["raw_value"].append(row["winrate"])
                new_source_data["n_games"].append(row["n_games"])  # Add number of games
        else:
            # Handle normalized metrics
            metric_min = updated_data[metric].min()
            metric_max = updated_data[metric].max()

            # Avoid divide-by-zero errors
            if metric_max > metric_min:
                updated_data[metric] = (
                    (updated_data[metric] - metric_min) / (metric_max - metric_min)
                )
            else:
                updated_data[metric] = 0.5  # Neutral value

            for _, row in updated_data.iterrows():
                new_source_data["lane_opponent"].append(row["lane_opponent"])
                new_source_data["metric"].append(label)
                new_source_data["value"].append(row[metric])
                new_source_data["raw_value"].append(row[raw_metric])
                new_source_data["n_games"].append(row["n_games"])  # Add number of games

    # Update the ColumnDataSource
    source.data = new_source_data

    # Dynamically update the y_range of the plot
    p.y_range.factors = list(updated_data['lane_opponent'].unique())
    p.title.text = f"Performance Metrics Against Opponents ({selected_champion})"

    # Update the color bar to match the current metric
    selected_metric = metric_map[sort_select.value]
    color_bar.color_mapper = color_mappers[selected_metric]

# -------------------------------------------------------------------------------- #
# Widgets                                                                          #
# -------------------------------------------------------------------------------- #

# Dropdown for champion selection
champion_select = Select(
    title="Select Champion:",
    value=default_champion,
    options=list(heatmap_data['champion'].unique())
)
champion_select.on_change("value", update_heatmap)

# Add a TextInput widget for the minimum games threshold with a default of 50
min_games_input = TextInput(title="Minimum Games Threshold:", value="50")
min_games_input.on_change("value", update_heatmap)

# Add a dropdown for sorting by metrics
sort_select = Select(
    title="Sort By Metric:",
    value="Winrate",
    options=metric_labels
)
sort_select.on_change("value", update_heatmap)

# -------------------------------------------------------------------------------- #
# Layout and Display                                                               #
# -------------------------------------------------------------------------------- #

# Initialize the heatmap with default champion data
update_heatmap(None, None, None)

# Layout and display the figure
layout = column(row(min_games_input, sort_select), champion_select, p)
curdoc().add_root(layout)
