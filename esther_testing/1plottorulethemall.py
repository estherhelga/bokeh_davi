# -------------------------------------------------------------------------------- #
# Initialization and creation/loading of shared settings for all or multiple plots #
# -------------------------------------------------------------------------------- #

import pandas as pd
from bokeh.layouts import column, row
from bokeh.models import Select, TextInput, ColumnDataSource, HoverTool, Span
from bokeh.plotting import figure, curdoc

# Load the data
file_path = 'cleaned_data.csv'
df = pd.read_csv(file_path)
df['win'] = df['win'].astype(bool)

# Extract unique champions from the dataset
champions = sorted(df['champion'].unique().tolist())

# Define standard roles
roles = ['TOP', 'JUNGLE', 'MID', 'ADC', 'SUP']

# Create shared widgets
champion_select = Select(title="Select Your Champion:", value=champions[0], options=champions)
role_select = Select(title="Select Your Role:", value=roles[0], options=roles)
min_games_input = TextInput(title="Minimum Games Threshold:", value="10")
enemy_roles = ["ANY", "TOP", "JUNGLE", "MID", "ADC", "SUPPORT"]
enemy_role_select = Select(title="Enemy Role:", value="ANY", options=enemy_roles)
enemy_champion_select = Select(title="Compare Against Specific Enemy:", value="", options=[])

# -------------------------------------------------------------------------------- #
# Supporting Functions                                                             #
# -------------------------------------------------------------------------------- #

def calculate_overall_win_rate(champion):
    """Calculate the overall win rate for a champion."""
    champion_df = df[df['champion'] == champion]
    if champion_df.empty:
        return 0
    return (champion_df['win'].mean() * 100).round(2)


def update_enemy_champion_options(attr, old, new):
    """Update the enemy champion options based on the selected enemy role."""
    print(f"Enemy Role changed to: {enemy_role_select.value}")
    selected_role = enemy_role_select.value

    if selected_role == "ANY":
        # Combine all enemy columns
        unique_enemies = pd.concat([
            df['enemy_1'], df['enemy_2'], df['enemy_3'], df['enemy_4'], df['enemy_5']
        ]).unique()
    else:
        # Map role to the correct column
        role_column_map = {
            "TOP": "enemy_1",
            "JUNGLE": "enemy_2",
            "MID": "enemy_3",
            "ADC": "enemy_4",
            "SUPPORT": "enemy_5"
        }
        if selected_role in role_column_map:
            column = role_column_map[selected_role]
            unique_enemies = df[column].unique()
        else:
            unique_enemies = []

    if len(unique_enemies) == 0:
        print(f"No enemies found for role {selected_role}.")

    # Update the options in the enemy champion select widget
    enemy_champion_select.options = sorted(unique_enemies)
    print(f"Updated enemy options: {enemy_champion_select.options}")

# Attach callback to the enemy role dropdown
enemy_role_select.on_change('value', update_enemy_champion_options)

# -------------------------------------------------------------------------------- #
#               Creation of the Winrate against Enemies plot                       #
# -------------------------------------------------------------------------------- #

# Initialize empty data source for the plot
winrate_source = ColumnDataSource(data=dict(enemy_champion=[], win_rate_percent=[], n_games=[], color=[]))

# Function to create the Win Rate plot
def create_winrate_plot():
    p = figure(x_range=[], height=400, title="Win Rate Against Enemies", toolbar_location=None, tools="")
    p.vbar(x='enemy_champion', top='win_rate_percent', width=0.5, source=winrate_source, line_color="white", fill_color='color')

    hover = HoverTool(tooltips=[("Win Rate", "@win_rate_percent%"), ("Games Played", "@n_games")])
    p.add_tools(hover)

    p.y_range.start = 0
    p.y_range.end = 100
    p.yaxis.axis_label = "Win Rate (%)"
    p.xaxis.major_label_orientation = 0.785

    avg_win_rate_line = Span(location=0, dimension='width', line_color='black', line_dash='dashed', line_width=2)
    p.add_layout(avg_win_rate_line)

    return p, avg_win_rate_line

# Initialize the plot
winrate_plot, avg_win_rate_line = create_winrate_plot()


def update_winrate_plot_with_filters(attr, old, new):
    """Update the Win Rate plot based on filters."""
    global overall_avg_win_rate

    # Recalculate the overall average win rate when the champion changes
    overall_avg_win_rate = calculate_overall_win_rate(champion_select.value)
    print(f"Overall average win rate for {champion_select.value}: {overall_avg_win_rate}%")

    min_games = int(min_games_input.value) if min_games_input.value.isdigit() else 10
    selected_role = enemy_role_select.value
    selected_enemy = enemy_champion_select.value if enemy_champion_select.value else None

    # Step 1: Filter data for the selected champion and role
    filtered_df = df[(df['champion'] == champion_select.value) & (df['team_position'] == role_select.value)]
    print(f"Filtered DataFrame after Champion and Role filtering: {filtered_df.shape[0]} rows")

    # Step 2: Handle the "ANY" role (combine all enemy columns)
    if selected_role == "ANY":
        filtered_df = pd.concat([
            filtered_df[['win', 'enemy_1']].rename(columns={'enemy_1': 'enemy_champion'}),
            filtered_df[['win', 'enemy_2']].rename(columns={'enemy_2': 'enemy_champion'}),
            filtered_df[['win', 'enemy_3']].rename(columns={'enemy_3': 'enemy_champion'}),
            filtered_df[['win', 'enemy_4']].rename(columns={'enemy_4': 'enemy_champion'}),
            filtered_df[['win', 'enemy_5']].rename(columns={'enemy_5': 'enemy_champion'})
        ])
    else:
        # Handle specific enemy roles
        role_column_map = {
            "TOP": "enemy_1",
            "JUNGLE": "enemy_2",
            "MID": "enemy_3",
            "ADC": "enemy_4",
            "SUPPORT": "enemy_5"
        }
        if selected_role in role_column_map:
            column = role_column_map[selected_role]
            filtered_df = filtered_df.rename(columns={column: "enemy_champion"})

    # Step 3: Calculate win rates
    win_rates = (
        filtered_df.groupby('enemy_champion')['win']
        .agg(['mean', 'size'])
        .reset_index()
    )
    win_rates.columns = ['enemy_champion', 'win_rate', 'n_games']
    win_rates['win_rate_percent'] = (win_rates['win_rate'] * 100).round(2)
    win_rates = win_rates[win_rates['n_games'] >= min_games]

    # Step 4: Sort by win rate and select top and bottom 5 matchups
    win_rates_sorted = win_rates.sort_values(by="win_rate", ascending=False)
    top_5 = win_rates_sorted.head(5)
    bottom_5 = win_rates_sorted.tail(5)

    # Add bar colors
    top_5['color'] = '#2b93b6'  # Blue for top matchups
    bottom_5['color'] = '#e54635'  # Red for bottom matchups

    # Step 5: Include the selected enemy in the plot
    if selected_enemy and selected_enemy in win_rates['enemy_champion'].values:
        selected_enemy_row = win_rates[win_rates['enemy_champion'] == selected_enemy].copy()
        selected_enemy_row['color'] = '#d3d3d3'  # Neutral gray for the selected enemy
        combined = pd.concat([top_5, bottom_5, selected_enemy_row]).drop_duplicates(subset=['enemy_champion'])
    else:
        combined = pd.concat([top_5, bottom_5])

    # Ensure 'color' column exists for all rows in combined
    combined['color'] = combined['color'].fillna('#d3d3d3')  # Default to gray for safety

    # Step 6: Update the plot's data source
    combined = combined.sort_values(by="win_rate", ascending=False)  # Re-sort for display
    winrate_source.data = ColumnDataSource.from_df(combined)
    winrate_plot.x_range.factors = list(combined['enemy_champion'])
    winrate_plot.title.text = f"Win Rate Against Enemies as {champion_select.value} ({role_select.value})"

    # Set the dashed line's location to the overall win rate
    avg_win_rate_line.location = overall_avg_win_rate

# -------------------------------------------------------------------------------- #
# Layout and Initial Update                                                        #
# -------------------------------------------------------------------------------- #

layout = column(
    row(champion_select, role_select),
    row(enemy_role_select, min_games_input, enemy_champion_select),
    winrate_plot
)

# Attach callbacks
champion_select.on_change('value', update_winrate_plot_with_filters)
role_select.on_change('value', update_winrate_plot_with_filters)
min_games_input.on_change('value', update_winrate_plot_with_filters)
enemy_role_select.on_change('value', update_winrate_plot_with_filters)
enemy_champion_select.on_change('value', update_winrate_plot_with_filters)

# Initial update
update_enemy_champion_options(None, None, None)
update_winrate_plot_with_filters(None, None, None)

# Add layout to curdoc
curdoc().add_root(layout)




