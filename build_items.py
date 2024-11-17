from bokeh.plotting import curdoc
from bokeh.models import Select, Div
from bokeh.layouts import column
import pandas as pd

# Load the game data and items data
game_data_path = 'cleaned_data.csv'  # Replace with your actual file path
items_data_path = 'items.csv'  # Replace with your actual file path
game_data = pd.read_csv(game_data_path)
items_data = pd.read_csv(items_data_path)

# Filter only specific categories from items_data
full_items = items_data[items_data['Category'] == 'Full Item']['Item'].tolist()
boots_items = items_data[items_data['Category'] == 'Boots']['Item'].tolist()
starter_items = items_data[items_data['Category'] == 'Starter Item']['Item'].tolist()

# Ensure item columns are strings
item_columns = ['item0', 'item1', 'item2', 'item3', 'item4', 'item5', 'item6']
for col in item_columns:
    game_data[col] = game_data[col].astype(str)

# Ensure the 'win' column is boolean
game_data['win'] = game_data['win'].astype(bool)

# Prepare the initial champion
initial_champion = game_data['champion'].unique()[0]

# Function to get the top 20 most common full items with win rates
def get_top_items(champion):
    filtered_data = game_data[game_data['champion'] == champion]
    
    # Melt the non-trinket item columns into a single column
    melted_items = filtered_data.melt(
        id_vars=['win'], 
        value_vars=['item0', 'item1', 'item2', 'item3', 'item4', 'item5'],
        value_name='item'
    )
    
    # Exclude empty slots ('0') and filter only "Full Item" items
    filtered_items = melted_items[(melted_items['item'] != '0') & (melted_items['item'].isin(full_items))]
    
    # Group by item and calculate stats
    item_stats = filtered_items.groupby('item').agg(
        count=('win', 'size'),
        wins=('win', 'sum')
    ).reset_index()
    item_stats['win_rate'] = (item_stats['wins'] / item_stats['count'] * 100).round(2)
    
    # Sort by count and get the top 20
    top_items = item_stats.sort_values('count', ascending=False).head(20)
    return top_items

# Function to get the top 3 most common trinkets with win rates
def get_top_trinkets(champion):
    filtered_data = game_data[game_data['champion'] == champion]
    
    # Use the trinket slot (item6) only
    trinket_stats = filtered_data[filtered_data['item6'] != '0'].groupby('item6').agg(
        count=('win', 'size'),
        wins=('win', 'sum')
    ).reset_index()
    trinket_stats['win_rate'] = (trinket_stats['wins'] / trinket_stats['count'] * 100).round(2)
    
    # Sort by count and get the top 3
    top_trinkets = trinket_stats.sort_values('count', ascending=False).head(3)
    return top_trinkets

# Function to get the top 3 most common boots with win rates
def get_top_boots(champion):
    filtered_data = game_data[game_data['champion'] == champion]
    
    # Melt the non-trinket item columns into a single column
    melted_items = filtered_data.melt(
        id_vars=['win'], 
        value_vars=['item0', 'item1', 'item2', 'item3', 'item4', 'item5'],
        value_name='item'
    )
    
    # Exclude empty slots ('0') and filter only "Boots" items
    filtered_boots = melted_items[(melted_items['item'] != '0') & (melted_items['item'].isin(boots_items))]
    
    # Group by item and calculate stats
    boots_stats = filtered_boots.groupby('item').agg(
        count=('win', 'size'),
        wins=('win', 'sum')
    ).reset_index()
    boots_stats['win_rate'] = (boots_stats['wins'] / boots_stats['count'] * 100).round(2)
    
    # Sort by count and get the top 3
    top_boots = boots_stats.sort_values('count', ascending=False).head(3)
    return top_boots

# Function to get the top 3 most common starter items with win rates
def get_top_starter_items(champion):
    filtered_data = game_data[game_data['champion'] == champion]
    
    # Melt the non-trinket item columns into a single column
    melted_items = filtered_data.melt(
        id_vars=['win'], 
        value_vars=['item0', 'item1', 'item2', 'item3', 'item4', 'item5'],
        value_name='item'
    )
    
    # Exclude empty slots ('0') and filter only "Starter Item" items
    filtered_starters = melted_items[(melted_items['item'] != '0') & (melted_items['item'].isin(starter_items))]
    
    # Group by item and calculate stats
    starter_stats = filtered_starters.groupby('item').agg(
        count=('win', 'size'),
        wins=('win', 'sum')
    ).reset_index()
    starter_stats['win_rate'] = (starter_stats['wins'] / starter_stats['count'] * 100).round(2)
    
    # Sort by count and get the top 3
    top_starters = starter_stats.sort_values('count', ascending=False).head(3)
    return top_starters

# Initial data for the first champion
initial_top_items = get_top_items(initial_champion)
initial_top_trinkets = get_top_trinkets(initial_champion)
initial_top_boots = get_top_boots(initial_champion)
initial_top_starter_items = get_top_starter_items(initial_champion)

# Create a Div to display the results
results_div = Div(text="", width=400)

# Update the Div content
def update_results(champion):
    # Get top items, trinkets, boots, and starter items
    top_items = get_top_items(champion)
    top_trinkets = get_top_trinkets(champion)
    top_boots = get_top_boots(champion)
    top_starters = get_top_starter_items(champion)
    
    # Build the HTML content
    text = "<h3>Top 20 Most Common Full Items</h3>"
    for _, row in top_items.iterrows():
        text += f"<p>{row['item']} - {row['count']} occurrences, {row['win_rate']}% win rate</p>"
    
    text += "<h3>Top 3 Most Common Trinkets</h3>"
    for _, row in top_trinkets.iterrows():
        text += f"<p>{row['item6']} - {row['count']} occurrences, {row['win_rate']}% win rate</p>"
    
    text += "<h3>Top 3 Most Common Boots</h3>"
    for _, row in top_boots.iterrows():
        text += f"<p>{row['item']} - {row['count']} occurrences, {row['win_rate']}% win rate</p>"
    
    text += "<h3>Top 3 Most Common Starter Items</h3>"
    for _, row in top_starters.iterrows():
        text += f"<p>{row['item']} - {row['count']} occurrences, {row['win_rate']}% win rate</p>"
    
    results_div.text = text

# Update results for the initial champion
update_results(initial_champion)

# Create a dropdown to select the champion
champion_select = Select(
    title="Select Champion",
    value=initial_champion,
    options=sorted(game_data['champion'].unique().tolist())
)

# Callback to update the results when the champion is changed
def champion_changed(attr, old, new):
    update_results(new)

champion_select.on_change('value', champion_changed)

# Layout
layout = column(champion_select, results_div)
curdoc().add_root(layout)
