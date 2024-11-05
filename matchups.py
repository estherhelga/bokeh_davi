import pandas as pd
from bokeh.plotting import curdoc
from bokeh.models import ColumnDataSource, Select, DataTable, TableColumn, NumberFormatter
from bokeh.layouts import column


# Load data (relevant columns only)
columns_to_load = ["champion", "lane_opponent", "win"]
df = pd.read_csv("cleaned_data.csv", usecols=columns_to_load)


# Filter for OTP champions and capitalize 'side'
df = df[df["champion"].isin(["Aatrox", "Camille", "Gnar"])]

# Champion selection widget
champion_select = Select(title="Select Your Champion:", value="Aatrox", options=sorted(df["champion"].unique()))

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

# Create interactive table
columns = [
    TableColumn(field="lane_opponent", title="Enemy Champion"),
    TableColumn(field="total_games", title="Total Games"),
    TableColumn(field="wins", title="Wins Against"),
    TableColumn(field="losses", title="Losses Against"),
    TableColumn(field="winrate", title="Winrate Against", formatter=NumberFormatter(format="0.00%")),

]
data_table = DataTable(source=source, columns=columns, width=400, height=400, sortable=True)


# Update function
def update_table(attr, old, new):
    selected_champion = champion_select.value
    df_filtered = df[df["champion"] == selected_champion]

    matchups = calculate_matchup_stats(df_filtered)
    source.data = matchups

# Initial update
update_table(None, None, None)


champion_select.on_change('value', update_table)



# Layout
layout = column(champion_select, data_table)
curdoc().add_root(layout)