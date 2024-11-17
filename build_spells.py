from bokeh.plotting import curdoc
from bokeh.models import Select, Div
from bokeh.layouts import column
import pandas as pd

# Load the data
file_path = 'cleaned_data.csv'  # Replace with your actual file path
data = pd.read_csv(file_path)

# Ensure summoner spells are strings (if needed)
data['summoner1_id'] = data['summoner1_id'].astype(str)
data['summoner2_id'] = data['summoner2_id'].astype(str)

# Normalize summoner spell combinations by sorting the IDs
data['summoner_spell_combination'] = data[['summoner1_id', 'summoner2_id']].apply(
    lambda row: " + ".join(sorted(row)), axis=1
)

# Prepare the initial champion
initial_champion = data['champion'].unique()[0]

# Function to get the top 3 summoner spell combinations with win rates
def get_top_summoner_spells(champion):
    filtered_data = data[data['champion'] == champion]
    spell_stats = filtered_data.groupby('summoner_spell_combination').agg(
        Count=('win', 'size'),
        Wins=('win', 'sum')
    ).reset_index()
    spell_stats['Win Rate'] = (spell_stats['Wins'] / spell_stats['Count'] * 100).round(2)
    top_combinations = spell_stats.nlargest(3, 'Count')  # Get top 3 by count
    return top_combinations

# Initial data for the first champion
initial_top_spells = get_top_summoner_spells(initial_champion)

# Create a Div to display the top combinations with win rates
results_div = Div(text="", width=400)

# Update the Div content
def update_results(champion):
    top_spells = get_top_summoner_spells(champion).reset_index(drop=True)  # Reset index here
    text = "<h3>Top 3 Summoner Spell Combinations</h3>"
    for _, row in top_spells.iterrows():  # No enumeration here
        text += (
            f"<p>{row['summoner_spell_combination']} - "
            f"{row['Count']} games, {row['Win Rate']}% win rate</p>"
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
