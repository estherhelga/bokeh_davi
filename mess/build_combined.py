from bokeh.plotting import curdoc
from bokeh.models import Select, Div
from bokeh.layouts import column
import pandas as pd
import requests

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

# Load Summoner Spell Data from Data Dragon
summoner_spells_data = requests.get(
    "https://ddragon.leagueoflegends.com/cdn/14.20.1/data/en_US/summoner.json"
).json()
summoner_spells_mapping = {
    spell_data['id']: spell_data['image']['full'] for spell_data in summoner_spells_data['data'].values()
}
# Special cases for summoner spell icons
summoner_spell_exceptions = {
    "SummonerIgnite": "SummonerDot.png"
}

# Load Item Data from Data Dragon
item_data = requests.get(
    "https://ddragon.leagueoflegends.com/cdn/14.20.1/data/en_US/item.json"
).json()
item_mapping = {item_name: item_id for item_id, item_data in item_data['data'].items() for item_name in [item_data['name']]}

# Load Runes Data from Data Dragon
runes_data = requests.get(
    "https://ddragon.leagueoflegends.com/cdn/14.20.1/data/en_US/runesReforged.json"
).json()

# Build rune mappings
runes_mapping = {}

for style in runes_data:
    # Map primary style icons
    runes_mapping[style['name']] = style['icon']
    # Map keystone and minor runes within each style
    for slot in style['slots']:
        for rune in slot['runes']:
            runes_mapping[rune['name']] = rune['icon']

# Base URLs for icons
summoner_spell_icon_base_url = "https://ddragon.leagueoflegends.com/cdn/14.20.1/img/spell/"
item_icon_base_url = "https://ddragon.leagueoflegends.com/cdn/14.20.1/img/item/"
rune_icon_base_url = "https://ddragon.leagueoflegends.com/cdn/img/"

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
    if not starter_items_stats.empty:
        starter_icon = item_mapping.get(starter_items_stats['item'].values[0], "")
        text += (
            f'<p><b>Starter:</b> <img src="{item_icon_base_url}{starter_icon}.png" alt="{starter_icon}" width="32" height="32">'
            f' - {starter_items_stats["count"].values[0]} games, {starter_items_stats["win_rate"].values[0]}% win rate</p>'
        )
    if not boots_stats.empty:
        boots_icon = item_mapping.get(boots_stats['item'].values[0], "")
        text += (
            f'<p><b>Boots:</b> <img src="{item_icon_base_url}{boots_icon}.png" alt="{boots_icon}" width="32" height="32">'
            f' - {boots_stats["count"].values[0]} games, {boots_stats["win_rate"].values[0]}% win rate</p>'
        )
    text += "<p><b>Full Items:</b><br>"
    for _, row in full_items_stats.iterrows():
        item_icon = item_mapping.get(row['item'], "")
        text += (
            f'- <img src="{item_icon_base_url}{item_icon}.png" alt="{row["item"]}" width="32" height="32">'
            f' {row["item"]} - {row["count"]} games, {row["win_rate"]}% win rate<br>'
        )
    if not trinket_stats.empty:
        trinket_icon = item_mapping.get(trinket_stats['item'].values[0], "")
        text += (
            f'<b>Trinket:</b> <img src="{item_icon_base_url}{trinket_icon}.png" alt="{trinket_icon}" width="32" height="32">'
            f' - {trinket_stats["count"].values[0]} games, {trinket_stats["win_rate"].values[0]}% win rate</p>'
        )

    # Runes Section
    text += "<h4>Runes</h4><p>"
    for col, stats in runes.items():
        if stats is not None:
            rune_icon = runes_mapping.get(stats[col], "")  # Fetch icon using rune name
            text += (
                f'<b>{col.replace("_", " ").title()}:</b> '
                f'<img src="{rune_icon_base_url}{rune_icon}" alt="{stats[col]}" width="32" height="32"> '
                f'{stats[col]} - {stats["count"]} games, {stats["win_rate"]}% win rate<br>'
            )
    text += "</p>"
    
    # Summoner Spells Section with Icons
    text += "<h4>Summoner Spells</h4>"
    if spells is not None:
        spell1_name = f"Summoner{spells['summoner1_id']}"
        spell2_name = f"Summoner{spells['summoner2_id']}"
        spell1_icon = summoner_spell_exceptions.get(spell1_name, summoner_spells_mapping.get(spell1_name, ""))
        spell2_icon = summoner_spell_exceptions.get(spell2_name, summoner_spells_mapping.get(spell2_name, ""))
        text += (
            f'<p><img src="{summoner_spell_icon_base_url}{spell1_icon}" alt="{spell1_name}" width="32" height="32">'
            f' + <img src="{summoner_spell_icon_base_url}{spell2_icon}" alt="{spell2_name}" width="32" height="32">'
            f' - {spells["count"]} games, {spells["win_rate"]}% win rate</p>'
        )
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
