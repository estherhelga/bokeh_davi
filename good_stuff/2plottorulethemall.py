import pandas as pd
from bokeh.layouts import column, row, grid
from bokeh.models import Select, TextInput, MultiSelect, ColumnDataSource, HoverTool, Span, Spacer, Button, Div, LinearColorMapper, ColorBar, Tooltip, Legend, LegendItem
from bokeh.plotting import figure, curdoc, show
from bokeh.models import CustomJSTickFormatter, Label
from bokeh.palettes import linear_palette
from bokeh.palettes import Blues256
import numpy as np
from sklearn.neighbors import KernelDensity
from bokeh.palettes import RdYlGn11, Viridis256, RdYlBu11, RdYlBu
from bokeh.models.dom import HTML
from bokeh.models.glyphs import Rect, Line
import requests
import plotly.express as px
from bokeh.models import TapTool

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


color_palette = ["#0d4254", "#10485c", "#134f64", "#16566d", "#195c74", "#1b627c", "#1d6983", "#1f6f8b", "#217593", "#227b9a", "#2481a2", "#2687a8", "#288caf", "#2d92b4", "#4097b3", "#509bb2", "#5b9fb1", "#68a3b1", "#71a8b1", "#7bacb1", "#83b0b2", "#8bb4b3", "#92b8b4", "#98bdb5", "#9fc1b6", "#a5c5b7", "#aac9b8", "#b0cdb8", "#b6d1b8", "#bad5b8", "#c0d8b8", "#c4dcb7", "#cadfb6", "#cfe3b6", "#d4e6b4", "#d8e9b3", "#ddebb2", "#e2eeb0", "#e5f1af", "#eaf3ae", "#edf5ad", "#f0f7ac", "#f3f8ab", "#f6faaa", "#f8fba9", "#f9fca9", "#fbfca9", "#fcfda8", "#fdfea8", "#ffffa8", "#fefda7", "#fefca6", "#fefba5", "#fefaa5", "#fef9a4", "#fef7a3", "#fef5a1", "#fef29f", "#fef09e", "#fdec9b", "#fde999", "#fde696", "#fde294", "#fcdd90", "#fcd98e", "#fcd58a", "#fbd087", "#fbcb83", "#fac680", "#f9c07c", "#f9bb78", "#f8b575", "#f7af71", "#f7a86c", "#f6a269", "#f49b64", "#f39460", "#f28d5b", "#f18657", "#ef7e52", "#ee764d", "#ec6d48", "#ea6543", "#e85b3e", "#e65139", "#e44634", "#dc4231", "#d53e2f", "#cc3c2d", "#c3392a", "#ba3729", "#b23426", "#a93125", "#a02e22", "#972b1f", "#8e271d", "#84241a", "#7b2017", "#721d14"]

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
        "normalized_winrate",  # Add winrate as the first metric
        "normalized_lane_minions_first_10_minutes",
        "normalized_max_cs_advantage_on_lane_opponent",
        "normalized_max_level_lead_lane_opponent",
        "normalized_turret_plates_taken",
        "normalized_solo_kills",
        "normalized_deaths",
    ]

    # Define color mappers for each metric
    color_mappers = {
        "normalized_winrate": LinearColorMapper(palette=color_palette[::-1], low=0, high=1),
        "normalized_lane_minions_first_10_minutes": LinearColorMapper(palette=color_palette[::-1], low=0, high=1),
        "normalized_max_cs_advantage_on_lane_opponent": LinearColorMapper(palette=color_palette[::-1], low=0, high=1),
        "normalized_max_level_lead_lane_opponent": LinearColorMapper(palette=color_palette[::-1], low=0, high=1),
        "normalized_turret_plates_taken": LinearColorMapper(palette=color_palette[::-1], low=0, high=1),
        "normalized_solo_kills": LinearColorMapper(palette=color_palette[::-1], low=0, high=1),
        "normalized_deaths": LinearColorMapper(palette=color_palette[::-1], low=0, high=1),  # Non-reversed colormap for Deaths
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
        "Win Rate",  # Label for winrate
        "CS First 10min",
        "Max. \nCS Advantage",
        "Max. \nLevel Lead",
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
    Update the enemy champion options based on the selected enemy role,
    champion, role, and minimum games threshold.
    """
    selected_role = enemy_role_select.value
    selected_champion = champion_select.value
    selected_user_role = role_select.value
    min_games = validate_numeric_input(min_games_input.value, default=50)

    # Filter data for the selected champion and role
    filtered_df = df[(df['champion'] == selected_champion) & (df['team_position'] == selected_user_role)]

    if selected_role == "ANY":
        # Combine all enemy columns to get unique enemies
        combined_df = pd.concat([
            filtered_df[['win', 'enemy_1']].rename(columns={'enemy_1': 'enemy_champion'}),
            filtered_df[['win', 'enemy_2']].rename(columns={'enemy_2': 'enemy_champion'}),
            filtered_df[['win', 'enemy_3']].rename(columns={'enemy_3': 'enemy_champion'}),
            filtered_df[['win', 'enemy_4']].rename(columns={'enemy_4': 'enemy_champion'}),
            filtered_df[['win', 'enemy_5']].rename(columns={'enemy_5': 'enemy_champion'})
        ])
    else:
        # Map the role to the appropriate column and filter
        role_column_map = {
            "TOP": "enemy_1",
            "JUNGLE": "enemy_2",
            "MID": "enemy_3",
            "ADC": "enemy_4",
            "SUPPORT": "enemy_5"
        }
        column = role_column_map.get(selected_role)
        if column:
            combined_df = filtered_df.rename(columns={column: "enemy_champion"})
        else:
            combined_df = pd.DataFrame(columns=['win', 'enemy_champion'])

    # Aggregate win rate and games played
    aggregated_data = (
        combined_df.groupby('enemy_champion')['win']
        .agg(['size'])
        .reset_index()
        .rename(columns={'size': 'n_games'})
    )

    # Filter by the minimum games threshold
    valid_enemies = aggregated_data[aggregated_data['n_games'] >= min_games]['enemy_champion']

    # Update dropdown options
    enemy_champion_select.options = sorted(valid_enemies.tolist())
    enemy_champion_select.value = ""  # Reset selection


# Placeholder for champion stats with image
overall_avg_win_rate = calculate_overall_win_rate(champions[0])  # First champion's stats
total_games = df[df['champion'] == champions[0]].shape[0]
champion_stats = Div(
    text=f"""
    <div style="
        display: flex; 
        align-items: center; 
        color: black; 
        font-family: Arial, sans-serif; 
        background-color: #f9f9f9; 
        border: 1px solid black; 
        border-radius: 5px; 
        padding: 10px;
    ">
        <img src='http://ddragon.leagueoflegends.com/cdn/14.20.1/img/champion/{champions[0]}.png' 
             style="width:50px; height:50px; margin-right:10px; border-radius:5px;">
        <div>
            <span style="font-size:20px; font-weight:bold;">{overall_avg_win_rate:.1f}%</span> 
            Average Win Rate for 
            <span style="font-size:20px; font-weight:bold;">{champions[0]}</span> 
            High Rank OTPs | 
            <span style="font-size:20px; font-weight:bold;">{total_games}</span> games
        </div>
    </div>
    """,
    width=700, height=60
)

def update_champion_image_and_stats(attr, old, new):
    """
    Update the champion stats (including the icon) when the selected champion changes.
    """
    selected_champion = champion_select.value

    # Calculate stats
    overall_winrate = calculate_overall_win_rate(selected_champion)
    total_games = df[df['champion'] == selected_champion].shape[0]

    # Update the stats display with image and formatted text
    champion_stats.text = (
        f"""
        <div style="
            display: flex; 
            align-items: center; 
            color: black; 
            font-family: Arial, sans-serif; 
            background-color: #f9f9f9; 
            border: 1px solid black; 
            border-radius: 5px; 
            padding: 5px;
        ">
            <img src='http://ddragon.leagueoflegends.com/cdn/14.20.1/img/champion/{selected_champion}.png' 
                 style="width:50px; height:50px; margin-right:10px; border-radius:5px;">
            <div>
                <span style="font-size:15px; font-weight:bold;">{overall_winrate:.1f}%</span> 
                Average Win Rate for 
                <span style="font-size:15px; font-weight:bold;">{selected_champion}</span> 
                High Rank OTPs | 
                <span style="font-size:15px; font-weight:bold;">{total_games}</span> games
            </div>
        </div>
        """
    )


# -------------------------------------------------------------------------------- #
# Shared Global Widgets                                                           #
# -------------------------------------------------------------------------------- #

# Main widgets for user input
champion_select = Select(title="Your Champion:", value=champions[0], options=champions, width=100)
role_select = Select(title="Your Role:", value=roles[0], options=roles, width=100)

# Div to display the overall win rate dynamically
overall_avg_win_rate = calculate_overall_win_rate(champion_select.value)
overall_winrate_div = Div(text=f"Overall Win Rate: {overall_avg_win_rate:.2f}%", width=200)

# Enemy-specific widgets
enemy_roles = ["ANY", "TOP", "JUNGLE", "MID", "ADC", "SUPPORT"]
enemy_role_select = Select(title="Enemy Role:", value="TOP", options=enemy_roles, width=100)
enemy_champion_select = Select(title="Specific Enemy:", value="", options=[], width=100)
min_games_input = TextInput(title="Minimum Games:", value="50", width=100)

# Ally-specific widgets
ally_role_select = Select(title="Ally Role:", value="JUNGLE", options=roles, width=100)
ally_min_games_input = TextInput(title="Minimum Games:", value="50", width=100)

# Population Pyramid
sort_criterion_select = Select(title="Sort By:", value="Frequency", options=["Frequency", "Win Rate"], width=100)

# Sort Selector Widget for Heatmap
sort_select = Select(title="Sort By:", value="Win Rate", options=metric_labels, width=100)

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
    # Create the figure
    p = figure(x_range=[], height=370, width=1050, title="Win Rate Against Enemies", toolbar_location=None, tools="")

    # Add the bars to the plot
    bars = p.vbar(
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

    # Add the average win rate line
    avg_win_rate_line = Span(location=0, dimension='width', line_color='black', line_dash='dashed', line_width=2)
    p.add_layout(avg_win_rate_line)

    # Configure axes and appearance
    p.y_range.start = 0
    p.y_range.end = 100
    p.yaxis.axis_label = "Win Rate (%)"
    p.xaxis.major_label_orientation = 0.785

    # Add a hover tool for the bars
    hover = HoverTool(tooltips=[("Win Rate", "@win_rate_percent%"), ("Games Played", "@n_games"), ("Enemy", "@enemy_champion")])
    p.add_tools(hover)

    # Add invisible glyphs for legend entries
    above_avg_glyph = p.vbar(x=[0], top=[1], fill_color='#2b93b6', line_color='white', width=0.1, visible=False)
    below_avg_glyph = p.vbar(x=[0], top=[1], fill_color='#e54635', line_color='white', width=0.1, visible=False)
    comparison_glyph = p.vbar(x=[0], top=[1], fill_color='#d3d3d3', line_color='white', hatch_pattern='/', hatch_color="white", width=0.1, visible=False)
    avg_line_glyph = p.line(x=[0, 1], y=[0, 1], line_color="black", line_dash="dashed", line_width=2, visible=False)

    # Add legend
    legend_items = [
        LegendItem(label="Above Avg. Win Rate", renderers=[above_avg_glyph]),
        LegendItem(label="Below Avg. Win Rate", renderers=[below_avg_glyph]),
        LegendItem(label="Specific Enemy", renderers=[comparison_glyph]),
        LegendItem(label="Average Win Rate", renderers=[avg_line_glyph])
    ]
    legend = Legend(items=legend_items, location="top_right", label_text_font_size="10pt")
    legend.background_fill_alpha = 0  # Make the legend background transparent
    legend.border_line_alpha = 0  # Remove the legend border
    p.add_layout(legend)

    return p, avg_win_rate_line


def update_winrate_plot_with_filters(attr, old, new):
    """
    Update the Win Rate plot based on filters.
    Always highlight the selected enemy, whether it is already in the graph or not.
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

    # Add image URLs
    win_rates['image_url'] = win_rates['enemy_champion'].apply(
        lambda x: f"http://ddragon.leagueoflegends.com/cdn/14.20.1/img/champion/{x}.png"
    )

    # Sort and assign colors/hatches
    win_rates_sorted = win_rates.sort_values(by="win_rate", ascending=False)
    top_5 = win_rates_sorted.head(5).copy()
    bottom_5 = win_rates_sorted.tail(5).copy()

    top_5['color'] = '#2b93b6'  # Blue for top matchups
    bottom_5['color'] = '#e54635'  # Red for bottom matchups
    top_5['hatch'] = ''
    bottom_5['hatch'] = ''

    # Combine top and bottom 5 into a single dataset
    combined = pd.concat([top_5, bottom_5]).drop_duplicates(subset=['enemy_champion'])

    # Handle specific enemy selection
    if selected_enemy:
        selected_enemy_row = win_rates[win_rates['enemy_champion'] == selected_enemy].copy()
        if not selected_enemy_row.empty:
            # Assign special color and hatch to the selected enemy
            selected_enemy_row['color'] = (
                '#2b93b6' if selected_enemy_row['win_rate_percent'].iloc[0] > overall_avg_win_rate else '#e54635'
            )
            selected_enemy_row['hatch'] = '/'

            # Update styling if the enemy is already in the dataset
            combined.update(selected_enemy_row)

            # If not already in the dataset, add it
            if selected_enemy not in combined['enemy_champion'].values:
                combined = pd.concat([combined, selected_enemy_row])

    # Update plot data
    combined = combined.sort_values(by="win_rate", ascending=False)
    winrate_source.data = combined.to_dict(orient='list')
    winrate_plot.x_range.factors = list(combined['enemy_champion'])
    winrate_plot.title.text = f"Win Rate Against Enemies as {champion_select.value} ({role_select.value}) - Showing Best and Worst Matchups"

    tap_tool = TapTool()
    winrate_plot.add_tools(tap_tool)

    hover = HoverTool(
        tooltips="""
        <div style="display: flex; align-items: center;">
            <div>
                <img src="@image_url" style="width: 50px; height: 50px; margin-right: 10px; border-radius: 5px;">
            </div>
            <div>
                <span style="font-size: 14px; font-weight: bold;">@enemy_champion</span><br>
                Win Rate: <span style="font-size: 12px;">@win_rate_percent%</span><br>
                Games Played: <span style="font-size: 12px;">@n_games</span>
            </div>
        </div>
        """
    )
    winrate_plot.add_tools(hover)

    avg_win_rate_line.location = overall_avg_win_rate


def on_bar_click(attr, old, new):
    """
    Callback for when a bar is clicked on the winrate plot.
    Updates the enemy_champion_select widget to the clicked enemy champion.
    """
    # Get the index of the selected bar
    selected_index = winrate_source.selected.indices

    # Ensure something is selected
    if selected_index:
        index = selected_index[0]  # Get the first selected index
        clicked_champion = winrate_source.data['enemy_champion'][index]  # Retrieve the clicked champion

        # Update the dropdown value programmatically
        enemy_champion_select.value = clicked_champion

    # Clear the selection to avoid visual artifacts
    winrate_source.selected.indices = []

# Initialize the plot
winrate_plot, avg_win_rate_line = create_winrate_plot()

# -------------------------------------------------------------------------------- #
# Ally Synergies Plot                                                              #
# -------------------------------------------------------------------------------- #

# Initialize empty data source for the ally synergies plot
ally_synergy_source = ColumnDataSource(data=dict(ally_champion=[], win_rate_percent=[], n_games=[], color=[]))

def calculate_ally_synergies(champion: str, role: str, ally_role: str) -> pd.DataFrame:
    """
    Calculate ally synergies based on the selected champion, role, and allies.
    Args:
        champion (str): Selected champion.
        role (str): User's role.
        ally_role (str): Selected ally role.
    Returns:
        pd.DataFrame: DataFrame containing ally synergy statistics.
    """
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

    # Exclude rows where the selected champion appears in the ally column
    filtered_df = filtered_df[filtered_df[ally_column] != champion]    

    # Aggregate win rates and game counts
    combined_df = filtered_df[['win', ally_column]].rename(columns={ally_column: 'ally_champion'})
    win_rates = (
        combined_df.groupby('ally_champion')['win']
        .agg(['mean', 'size'])
        .reset_index()
        .rename(columns={'mean': 'win_rate', 'size': 'n_games'})
    )
    win_rates['win_rate_percent'] = (win_rates['win_rate'] * 100).round(2)

    # Filter by minimum games threshold
    min_games = validate_numeric_input(ally_min_games_input.value, default=10)
    win_rates = win_rates[win_rates['n_games'] >= min_games]

    # Filter allies with win rates above the overall win rate
    overall_winrate = calculate_overall_win_rate(champion)
    win_rates = win_rates[win_rates['win_rate_percent'] > overall_winrate]

    return win_rates

def update_ally_synergy_plot(attr, old, new):
    """
    Update the ally synergy plot based on the selected ally role.
    """
    ally_role = ally_role_select.value
    if not ally_role or ally_role not in roles:
        ally_synergy_source.data = dict(ally_champion=[], win_rate_percent=[], n_games=[], color=[])
        ally_synergy_plot.x_range.factors = []
        ally_synergy_plot.title.text = "No role selected for ally synergies."
        return

    ally_data = calculate_ally_synergies(
        champion=champion_select.value,
        role=role_select.value,
        ally_role=ally_role
    )

    # Calculate overall win rate
    overall_winrate = calculate_overall_win_rate(champion_select.value)
    overall_winrate_line.location = overall_winrate

    # Sort allies by win rate in descending order
    ally_data = ally_data.sort_values(by='win_rate_percent', ascending=False)

    # Assign colors based on win rate
    ally_data['color'] = ally_data['win_rate_percent'].apply(
        lambda x: '#2b93b6' if x >= overall_winrate else '#e54635'
    )

    # Add image URLs dynamically
    ally_data['image_url'] = ally_data['ally_champion'].apply(
        lambda x: f"http://ddragon.leagueoflegends.com/cdn/14.20.1/img/champion/{x}.png"
    )

    # Update the plot with sorted data
    ally_synergy_source.data = ally_data.to_dict(orient='list')
    ally_synergy_plot.x_range.factors = list(ally_data['ally_champion'])
    ally_synergy_plot.title.text = f"Top Ally Synergies for {champion_select.value} ({role_select.value})"

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
    

    ally_data = calculate_ally_synergies(
        champion=champion_select.value,
        role=user_role,
        ally_role=ally_role
    )

    overall_winrate = calculate_overall_win_rate(champion_select.value)
    overall_winrate_line.location = overall_winrate

    # Sort allies by win rate
    ally_data = ally_data.sort_values(by='win_rate_percent', ascending=False)

    ally_data['color'] = ally_data['win_rate_percent'].apply(
        lambda x: '#2b93b6' if x >= overall_winrate else '#e54635'
    )

    # Add image URLs
    ally_data['image_url'] = ally_data['ally_champion'].apply(
        lambda x: f"http://ddragon.leagueoflegends.com/cdn/14.20.1/img/champion/{x}.png"
    )

    # Update the plot
    ally_synergy_source.data = ally_data.to_dict(orient='list')
    ally_synergy_plot.x_range.factors = list(ally_data['ally_champion'])
    ally_synergy_plot.title.text = f"Best {ally_role_select.value} Allies for {champion_select.value} ({role_select.value}) - Showing Synergies Above Average Win Rate"

    hover = HoverTool(
        tooltips="""
        <div style="display: flex; align-items: center;">
            <div>
                <img src="@image_url" style="width: 50px; height: 50px; margin-right: 10px; border-radius: 5px;">
            </div>
            <div>
                <span style="font-size: 14px; font-weight: bold;">@ally_champion</span><br>
                Win Rate: <span style="font-size: 12px;">@win_rate_percent%</span><br>
                Games Played: <span style="font-size: 12px;">@n_games</span>
            </div>
        </div>
        """
    )
    ally_synergy_plot.add_tools(hover)

def create_ally_synergy_plot():
    """
    Create the Ally Synergy plot.
    Returns:
        tuple: Bokeh figure and overall win rate line.
    """
    p = figure(x_range=[], height=370, width=1050, title="Ally Synergies", toolbar_location=None, tools="")

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

    hover = HoverTool(tooltips=[("Win Rate", "@win_rate_percent%"), ("Games Played", "@n_games"), ("Ally", "@ally_champion")])
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

    # Add invisible glyphs for the legend
    synergy_above_avg_glyph = p.vbar(x=[0], top=[1], fill_color='#2b93b6', line_color='white', width=0.1, visible=False)
    synergy_avg_line_glyph = p.line(x=[0, 1], y=[0, 1], line_color="black", line_dash="dashed", line_width=2, visible=False)

    # Create legend items
    legend_items = [
        LegendItem(label="Above Avg. Win Rate", renderers=[synergy_above_avg_glyph]),
        LegendItem(label="Average Win Rate", renderers=[synergy_avg_line_glyph])
    ]

    # Add the legend to the plot
    legend = Legend(items=legend_items, location="top_right", label_text_font_size="10pt")
    legend.background_fill_alpha = 0  # Transparent background
    legend.border_line_alpha = 0  # No border
    p.add_layout(legend)

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
    "image_url": [],  # Include image_url in the initial data
})

# Create Heatmap Figure
heatmap_plot = figure(
    title=f"Performance Metrics Against Opponents ({default_champion})",
    x_range=metric_labels,
    y_range=list(filtered_data['lane_opponent'].unique()),
    toolbar_location=None,
    tools="",
    width=700,  # Horizontal size
    height=530 # Vertical size
)

# Create the heatmap rectangles (renderer) and set the initial fill color
heatmap_renderer = heatmap_plot.rect(
    x="metric",
    y="lane_opponent",
    width=1,
    height=1,
    source=source,
    fill_color={"field": "value", "transform": color_mappers["normalized_winrate"]},  # Initial color mapper
    line_color=None
)

from bokeh.models import BoxAnnotation

row_highlight = BoxAnnotation(
    top=None,
    bottom=None,
    fill_alpha=0.0,  # No fill
    line_color="black",  # Black outline 
    line_width=3  # Thick outline
)
heatmap_plot.add_layout(row_highlight)



def update_row_highlight(attr, old, new):
    """
    Update the row highlight on the heatmap when a specific enemy is selected.
    If no enemy is selected, remove the highlight.
    """
    # Get the currently selected enemy
    selected_enemy = enemy_champion_select.value

    if not selected_enemy:  # No enemy selected
        row_highlight.bottom = None
        row_highlight.top = None
        row_highlight.line_alpha = 0.0  # Hide the outline
        return

    # Get the updated list of lane opponents from the heatmap's y-axis
    lane_opponents = heatmap_plot.y_range.factors

    if selected_enemy in lane_opponents:
        # Map the selected category to its numeric position
        idx = lane_opponents.index(selected_enemy) + 0.5  # Center of the row
        row_highlight.bottom = idx - 0.5  # Bottom of the box
        row_highlight.top = idx + 0.5    # Top of the box
        row_highlight.line_alpha = 1.0  # Make the outline visible
    else:  # If the selection is not in the heatmap
        row_highlight.bottom = None
        row_highlight.top = None
        row_highlight.line_alpha = 0.0  # Hide the outline



# Add a color bar to the heatmap
from bokeh.models import FixedTicker, PrintfTickFormatter

# Modify the color bar to remove numbers and add custom labels
color_bar = ColorBar(
    color_mapper=color_mappers["normalized_winrate"],  # Replace with your specific color mapper
    label_standoff=12,
    location=(0, 0),
    orientation="vertical",
    major_label_overrides={0: "", 0.2: "", 0.4: "", 0.6: "", 0.8: "", 1: "Better"},  # Override labels
    major_tick_line_color=None,  # Remove tick lines
    formatter=PrintfTickFormatter(format="")  # Remove numbers entirely
)
heatmap_plot.add_layout(color_bar, "right")


# Add HoverTool for interactivity
hover = HoverTool(
    tooltips="""
    <div style="display: flex; align-items: center;">
        <div>
            <img src="@image_url" style="width: 50px; height: 50px; margin-right: 10px; border-radius: 5px;">
        </div>
        <div>
            <span style="font-size: 14px; font-weight: bold;">@lane_opponent</span><br>
            Metric: <span style="font-size: 12px;">@metric</span><br>
            Normalized Value: <span style="font-size: 12px;">@value{0.2f}</span><br>
            Raw Value: <span style="font-size: 12px;">@raw_value{0.2f}</span><br>
            Games Played: <span style="font-size: 12px;">@n_games</span>
        </div>
    </div>
    """
)
heatmap_plot.add_tools(hover)

# Update Function for Heatmap
def update_heatmap(attr, old, new):
    """
    Dynamically update the heatmap based on the selected champion, role, metric, and threshold.
    """
    selected_champion = champion_select.value
    selected_sort_metric = metric_map[sort_select.value]  # Metric to sort by
    selected_role = role_select.value  # Selected role (TOP, JUNGLE, etc.)
    min_games = int(min_games_input.value) if min_games_input.value.isdigit() else 50

    # Define a mapping from lane_opponent to roles (adjust based on your data structure)
    role_map = {
        "TOP": "top_opponents",
        "JUNGLE": "jungle_opponents",
        "MID": "mid_opponents",
        "ADC": "adc_opponents",
        "SUPPORT": "support_opponents",
    }

    # Add a 'role' column to heatmap_data if it does not exist
    if "role" not in heatmap_data.columns:
        heatmap_data["role"] = heatmap_data["lane_opponent"].apply(
            lambda opponent: role_map.get(opponent.upper(), "UNKNOWN")
        )

    # Filter data for the selected champion, role, and minimum games
    updated_data = heatmap_data[
        (heatmap_data['champion'] == selected_champion) &
        (heatmap_data['role'] == selected_role) &  # Filter for the selected role
        (heatmap_data['n_games'] >= min_games)
    ]

    # Normalize the required columns for updated data
    metrics_to_normalize = [
        "normalized_winrate",
        "normalized_lane_minions_first_10_minutes",
        "normalized_max_cs_advantage_on_lane_opponent",
        "normalized_max_level_lead_lane_opponent",
        "normalized_turret_plates_taken",
        "normalized_solo_kills",
        "normalized_deaths",
    ]
    for metric in metrics_to_normalize:
        metric_raw = metric.replace("normalized_", "")
        if metric_raw in updated_data.columns:
            updated_data.loc[:, metric] = (
                updated_data[metric_raw] - updated_data[metric_raw].min()
            ) / (updated_data[metric_raw].max() - updated_data[metric_raw].min())

    # Invert deaths for better visualization
    updated_data.loc[:, 'normalized_deaths'] = 1 - updated_data['normalized_deaths']

    # Sort the data by the selected metric
    updated_data = updated_data.sort_values(by=selected_sort_metric, ascending=False)

    # Add image URLs
    updated_data['image_url'] = updated_data['lane_opponent'].apply(
        lambda x: f"http://ddragon.leagueoflegends.com/cdn/14.20.1/img/champion/{x}.png"
    )

    # Prepare new source data
    new_source_data = {
        "lane_opponent": [],
        "metric": [],
        "value": [],
        "raw_value": [],
        "n_games": [],
        "image_url": [],  # Add image URLs
    }

    # Populate the new data source with normalized values for metrics
    for metric, label in zip(metrics, metric_labels):
        raw_metric = raw_metric_map[label]
        for _, row in updated_data.iterrows():
            new_source_data["lane_opponent"].append(row["lane_opponent"])
            new_source_data["metric"].append(label)
            new_source_data["value"].append(row[metric])  # Normalized value
            new_source_data["raw_value"].append(row[raw_metric])  # Raw value for tooltip
            new_source_data["n_games"].append(row["n_games"])
            new_source_data["image_url"].append(row["image_url"])  # Image URL

    # Update the source data for the heatmap
    source.data = new_source_data

    # Dynamically update the y_range of the heatmap
    heatmap_plot.y_range.factors = list(reversed(updated_data['lane_opponent'].unique()))
    heatmap_plot.title.text = f"Performance Metrics Against {selected_role} Enemies as {selected_champion} ({selected_role}) - Color Ranked by Normalized Values"

    # Update the heatmap's fill_color dynamically
    heatmap_renderer.glyph.fill_color = {"field": "value", "transform": color_mappers[selected_sort_metric]}

    # Update the color bar to reflect the selected metric's color mapping
    color_bar.color_mapper = color_mappers[selected_sort_metric]

    tap_tool = TapTool()
    heatmap_plot.add_tools(tap_tool)

def on_heatmap_row_click(attr, old, new):
    """
    Callback for when a row (cell) in the heatmap is clicked.
    Updates the enemy_champion_select widget to the clicked lane opponent.
    """
    selected_index = source.selected.indices  # Get the selected indices

    if selected_index:  # Ensure something is selected
        index = selected_index[0]  # Get the first selected index
        clicked_opponent = source.data['lane_opponent'][index]  # Retrieve the opponent name

        # Update the dropdown value programmatically
        enemy_champion_select.value = clicked_opponent

    # Clear the selection to avoid visual artifacts
    source.selected.indices = []


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
        p = figure(title="Population Pyramid: No Data Available", height=400, width=650)
        return p

    # Prepare data for the pyramid
    freq = pyramid_data[['item_name', 'frequency_percentage']]
    winrate = pyramid_data[['item_name', 'win_rate']]

    merged_data = pd.merge(freq, winrate, on='item_name', suffixes=('_freq', '_winrate'))

    # Sort by the selected criterion
    if sort_by == "Frequency":
        merged_data.sort_values('frequency_percentage', ascending=False, inplace=True)
    elif sort_by == "Win Rate":
        merged_data.sort_values('win_rate', ascending=False, inplace=True)

    sorted_items = merged_data['item_name'][::-1]

    # Assign bar colors
    merged_data['frequency_color'] = [
        selected_blue_color if sort_by == "Frequency" else non_selected_gray_color
    ] * len(merged_data)
    merged_data['winrate_color'] = [
        selected_blue_color if sort_by == "Win Rate" else non_selected_gray_color
    ] * len(merged_data)

    # Negate frequency values for left-side rendering
    merged_data['frequency_percentage_neg'] = -merged_data['frequency_percentage']

    # Create a ColumnDataSource
    source = ColumnDataSource(merged_data)

    # Create the figure
    p = figure(
        title=f"Item Win Rate and Frequency for {champion_name} ({role_select.value}) - Min. 3% Frequency Items",
        height=250,
        width=650,
        x_range=(-100, 100),
        y_range=list(sorted_items),
        y_axis_label="",
        tools="",
    )

    # Add bars for frequency and win rate
    bin_width = 0.8
    p.hbar(
        y='item_name',
        right='frequency_percentage_neg',  # Negated for left-side rendering
        height=bin_width,
        color='frequency_color',  # Reference color column in the source
        legend_label="Frequency %",
        source=source,
    )
    p.hbar(
        y='item_name',
        right='win_rate',  # Positive for right-side rendering
        height=bin_width,
        color='winrate_color',  # Reference color column in the source
        legend_label="Win Rate %",
        source=source,
    )

    # Add HoverTool
    hover = HoverTool(
        tooltips=[
            ("Item", "@item_name"),
            ("Frequency (%)", "@frequency_percentage"),
            ("Win Rate (%)", "@win_rate"),
        ]
    )
    p.add_tools(hover)

    # Customize axes
    p.xaxis.ticker = list(range(-100, 101, 10))
    p.xaxis.formatter = CustomJSTickFormatter(code="return Math.abs(tick);")
    p.xaxis.axis_label = "Frequency      " + "%" + "     Win Rate"
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
    advanced_analysis_section.children[1].children[0] = column(sort_criterion_select, new_pyramid_plot)

pyramid_plot = create_population_pyramid()


#-------------------------------------------------------------------------------- #
#Layout Assembly and Final Setup                                                  #
#-------------------------------------------------------------------------------- #

# Spacer for visual alignment
spacer = Spacer(width=70, height=100)

selectors_with_info = row(
    row(champion_select, role_select),  # Align Champion and Role selectors horizontally
    champion_stats  # Combined image and stats
)


# Update the winrate section layout
winrate_section = column(
    selectors_with_info,  # Updated layout with image and stats
    row(enemy_role_select, min_games_input, enemy_champion_select),
    winrate_plot
)


# Layout for the Ally Synergies plot with widgets
ally_synergy_section = column(
    row(ally_role_select, ally_min_games_input),  # Ally Role and Min Games widgets
    ally_synergy_plot  # Synergies plot
)


# Create the Population Pyramid
pyramid_plot = create_population_pyramid()

# Define the advanced analysis section
advanced_analysis_section = column(
    row(column(sort_select, heatmap_plot)),
    row(column(sort_criterion_select, pyramid_plot))  # Population Pyramid
      # Heatmap and its sorting widget
)

left_padding = Spacer(width=25)  # Adjust the width as needed
top_padding = Spacer(height=10)  # Adjust the height as needed

 # Combine all sections into the final layout
layout = row(
    column(winrate_section, ally_synergy_section), spacer,
    advanced_analysis_section
)

# Adjust the layout
padded_layout = column(
    top_padding,  # Add padding to the top
    row(left_padding, layout), background="white" # Add left padding
)

# -------------------------------------------------------------------------------- #
# Attach Callbacks                                                                 #
# -------------------------------------------------------------------------------- #

# Global callbacks for Champion and Role selections + Stats
champion_select.on_change("value", update_champion_image_and_stats)


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

min_games_input.on_change("value", update_enemy_champion_options)
enemy_role_select.on_change("value", update_enemy_champion_options)
champion_select.on_change("value", update_enemy_champion_options)
role_select.on_change("value", update_enemy_champion_options)

enemy_role_select.on_change("value", update_winrate_plot_with_filters)

winrate_source.selected.on_change('indices', on_bar_click)

# Ally-specific callbacks
ally_min_games_input.on_change("value", update_ally_synergy_plot)
ally_role_select.on_change("value", update_ally_synergy_plot_on_role)


# Attach sort criterion callback for the Population Pyramid
sort_criterion_select.on_change("value", update_population_pyramid)

#Heatmap specific callbacks
# Attach callbacks for heatmap and highlight updates
sort_select.on_change("value", update_heatmap)  # Update heatmap data
sort_select.on_change("value", update_row_highlight)  # Ensure highlight box follows
enemy_champion_select.on_change("value", update_row_highlight)  # Update highlight on enemy selection
min_games_input.on_change("value", update_heatmap)

source.selected.on_change('indices', on_heatmap_row_click)




# -------------------------------------------------------------------------------- #
# Final Application Setup                                                          #
# -------------------------------------------------------------------------------- #

# Perform initial updates to ensure the application is initialized
update_enemy_champion_options(None, None, None)
update_winrate_plot_with_filters(None, None, None)
update_ally_synergy_plot_on_role(None, None, None)
update_heatmap(None, None, None)
update_champion_image_and_stats(None, None, None)  # Add this to update image and stats on startup
update_row_highlight(None, None, enemy_champion_select.value)

# Add the layout to the document
curdoc().clear()  # Clear any existing layout
curdoc().add_root(padded_layout)
