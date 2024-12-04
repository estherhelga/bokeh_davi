import pandas as pd
from bokeh.layouts import column, row
from bokeh.models import Select, TextInput, MultiSelect, ColumnDataSource, HoverTool, Span, Spacer, Button, Div, LinearColorMapper, ColorBar
from bokeh.plotting import figure, curdoc, show
from bokeh.models import CustomJSTickFormatter, Label
from bokeh.palettes import linear_palette
from bokeh.palettes import Blues256
import numpy as np
from sklearn.neighbors import KernelDensity
from bokeh.palettes import RdYlGn11


# -------------------------------------------------------------------------------- #
# Data Loading and Initialization                                                  #
# -------------------------------------------------------------------------------- #

# Load data with error handling
try:
    file_path = 'cleaned_data.csv'
    df = pd.read_csv(file_path)
    df['win'] = df['win'].astype(bool)
except FileNotFoundError:
    raise RuntimeError(f"File not found: {file_path}. Ensure the file exists.")
except pd.errors.ParserError as e:
    raise RuntimeError(f"Error parsing CSV file {file_path}: {e}")

# Validate required columns exist in the DataFrame
required_columns = {'champion', 'win', 'enemy_1', 'enemy_2', 'enemy_3', 'enemy_4', 'enemy_5'}
if not required_columns.issubset(df.columns):
    raise RuntimeError(f"Missing required columns in the dataset. Expected: {required_columns}")

# Extract unique champions and roles
champions = sorted(df['champion'].unique().tolist())
roles = ['TOP', 'JUNGLE', 'MID', 'ADC', 'SUP']

# Load additional item data with error handling
try:
    item_data = pd.read_csv('final_item_champion_stats.csv')
    item_data_filtered = item_data[item_data['Category'].isin(['Full Item'])].copy()

    # Add frequency percentage column
    item_data_filtered['frequency_percentage'] = (
        item_data_filtered['occurrence_count'] / item_data_filtered['total_games_champion'] * 100
    )

    # Calculate win rate as a percentage
    item_data_filtered['win_rate'] = (
        item_data_filtered['win_count'] / item_data_filtered['occurrence_count'] * 100
    )
    # Filter items with a frequency percentage of 3 or higher
    item_data_filtered = item_data_filtered[item_data_filtered['frequency_percentage'] >= 3]


except FileNotFoundError:
    raise RuntimeError("File not found: final_item_champion_stats.csv. Ensure the file exists.")
except pd.errors.ParserError as e:
    raise RuntimeError(f"Error parsing CSV file: {e}")

# Load heatmap data with error handling
try:
    heatmap_file_path = 'heatmap_data.csv'
    heatmap_data = pd.read_csv(heatmap_file_path)

    # Validate necessary columns
    required_columns = {'champion', 'lane_opponent', 'n_games'}
    if not required_columns.issubset(heatmap_data.columns):
        raise ValueError(f"Missing required columns in heatmap data. Expected: {required_columns}")

    # Additional metrics columns (ensure normalization-ready data)
    metrics = [
        "winrate",  # Add winrate as the first metric
        "normalized_lane_minions_first_10_minutes",
        "normalized_max_cs_advantage_on_lane_opponent",
        "normalized_max_level_lead_lane_opponent",
        "normalized_turret_plates_taken",
        "normalized_solo_kills",
        "normalized_deaths",
    ]

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
except FileNotFoundError:
    raise RuntimeError(f"File not found: {heatmap_file_path}. Ensure the file exists.")
except pd.errors.ParserError as e:
    raise RuntimeError(f"Error parsing CSV file {heatmap_file_path}: {e}")


# -------------------------------------------------------------------------------- #
# Supporting Functions                                                             #
# -------------------------------------------------------------------------------- #

def calculate_overall_win_rate(champion: str) -> float:
    """
    Calculate the overall win rate for a champion.
    Args:
        champion (str): Champion name.
    Returns:
        float: Win rate as a percentage, rounded to 2 decimals.
    """
    champion_df = df[df['champion'] == champion]
    if champion_df.empty:
        return 0.0
    return (champion_df['win'].mean() * 100).round(2)


def validate_numeric_input(value: str, default: int = 10) -> int:
    """
    Validate and convert a numeric string input to an integer.
    Args:
        value (str): Input value.
        default (int): Default value if validation fails.
    Returns:
        int: Validated numeric value.
    """
    return int(value) if value.isdigit() else default


def update_enemy_champion_options(attr, old, new):
    """
    Update the enemy champion options based on the selected enemy role and refresh the plot.
    """
    selected_role = enemy_role_select.value
    if selected_role == "ANY":
        # Combine all enemy columns to get unique enemies
        unique_enemies = pd.concat([
            df['enemy_1'], df['enemy_2'], df['enemy_3'], df['enemy_4'], df['enemy_5']
        ]).unique()
    else:
        role_column_map = {
            "TOP": "enemy_1",
            "JUNGLE": "enemy_2",
            "MID": "enemy_3",
            "ADC": "enemy_4",
            "SUPPORT": "enemy_5"
        }
        column = role_column_map.get(selected_role, None)
        unique_enemies = df[column].unique() if column else []

    # Update dropdown options and reset selection
    enemy_champion_select.options = sorted(unique_enemies.tolist())
    enemy_champion_select.value = ""
    update_winrate_plot_with_filters(attr, old, new)

# -------------------------------------------------------------------------------- #
# Shared Global Widgets                                                           #
# -------------------------------------------------------------------------------- #

# Main widgets for user input
champion_select = Select(title="Select Your Champion:", value=champions[0], options=champions)
role_select = Select(title="Select Your Role:", value=roles[0], options=roles)

# Div to display the overall win rate dynamically
overall_avg_win_rate = calculate_overall_win_rate(champion_select.value)
overall_winrate_div = Div(text=f"Overall Win Rate: {overall_avg_win_rate:.2f}%", width=200)

# Enemy-specific widgets
enemy_roles = ["ANY", "TOP", "JUNGLE", "MID", "ADC", "SUPPORT"]
enemy_role_select = Select(title="Enemy Role:", value="ANY", options=enemy_roles)
enemy_champion_select = Select(title="Compare Against Specific Enemy:", value="", options=[])
min_games_input = TextInput(title="Minimum Games Threshold:", value="50")

# Ally-specific widgets
ally_role_select = Select(title="Select Ally Role:", value="JUNGLE", options=roles)
ally_min_games_input = TextInput(title="Minimum Games Threshold for Allies:", value="50")
selected_allies = []  # Track selected allies dynamically
selected_allies_display = column()  # Dynamic ally display

# Sort Selector Widget for Heatmap
sort_select = Select(
    title="Sort By Metric:",
    value="Winrate",
    options=metric_labels
)

# -------------------------------------------------------------------------------- #
# Creation of the Win Rate Against Enemies Plot                                    #
# -------------------------------------------------------------------------------- #

# Initialize empty data source for the plot
winrate_source = ColumnDataSource(data=dict(enemy_champion=[], win_rate_percent=[], n_games=[], color=[], hatch=[]))

def create_winrate_plot():
    """
    Create the Win Rate plot against enemies.
    Returns:
        tuple: Bokeh figure and average win rate line.
    """
    p = figure(x_range=[], height=400, title="Win Rate Against Enemies", toolbar_location=None, tools="")

    p.vbar(
        x='enemy_champion',
        top='win_rate_percent',
        width=0.5,
        source=winrate_source,
        line_color="white",
        fill_color='color',
        hatch_pattern='hatch',
        hatch_color="white",
        hatch_alpha=0.5,
        hatch_weight=2
    )

    hover = HoverTool(tooltips=[("Win Rate", "@win_rate_percent%"), ("Games Played", "@n_games")])
    p.add_tools(hover)

    p.y_range.start = 0
    p.y_range.end = 100
    p.yaxis.axis_label = "Win Rate (%)"
    p.xaxis.major_label_orientation = 0.785

    avg_win_rate_line = Span(location=0, dimension='width', line_color='black', line_dash='dashed', line_width=2)
    p.add_layout(avg_win_rate_line)

    return p, avg_win_rate_line


def update_winrate_plot_with_filters(attr, old, new):
    """
    Update the Win Rate plot based on filters.
    """
    global overall_avg_win_rate

    # Calculate overall win rate for the selected champion
    overall_avg_win_rate = calculate_overall_win_rate(champion_select.value)

    # Update the overall win rate display
    overall_winrate_div.text = f"Overall Win Rate: {overall_avg_win_rate:.2f}%"

    # Validate the minimum games input
    min_games = validate_numeric_input(min_games_input.value, default=10)

    selected_role = enemy_role_select.value
    selected_enemy = enemy_champion_select.value if enemy_champion_select.value else None

    # Filter data for the selected champion and role
    filtered_df = df[(df['champion'] == champion_select.value) & (df['team_position'] == role_select.value)]

    # Handle filtering by enemy role
    if selected_role == "ANY":
        filtered_df = pd.concat([
            filtered_df[['win', 'enemy_1']].rename(columns={'enemy_1': 'enemy_champion'}),
            filtered_df[['win', 'enemy_2']].rename(columns={'enemy_2': 'enemy_champion'}),
            filtered_df[['win', 'enemy_3']].rename(columns={'enemy_3': 'enemy_champion'}),
            filtered_df[['win', 'enemy_4']].rename(columns={'enemy_4': 'enemy_champion'}),
            filtered_df[['win', 'enemy_5']].rename(columns={'enemy_5': 'enemy_champion'})
        ])
    else:
        role_column_map = {
            "TOP": "enemy_1",
            "JUNGLE": "enemy_2",
            "MID": "enemy_3",
            "ADC": "enemy_4",
            "SUPPORT": "enemy_5"
        }
        column = role_column_map.get(selected_role)
        if column:
            filtered_df = filtered_df.rename(columns={column: "enemy_champion"})

    # Aggregate win rate data
    win_rates = (
        filtered_df.groupby('enemy_champion')['win']
        .agg(['mean', 'size'])
        .reset_index()
        .rename(columns={'mean': 'win_rate', 'size': 'n_games'})
    )
    win_rates['win_rate_percent'] = (win_rates['win_rate'] * 100).round(2)
    win_rates = win_rates[win_rates['n_games'] >= min_games]

    # Sort and assign colors/hatches
    win_rates_sorted = win_rates.sort_values(by="win_rate", ascending=False)
    top_5 = win_rates_sorted.head(5).copy()
    bottom_5 = win_rates_sorted.tail(5).copy()

    top_5['color'] = '#2b93b6'  # Blue for top matchups
    bottom_5['color'] = '#e54635'  # Red for bottom matchups
    top_5['hatch'] = ''
    bottom_5['hatch'] = ''

    # Handle specific enemy selection
    if selected_enemy and selected_enemy in win_rates['enemy_champion'].values:
        selected_enemy_row = win_rates[win_rates['enemy_champion'] == selected_enemy].copy()
        selected_enemy_row['color'] = (
            '#2b93b6' if selected_enemy_row['win_rate_percent'].iloc[0] > overall_avg_win_rate else '#e54635'
        )
        selected_enemy_row['hatch'] = '/'
        combined = pd.concat([top_5, bottom_5, selected_enemy_row]).drop_duplicates(subset=['enemy_champion'])
    else:
        combined = pd.concat([top_5, bottom_5])

    # Update plot data
    combined = combined.sort_values(by="win_rate", ascending=False)
    winrate_source.data = combined.to_dict(orient='list')
    winrate_plot.x_range.factors = list(combined['enemy_champion'])
    winrate_plot.title.text = f"Win Rate Against Enemies as {champion_select.value} ({role_select.value})"

    avg_win_rate_line.location = overall_avg_win_rate


# Initialize the plot
winrate_plot, avg_win_rate_line = create_winrate_plot()

# -------------------------------------------------------------------------------- #
# Ally Synergies Plot                                                              #
# -------------------------------------------------------------------------------- #

# Initialize empty data source for the ally synergies plot
ally_synergy_source = ColumnDataSource(data=dict(ally_champion=[], win_rate_percent=[], n_games=[], color=[]))

def calculate_ally_synergies(champion: str, role: str, selected_allies: list, ally_role: str) -> pd.DataFrame:
    """
    Calculate ally synergies based on the selected champion, role, and allies.
    Args:
        champion (str): Selected champion.
        role (str): User's role.
        selected_allies (list): List of selected allies.
        ally_role (str): Selected ally role.
    Returns:
        pd.DataFrame: DataFrame containing ally synergy statistics.
    """
    if not selected_allies:
        return pd.DataFrame(columns=['ally_champion', 'win_rate', 'n_games', 'win_rate_percent', 'texture'])

    filtered_df = df[(df['champion'] == champion) & (df['team_position'] == role)]

    # Map ally roles to columns
    role_column_map = {
        "TOP": "ally_1",
        "JUNGLE": "ally_2",
        "MID": "ally_3",
        "ADC": "ally_4",
        "SUP": "ally_5",
    }
    ally_column = role_column_map.get(ally_role)

    if not ally_column:
        return pd.DataFrame()

    # Filter data by allies and ally role
    combined_df = filtered_df[['win', ally_column]].rename(columns={ally_column: 'ally_champion'})
    combined_df = combined_df[combined_df['ally_champion'].isin(selected_allies)]

    # Aggregate win rates and game counts
    win_rates = (
        combined_df.groupby('ally_champion')['win']
        .agg(['mean', 'size'])
        .reset_index()
        .rename(columns={'mean': 'win_rate', 'size': 'n_games'})
    )
    win_rates['win_rate_percent'] = (win_rates['win_rate'] * 100).round(2)
    win_rates['texture'] = ''  # Default no texture

    # Filter by minimum games threshold
    min_games = validate_numeric_input(ally_min_games_input.value, default=10)
    win_rates = win_rates[win_rates['n_games'] >= min_games]

    # Filter out allies with win rates less than the overall win rate
    overall_winrate = calculate_overall_win_rate(champion)
    win_rates = win_rates[win_rates['win_rate_percent'] > overall_winrate]

    return win_rates


def update_ally_synergy_plot(attr, old, new):
    """
    Update the ally synergy plot based on selected allies and roles.
    """
    global selected_allies
    # Fallback if no role is selected
    ally_role = ally_role_select.value
    if not ally_role or ally_role not in roles:
        ally_synergy_source.data = dict(ally_champion=[], win_rate_percent=[], n_games=[], color=[])
        ally_synergy_plot.x_range.factors = []
        ally_synergy_plot.title.text = "No role selected for ally synergies."
        return

    ally_data = calculate_ally_synergies(
    champion=champion_select.value,
    role=role_select.value,
    selected_allies=selected_allies,
    ally_role=ally_role
    )

    # Calculate overall win rate
    overall_winrate = calculate_overall_win_rate(champion_select.value)

    # Update the overall win rate line location
    overall_winrate = calculate_overall_win_rate(champion_select.value)
    overall_winrate_line.location = overall_winrate

    # Filter allies based on win rates above the overall win rate
    ally_data = ally_data[ally_data['win_rate_percent'] > overall_winrate]

    # Ensure selected allies are always displayed
    for ally in selected_allies:
        if ally not in ally_data['ally_champion'].values:
            ally_data = pd.concat([ally_data, pd.DataFrame({
                'ally_champion': [ally],
                'win_rate_percent': [0],  # Default win rate if no data available
                'n_games': [0],
                'color': ['#e54635']
            })], ignore_index=True)

    # Sort allies by win rate in descending order
    ally_data = ally_data.sort_values(by='win_rate_percent', ascending=False)

    # Assign colors based on win rate
    ally_data['color'] = ally_data['win_rate_percent'].apply(
        lambda x: '#2b93b6' if x >= overall_winrate else '#e54635'
    )

    # Update the plot with sorted data
    ally_synergy_source.data = ally_data.to_dict(orient='list')
    ally_synergy_plot.x_range.factors = list(ally_data['ally_champion'])
    ally_synergy_plot.title.text = f"Ally Synergies for {champion_select.value} ({role_select.value}) with Selected Allies"

def update_ally_synergy_plot_on_role(attr, old, new):
    """
    Update the ally synergy plot based on the selected ally role.
    """
    ally_role = ally_role_select.value
    user_role = role_select.value

    # Prevent same role selection
    if ally_role == user_role:
        ally_synergy_source.data = dict(ally_champion=[], win_rate_percent=[], n_games=[], color=[])
        ally_synergy_plot.x_range.factors = []
        ally_synergy_plot.title.text = f"No synergies available for same role ({ally_role})."
        return

    # Get all allies for the selected role
    role_column_map = {
        "TOP": "ally_1",
        "JUNGLE": "ally_2",
        "MID": "ally_3",
        "ADC": "ally_4",
        "SUP": "ally_5",
    }
    ally_column = role_column_map.get(ally_role)

    if not ally_column:
        ally_synergy_source.data = dict(ally_champion=[], win_rate_percent=[], n_games=[], color=[])
        ally_synergy_plot.x_range.factors = []
        ally_synergy_plot.title.text = "Invalid role selected."
        return

    allies_in_role = df[ally_column].dropna().unique().tolist()
    ally_data = calculate_ally_synergies(
        champion=champion_select.value,
        role=user_role,
        selected_allies=allies_in_role,
        ally_role=ally_role
    )

    overall_winrate = calculate_overall_win_rate(champion_select.value)

    # Update the overall win rate line location
    overall_winrate_line.location = overall_winrate

    # Filter allies based on win rates above the overall win rate
    ally_data = ally_data[ally_data['win_rate_percent'] > overall_winrate]

    # Sort allies by win rate in descending order
    ally_data = ally_data.sort_values(by='win_rate_percent', ascending=False)

    ally_data['color'] = ally_data['win_rate_percent'].apply(
        lambda x: '#2b93b6' if x >= overall_winrate else '#e54635'
    )

    # Update the plot with sorted data
    ally_synergy_source.data = ally_data.to_dict(orient='list')
    ally_synergy_plot.x_range.factors = list(ally_data['ally_champion'])
    ally_synergy_plot.title.text = f"Ally Synergies for {champion_select.value} ({role_select.value}) with {ally_role} Allies"

def create_ally_synergy_plot():
    """
    Create the Ally Synergy plot.
    Returns:
        tuple: Bokeh figure and overall win rate line.
    """
    p = figure(x_range=[], height=400, title="Ally Synergies", toolbar_location=None, tools="")

    p.vbar(
        x='ally_champion',
        top='win_rate_percent',
        width=0.5,
        source=ally_synergy_source,
        line_color="white",
        fill_color='color',
        hatch_pattern='texture',  # Add hatch pattern from texture column
        hatch_color="white",
        hatch_alpha=0.5,
        hatch_weight=2
    )

    hover = HoverTool(tooltips=[("Win Rate", "@win_rate_percent%"), ("Games Played", "@n_games")])
    p.add_tools(hover)

    p.y_range.start = 0
    p.y_range.end = 100
    p.yaxis.axis_label = "Win Rate (%)"
    p.xaxis.major_label_orientation = 0.785

    overall_winrate_line = Span(
        location=0,
        dimension='width',
        line_color='black',
        line_dash='dashed',
        line_width=2
    )
    p.add_layout(overall_winrate_line)

    return p, overall_winrate_line


# Initialize the ally synergies plot
ally_synergy_plot, overall_winrate_line = create_ally_synergy_plot()


# -------------------------------------------------------------------------------- #
# Heatmap Plot                                                                     #
# -------------------------------------------------------------------------------- #

# Prepare Heatmap Data
default_champion = heatmap_data['champion'].unique()[0]
filtered_data = heatmap_data[heatmap_data['champion'] == default_champion]

# Create the initial ColumnDataSource for the heatmap
source = ColumnDataSource(data={
    "lane_opponent": [],
    "metric": [],
    "value": [],
    "raw_value": [],
    "n_games": [],
})

# Create Heatmap Figure
heatmap_plot = figure(
    title=f"Performance Metrics Against Opponents ({default_champion})",
    x_range=metric_labels,
    y_range=list(filtered_data['lane_opponent'].unique()),
    x_axis_label="Metrics",
    y_axis_label="Opponents",
    toolbar_location=None,
    tools=""
)

# Add rectangles to the heatmap
heatmap_plot.rect(
    x="metric",
    y="lane_opponent",
    width=1,
    height=1,
    source=source,
    fill_color={"field": "value", "transform": color_mappers["winrate"]},
    line_color=None
)

# Add a color bar
color_bar = ColorBar(
    color_mapper=color_mappers["winrate"],
    label_standoff=12,
    location=(0, 0),
    orientation="vertical"
)
heatmap_plot.add_layout(color_bar, "right")

# Add HoverTool
hover = HoverTool(
    tooltips=[
        ("Metric", "@metric"),
        ("Opponent", "@lane_opponent"),
        ("Normalized Value", "@value{0.2f}"),
        ("Mean Value", "@raw_value{0.2f}"),
        ("Number of Games", "@n_games"),
    ]
)
heatmap_plot.add_tools(hover)

# Update Function for Heatmap
def update_heatmap(attr, old, new):
    selected_champion = champion_select.value
    selected_sort_metric = metric_map[sort_select.value]
    min_games = int(min_games_input.value) if min_games_input.value.isdigit() else 50

    # Filter data for the selected champion and minimum games
    updated_data = heatmap_data[
        (heatmap_data['champion'] == selected_champion) & 
        (heatmap_data['n_games'] >= min_games)
    ]

    # Sort the data by the selected metric
    updated_data = updated_data.sort_values(by=selected_sort_metric, ascending=False)

    # Prepare new data for the heatmap
    new_source_data = {
        "lane_opponent": [],
        "metric": [],
        "value": [],
        "raw_value": [],
        "n_games": [],
    }

    for metric, label in zip(metrics, metric_labels):
        raw_metric = raw_metric_map[label]
        if metric == "winrate":
            for _, row in updated_data.iterrows():
                new_source_data["lane_opponent"].append(row["lane_opponent"])
                new_source_data["metric"].append(label)
                new_source_data["value"].append(row["winrate"])
                new_source_data["raw_value"].append(row["winrate"])
                new_source_data["n_games"].append(row["n_games"])
        else:
            metric_min = updated_data[metric].min()
            metric_max = updated_data[metric].max()

            # Avoid divide-by-zero errors
            if metric_max > metric_min:
                updated_data[metric] = (
                    (updated_data[metric] - metric_min) / (metric_max - metric_min)
                )
            else:
                updated_data[metric] = 0.5

            for _, row in updated_data.iterrows():
                new_source_data["lane_opponent"].append(row["lane_opponent"])
                new_source_data["metric"].append(label)
                new_source_data["value"].append(row[metric])
                new_source_data["raw_value"].append(row[raw_metric])
                new_source_data["n_games"].append(row["n_games"])

    source.data = new_source_data
    heatmap_plot.y_range.factors = list(updated_data['lane_opponent'].unique())
    heatmap_plot.title.text = f"Performance Metrics Against Opponents ({selected_champion})"
    color_bar.color_mapper = color_mappers[selected_sort_metric]

# Initial Update for Heatmap
update_heatmap(None, None, None)


# -------------------------------------------------------------------------------- #
# Population Pyramid                                                               #
# -------------------------------------------------------------------------------- #

def create_population_pyramid():
    """
    Create the Population Pyramid for item frequency and win rate.
    Returns:
        bokeh.plotting.figure: Configured Population Pyramid figure.
    """
    # Colors for the bars
    selected_blue_color = "#2B93B6"
    non_selected_gray_color = "#7F7F7F"

    # Extract settings
    champion_name = champion_select.value
    role = role_select.value
    sort_by = sort_criterion_select.value

    # Filter data for the pyramid
    pyramid_data = item_data_filtered[
        (item_data_filtered['champion'] == champion_name) &
        (item_data_filtered['role'] == role)
    ]

    if pyramid_data.empty:
        # Return an empty plot if no data is available
        p = figure(title="Population Pyramid: No Data Available", height=400, width=800)
        return p

    # Prepare data for the pyramid
    freq = pyramid_data[['item_name', 'frequency_percentage']]
    winrate = pyramid_data[['item_name', 'win_rate']]

    merged_data = pd.merge(freq, winrate, on='item_name', suffixes=('_freq', '_winrate'))

    # Sort by the selected criterion
    if sort_by == "Frequency":
        merged_data.sort_values('frequency_percentage', ascending=False, inplace=True)
    elif sort_by == "Winrate":
        merged_data.sort_values('win_rate', ascending=False, inplace=True)

    sorted_items = merged_data['item_name'][::-1]

    # Assign bar colors
    frequency_colors = [selected_blue_color if sort_by == "Frequency" else non_selected_gray_color] * len(merged_data)
    winrate_colors = [selected_blue_color if sort_by == "Winrate" else non_selected_gray_color] * len(merged_data)

    # Create the figure
    p = figure(
        title=f"Population Pyramid for {champion_name}: {sort_by} %",
        height=400,
        width=800,
        x_range=(-100, 100),
        y_range=list(sorted_items),
        y_axis_label="Items",
    )

    # Add bars for frequency and win rate
    bin_width = 0.8
    p.hbar(
        y=merged_data['item_name'],
        right=merged_data['frequency_percentage'],
        height=bin_width,
        color=frequency_colors,
        legend_label="Frequency %",
    )
    p.hbar(
        y=merged_data['item_name'],
        right=-merged_data['win_rate'],  # Negative for the left side
        height=bin_width,
        color=winrate_colors,
        legend_label="Win Rate %",
    )

    # Customize axes
    p.xaxis.ticker = list(range(-100, 101, 10))
    p.xaxis.formatter = CustomJSTickFormatter(code="return Math.abs(tick);")
    p.xaxis.axis_label = "Percentage"
    p.yaxis.axis_label_text_font_size = "14pt"

    # Hide the legend
    p.legend.visible = False

    return p


def update_population_pyramid(attr, old, new):
    """
    Dynamically update the Population Pyramid plot in the layout.
    """
    # Create a new Population Pyramid figure
    new_pyramid_plot = create_population_pyramid()
    
    # Update the layout's children to replace the old pyramid plot
    advanced_analysis_section.children[0].children[1] = new_pyramid_plot



# Initialize sort criterion selector and attach callbacks
sort_criterion_select = Select(title="Sort Population Pyramid By:", value="Frequency", options=["Frequency", "Winrate"])
sort_criterion_select.on_change("value", update_population_pyramid)

# -------------------------------------------------------------------------------- #
# Layout Assembly and Final Setup                                                  #
# -------------------------------------------------------------------------------- #

# Spacer for visual alignment
spacer = Spacer(width=300, height=100)

# Layout for the Win Rate plot with widgets
winrate_section = column(
    row(champion_select, role_select, overall_winrate_div),  # Add the div here
    row(enemy_role_select, min_games_input, enemy_champion_select),
    winrate_plot
)

# Layout for the Ally Synergies plot with widgets
ally_synergy_section = column(
    row(ally_role_select, ally_min_games_input),  # Ally Role and Min Games widgets
    ally_synergy_plot  # Synergies plot
)

# Buttons to dynamically display and remove selected allies
def update_selected_allies_display():
    """
    Dynamically update the display of selected allies.
    """
    buttons = []
    for ally in selected_allies:
        button = Button(label=f"Remove {ally}", button_type="danger", width=150)
        button.on_click(lambda ally=ally: remove_ally_from_selection(ally))
        buttons.append(button)
    selected_allies_display.children = buttons


def remove_ally_from_selection(ally):
    """
    Remove an ally from the selected list and update the ally synergies plot.
    """
    global selected_allies
    if ally in selected_allies:
        selected_allies.remove(ally)
        update_ally_dropdown_options()  # Refresh available allies in dropdown
        update_ally_synergy_plot(None, None, None)  # Refresh the plot
        update_selected_allies_display()  # Update ally display


def update_ally_dropdown_options():
    """
    Update the Ally dropdown options to exclude already-selected allies.
    """
    ally_role = ally_role_select.value
    role_column_map = {
        "TOP": "ally_1",
        "JUNGLE": "ally_2",
        "MID": "ally_3",
        "ADC": "ally_4",
        "SUP": "ally_5",
    }
    ally_column = role_column_map.get(ally_role)

    # Get allies in the selected role
    allies_in_role = df[ally_column].dropna().unique()

    # Exclude already-selected allies
    remaining_allies = [ally for ally in allies_in_role if ally not in selected_allies]

# Initial update of selected allies display
update_selected_allies_display()

# Create the Population Pyramid
pyramid_plot = create_population_pyramid()

# Define the advanced analysis section
advanced_analysis_section = row(
    column(sort_criterion_select, pyramid_plot),  # Population Pyramid
    column(sort_select, heatmap_plot)  # Heatmap and its sorting widget
)


# Combine all sections into the final layout
layout = column(
    row(winrate_section, ally_synergy_section),
    advanced_analysis_section
)

# -------------------------------------------------------------------------------- #
# Attach Callbacks                                                                 #
# -------------------------------------------------------------------------------- #

# Global callbacks for Champion and Role selections
champion_select.on_change("value", update_winrate_plot_with_filters)
champion_select.on_change("value", update_ally_synergy_plot_on_role)
champion_select.on_change("value", update_population_pyramid)
champion_select.on_change("value", update_heatmap)

role_select.on_change("value", update_winrate_plot_with_filters)
role_select.on_change("value", update_ally_synergy_plot_on_role)
role_select.on_change("value", update_population_pyramid)
role_select.on_change("value", update_heatmap)

# Enemy-specific callbacks
min_games_input.on_change("value", update_winrate_plot_with_filters)
enemy_role_select.on_change("value", update_enemy_champion_options)
enemy_champion_select.on_change("value", update_winrate_plot_with_filters)

# Ally-specific callbacks
ally_role_select.on_change("value", update_ally_synergy_plot_on_role)
ally_min_games_input.on_change("value", update_ally_synergy_plot)

# Attach sort criterion callback for the Population Pyramid
sort_criterion_select.on_change("value", update_population_pyramid)


# -------------------------------------------------------------------------------- #
# Final Application Setup                                                          #
# -------------------------------------------------------------------------------- #

# Perform initial updates to ensure the application is initialized
update_enemy_champion_options(None, None, None)
update_winrate_plot_with_filters(None, None, None)
update_ally_synergy_plot_on_role(None, None, None)
update_ally_dropdown_options()

# Add the layout to the document
curdoc().clear()  # Clear any existing layout
curdoc().add_root(layout)
