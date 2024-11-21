import pandas as pd
from bokeh.plotting import curdoc
from bokeh.models import ColumnDataSource, Select, DataTable, TableColumn, NumberFormatter, TextInput, CheckboxGroup, Div
from bokeh.layouts import column, row

# Load data (with the correct column names for the new metrics)
columns_to_load = [
    "champion", "lane_opponent", "win", "kills", "deaths", "assists", 
    "game_duration", "side", "team_damage_percentage", 
    "lane_minions_first_10_minutes", "max_cs_advantage_on_lane_opponent", 
    "max_level_lead_lane_opponent", "solo_kills", "turret_plates_taken", 
    "turret_kills", "first_blood", "first_tower", 
    "damage_dealt_to_buildings", "total_damage_dealt_champions"
]
df = pd.read_csv("cleaned_data.csv", usecols=columns_to_load)

# Filter for OTP champions
df = df[df["champion"].isin(["Aatrox", "Camille", "Gnar"])]

# Calculate average win rate for each champion
champion_winrates = df.groupby("champion")["win"].mean()

# Champion selection widget
champion_select = Select(title="Select Your Champion:", value="Aatrox", options=sorted(df["champion"].unique()))

# Display selected champion's average winrate
champion_winrate_display = Div(text=f"Average Winrate: {champion_winrates[champion_select.value]:.2%}", width=200)

# TextInput for minimum games cutoff
cutoff_input = TextInput(title="Minimum Games Cutoff", value="5")

# Checkbox to enable/disable cutoff
cutoff_checkbox = CheckboxGroup(labels=["Apply Minimum Games Cutoff"], active=[])

# Calculate matchup statistics, now including the new columns
def calculate_matchup_stats(df_filtered):
    # Calculate average win rate per side (using 'side' column)
    side_win_rates = df_filtered.groupby(['side', 'lane_opponent']).win.mean().unstack().fillna(0)

    # Aggregating other stats for each matchup
    matchups = df_filtered.groupby('lane_opponent').agg(
        total_games=('win', 'size'),
        wins=('win', lambda x: x.sum()),
        losses=('win', lambda x: (~x).sum()),  # Count losses
        avg_kills=('kills', 'mean'),
        avg_deaths=('deaths', 'mean'),
        avg_assists=('assists', 'mean'),
        avg_game_duration=('game_duration', lambda x: x.mean() / 60),  # Convert seconds to minutes
        avg_team_damage_percentage=('team_damage_percentage', 'mean'),
        avg_lane_minions_10=('lane_minions_first_10_minutes', 'mean'),
        avg_max_cs_advantage=('max_cs_advantage_on_lane_opponent', 'mean'),
        avg_max_level_lead=('max_level_lead_lane_opponent', 'mean'),
        avg_solo_kills=('solo_kills', 'mean'),
        avg_turret_plates_taken=('turret_plates_taken', 'mean'),
        avg_turret_kills=('turret_kills', 'mean'),
        first_blood_percentage=('first_blood', 'mean'),  # Percentage of games with first blood
        first_tower_percentage=('first_tower', 'mean'),  # Percentage of games with first tower
        avg_damage_to_buildings=('damage_dealt_to_buildings', 'mean'),
        avg_total_damage_to_champions=('total_damage_dealt_champions', 'mean')
    ).reset_index()
    matchups['winrate'] = (matchups['wins'] / matchups['total_games']).round(4)  # Keep as a decimal for Bokeh
    
    # Adding the side-specific win rates
    matchups['avg_red_side_win_rate'] = matchups['lane_opponent'].map(side_win_rates.loc['red'])
    matchups['avg_blue_side_win_rate'] = matchups['lane_opponent'].map(side_win_rates.loc['blue'])

    return matchups

# Create ColumnDataSource (initially empty, updated by callback)
source = ColumnDataSource(data=dict())

# Create interactive table with customized column widths, now including new columns with shortened titles
columns = [
    TableColumn(field="lane_opponent", title="Enemy Champion", width=150),
    TableColumn(field="total_games", title="Total Games", width=100),
    TableColumn(field="wins", title="Wins Against", width=100),
    TableColumn(field="losses", title="Losses Against", width=100),
    TableColumn(field="winrate", title="Winrate Against", width=120, formatter=NumberFormatter(format="0.00%")),
    TableColumn(field="avg_kills", title="Average Kills", width=100, formatter=NumberFormatter(format="0.00")),
    TableColumn(field="avg_deaths", title="Average Deaths", width=100, formatter=NumberFormatter(format="0.00")),
    TableColumn(field="avg_assists", title="Average Assists", width=100, formatter=NumberFormatter(format="0.00")),
    TableColumn(field="avg_game_duration", title="Game Duration (min)", width=150, formatter=NumberFormatter(format="0.0")),
    TableColumn(field="avg_red_side_win_rate", title="Red Win Rate", width=120, formatter=NumberFormatter(format="0.00%")),
    TableColumn(field="avg_blue_side_win_rate", title="Blue Win Rate", width=120, formatter=NumberFormatter(format="0.00%")),
    TableColumn(field="avg_team_damage_percentage", title="Team Dmg %", width=120, formatter=NumberFormatter(format="0.00%")),
    TableColumn(field="avg_lane_minions_10", title="Lane Minions (10min)", width=150, formatter=NumberFormatter(format="0.0")),
    TableColumn(field="avg_max_cs_advantage", title="CS Advantage", width=120, formatter=NumberFormatter(format="0.0")),
    TableColumn(field="avg_max_level_lead", title="Level Lead", width=120, formatter=NumberFormatter(format="0.0")),
    TableColumn(field="avg_solo_kills", title="Solo Kills", width=100, formatter=NumberFormatter(format="0.0")),
    TableColumn(field="avg_turret_plates_taken", title="Plates Taken", width=150, formatter=NumberFormatter(format="0.0")),
    TableColumn(field="avg_turret_kills", title="Turret Kills", width=120, formatter=NumberFormatter(format="0.0")),
    TableColumn(field="first_blood_percentage", title="First Blood", width=120, formatter=NumberFormatter(format="0.00%")),
    TableColumn(field="first_tower_percentage", title="First Tower", width=120, formatter=NumberFormatter(format="0.00%")),
    TableColumn(field="avg_damage_to_buildings", title="Dmg to Buildings", width=150, formatter=NumberFormatter(format="0.0")),
    TableColumn(field="avg_total_damage_to_champions", title="Dmg to Champs", width=150, formatter=NumberFormatter(format="0.0"))
]
data_table = DataTable(source=source, columns=columns, width=2000, height=400, sortable=True)

# Update function for main table
def update_table(attr, old, new):
    selected_champion = champion_select.value
    apply_cutoff = 0 in cutoff_checkbox.active  # Check if the checkbox is checked (active)

    # Validate the cutoff input
    try:
        min_games = int(cutoff_input.value)
        if min_games < 1:  # Ensure it’s a positive number
            min_games = 1
    except ValueError:
        min_games = 1  # Default to 1 if input is not a valid integer

    # Update the average win rate display for the selected champion
    avg_winrate = champion_winrates.get(selected_champion, 0)
    champion_winrate_display.text = f"Average Winrate: {avg_winrate:.2%}"

    # Filter data for the selected champion
    df_filtered = df[df["champion"] == selected_champion]
    matchups = calculate_matchup_stats(df_filtered)

    # Apply the cutoff if the checkbox is active
    if apply_cutoff:
        matchups = matchups[matchups['total_games'] >= min_games]

    # Update the data source with the filtered data
    source.data = {col: matchups[col].values for col in matchups.columns}

# Initial update
update_table(None, None, None)

# Attach callbacks
champion_select.on_change('value', update_table)
cutoff_input.on_change('value', update_table)
cutoff_checkbox.on_change('active', update_table)

# Layout
layout = column(row(champion_select, champion_winrate_display), row(cutoff_input, cutoff_checkbox), data_table)
curdoc().add_root(layout)
