from bokeh.plotting import curdoc
from bokeh.models import Select, Div
from bokeh.layouts import column
import pandas as pd

# Load the data
file_path = 'cleaned_data.csv'  # Replace with your actual file path
items_file = 'items.csv'
data = pd.read_csv(file_path)
items_data = pd.read_csv(items_file)

# Ensure columns are strings
for col in ['item0', 'item1', 'item2', 'item3', 'item4', 'item5', 'item6']:
    data[col] = data[col].astype(str)

for col in [
    'perk_keystone', 'perk_primary_row_1', 'perk_primary_row_2', 'perk_primary_row_3',
    'perk_secondary_row_1', 'perk_secondary_row_2', 'perk_primary_style',
    'perk_secondary_style', 'perk_shard_defense', 'perk_shard_flex', 'perk_shard_offense',
    'summoner1_id', 'summoner2_id'
]:
    data[col] = data[col].astype(str)

# Ensure 'win' column is boolean
data['win'] = data['win'].astype(bool)

# Prepare the initial champion
initial_champion = data['champion'].unique()[0]

# Filter item categories
full_items = set(items_data[items_data['Category'] == 'Full Item']['Item'])
starter_items = set(items_data[items_data['Category'] == 'Starter Item']['Item'])
boots_items = set(items_data[items_data['Category'] == 'Boots']['Item'])
trinket_items = set(items_data[items_data['Category'] == 'Trinket']['Item'])

# Helper function to get the most common items with win rates
def get_most_common_items(champion, item_set, count=5):
    filtered_data = data[data['champion'] == champion]
    melted_items = filtered_data.melt(
        id_vars=['win'],
        value_vars=['item0', 'item1', 'item2', 'item3', 'item4', 'item5', 'item6'],
        value_name='item'
    )
    
    # Filter items by category
    filtered_items = melted_items[melted_items['item'].isin(item_set)]
    item_stats = filtered_items.groupby('item').agg(
        count=('win', 'size'),
        wins=('win', 'sum')
    ).reset_index()
    item_stats['win_rate'] = (item_stats['wins'] / item_stats['count'] * 100).round(2)
    item_stats = item_stats.sort_values('count', ascending=False).head(count)
    return item_stats

# Helper function to get the most common runes with win rates
def get_most_common_runes(champion):
    filtered_data = data[data['champion'] == champion]
    runes = {}
    for col in [
        'perk_keystone', 'perk_primary_row_1', 'perk_primary_row_2', 'perk_primary_row_3',
        'perk_secondary_row_1', 'perk_secondary_row_2', 'perk_primary_style',
        'perk_secondary_style', 'perk_shard_defense', 'perk_shard_flex', 'perk_shard_offense'
    ]:
        stats = filtered_data.groupby(col).agg(
            count=('win', 'size'),
            wins=('win', 'sum')
        ).reset_index()
        stats['win_rate'] = (stats['wins'] / stats['count'] * 100).round(2)
        stats = stats.sort_values('count', ascending=False).head(1)
        runes[col] = stats.iloc[0] if not stats.empty else None
    return runes

# Helper function to get the most common summoner spell combination with win rates
def get_most_common_summoner_spells(champion):
    filtered_data = data[data['champion'] == champion]
    spells = (
        filtered_data.groupby(['summoner1_id', 'summoner2_id'])
        .agg(count=('win', 'size'), wins=('win', 'sum'))
        .reset_index()
    )
    spells['win_rate'] = (spells['wins'] / spells['count'] * 100).round(2)
    spells = spells.sort_values('count', ascending=False).head(1)
    return spells.iloc[0] if not spells.empty else None

# Update the Div content
def update_results(champion):
    # Fetch the most common items
    starter_items_stats = get_most_common_items(champion, starter_items, count=1)
    boots_stats = get_most_common_items(champion, boots_items, count=1)
    full_items_stats = get_most_common_items(champion, full_items, count=5)
    trinket_stats = get_most_common_items(champion, trinket_items, count=1)
    runes = get_most_common_runes(champion)
    spells = get_most_common_summoner_spells(champion)
    
    # Build the HTML content
    text = f"<h3>Most Common Build for {champion}</h3>"
    
    # Items Section
    text += "<h4>Items</h4>"
    text += f"<p><b>Starter:</b> {starter_items_stats['item'].values[0]} - {starter_items_stats['count'].values[0]} games, {starter_items_stats['win_rate'].values[0]}% win rate</p>" if not starter_items_stats.empty else "<p><b>Starter:</b> None</p>"
    text += f"<p><b>Boots:</b> {boots_stats['item'].values[0]} - {boots_stats['count'].values[0]} games, {boots_stats['win_rate'].values[0]}% win rate</p>" if not boots_stats.empty else "<p><b>Boots:</b> None</p>"
    text += "<p><b>Full Items:</b><br>"
    for _, row in full_items_stats.iterrows():
        text += f"- {row['item']} - {row['count']} games, {row['win_rate']}% win rate<br>"
    text += f"<b>Trinket:</b> {trinket_stats['item'].values[0]} - {trinket_stats['count'].values[0]} games, {trinket_stats['win_rate'].values[0]}% win rate</p>" if not trinket_stats.empty else "<p><b>Trinket:</b> None</p>"
    
    # Runes Section
    text += "<h4>Runes</h4><p>"
    for col, stats in runes.items():
        if stats is not None:
            text += f"<b>{col.replace('_', ' ').title()}:</b> {stats[col]} - {stats['count']} games, {stats['win_rate']}% win rate<br>"
    text += "</p>"
    
    # Summoner Spells Section
    text += "<h4>Summoner Spells</h4>"
    if spells is not None:
        text += f"<p>{spells['summoner1_id']} + {spells['summoner2_id']} - {spells['count']} games, {spells['win_rate']}% win rate</p>"
    else:
        text += "<p>None</p>"
    
    results_div.text = text

# Initial data for the first champion
results_div = Div(text="", width=600)
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
