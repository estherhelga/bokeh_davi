from bokeh.plotting import curdoc
from bokeh.models import Select, Div
from bokeh.layouts import column
import pandas as pd

# Load the data
file_path = 'cleaned_data.csv'  # Replace with your actual file path
data = pd.read_csv(file_path)

# Ensure all rune-related columns are strings
rune_columns = [
    'perk_keystone', 'perk_primary_row_1', 'perk_primary_row_2', 'perk_primary_row_3',
    'perk_secondary_row_1', 'perk_secondary_row_2', 'perk_primary_style',
    'perk_secondary_style', 'perk_shard_defense', 'perk_shard_flex', 'perk_shard_offense'
]
for col in rune_columns:
    data[col] = data[col].astype(str)

# Ensure 'win' column is boolean
data['win'] = data['win'].astype(bool)

# Prepare the initial champion
initial_champion = data['champion'].unique()[0]

# Function to get the top 3 runes with win rates for a specific column
def get_top_runes(champion, column):
    filtered_data = data[data['champion'] == champion]
    
    # Group by rune, calculate count and win rate
    rune_stats = filtered_data.groupby(column).agg(
        count=('win', 'size'),
        wins=('win', 'sum')
    ).reset_index()
    rune_stats['win_rate'] = (rune_stats['wins'] / rune_stats['count'] * 100).round(2)
    rune_stats = rune_stats.rename(columns={column: 'rune'})
    
    # Sort by count and get the top 3
    top_runes = rune_stats.sort_values('count', ascending=False).head(3)
    return top_runes

# Initial data for the first champion
initial_results = {}
for col in rune_columns:
    initial_results[col] = get_top_runes(initial_champion, col)

# Create a Div to display the results
results_div = Div(text="", width=600)

# Update the Div content
def update_results(champion):
    text = f"<h3>Top 3 Runes for {champion}</h3>"
    
    for col in rune_columns:
        text += f"<h4>{col.replace('_', ' ').title()}</h4>"
        top_runes = get_top_runes(champion, col)
        for i, row in top_runes.iterrows():
            text += (
                f"<p>{row['rune']} - {row['count']} occurrences, {row['win_rate']}% win rate</p>"
            )
    
    results_div.text = text

# Update results for the initial champion
update_results(initial_champion)

# Create a dropdown to select the champion
champion_select = Select(
    title="Select Champion",
    value=initial_champion,
    options=sorted(data['champion'].unique().tolist())
)

# Callback to update the results when the champion is changed
def champion_changed(attr, old, new):
    update_results(new)

champion_select.on_change('value', champion_changed)

# Layout
layout = column(champion_select, results_div)
curdoc().add_root(layout)
