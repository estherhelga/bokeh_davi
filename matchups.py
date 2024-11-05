import pandas as pd
from bokeh.plotting import curdoc
from bokeh.models import ColumnDataSource, Select, DataTable, TableColumn, NumberFormatter, TextInput, CheckboxGroup, Div
from bokeh.layouts import column, row

# Load data (relevant columns only)
columns_to_load = ["champion", "lane_opponent", "win"]
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

# Calculate matchup statistics
def calculate_matchup_stats(df_filtered):
    matchups = df_filtered.groupby('lane_opponent').agg(
        total_games=('win', 'size'),
        wins=('win', lambda x: x.sum()),
        losses=('win', lambda x: (~x).sum())  # Count losses
    ).reset_index()
    matchups['winrate'] = (matchups['wins'] / matchups['total_games']).round(4)  # Keep as a decimal for Bokeh
    return matchups

# Create ColumnDataSource (initially empty, updated by callback)
source = ColumnDataSource(data=dict())

# Create interactive table with customized column widths
columns = [
    TableColumn(field="lane_opponent", title="Enemy Champion", width=150),
    TableColumn(field="total_games", title="Total Games", width=100),
    TableColumn(field="wins", title="Wins Against", width=100),
    TableColumn(field="losses", title="Losses Against", width=100),
    TableColumn(field="winrate", title="Winrate Against", width=120, formatter=NumberFormatter(format="0.00%")),
]
data_table = DataTable(source=source, columns=columns, width=570, height=400, sortable=True)

# Update function
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
