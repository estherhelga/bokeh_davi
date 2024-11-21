from bokeh.plotting import curdoc, figure
from bokeh.models import ColumnDataSource, HoverTool
from bokeh.layouts import column
import pandas as pd
import requests

# Data Loading
file_path = 'cleaned_data.csv'  # Replace with your actual file path
items_file = 'items.csv'
data = pd.read_csv(file_path)
items_data = pd.read_csv(items_file)

# Ensure columns are strings
for col in ['item0', 'item1', 'item2', 'item3', 'item4', 'item5', 'item6']:
    data[col] = data[col].astype(str)
data['win'] = data['win'].astype(bool)

# Data Dragon URLs
item_data = requests.get(
    "https://ddragon.leagueoflegends.com/cdn/14.20.1/data/en_US/item.json"
).json()
item_mapping = {item_name: item_id for item_id, item_data in item_data['data'].items() for item_name in [item_data['name']]}
item_icon_base_url = "https://ddragon.leagueoflegends.com/cdn/14.20.1/img/item/"

# Item Categories
starter_items = set(items_data[items_data['Category'] == 'Starter Item']['Item'])
boots_items = set(items_data[items_data['Category'] == 'Boots']['Item'])
full_items = set(items_data[items_data['Category'] == 'Full Item']['Item'])
trinket_items = set(items_data[items_data['Category'] == 'Trinket']['Item'])

# Helper: Get Most Common Items
def get_most_common_items(champion, item_set, count=5):
    filtered_data = data[data['champion'] == champion]
    melted_items = filtered_data.melt(
        id_vars=['win'],
        value_vars=['item0', 'item1', 'item2', 'item3', 'item4', 'item5', 'item6'],
        value_name='item'
    )
    filtered_items = melted_items[melted_items['item'].isin(item_set)]
    item_stats = filtered_items.groupby('item').agg(
        count=('win', 'size'),
        wins=('win', 'sum')
    ).reset_index()
    item_stats['win_rate'] = (item_stats['wins'] / item_stats['count'] * 100).round(2)
    item_stats = item_stats.sort_values('count', ascending=False).head(count)
    return item_stats

# Create Icon Figures with Tooltips
def create_item_figure(item_stats, title):
    icons = [
        item_icon_base_url + item_mapping.get(row['item'], "") + ".png"
        for _, row in item_stats.iterrows()
    ]
    tooltips = [
        f"{row['item']} - {row['count']} games, {row['win_rate']}% win rate"
        for _, row in item_stats.iterrows()
    ]
    source = ColumnDataSource(data=dict(
        url=icons,
        tooltip=tooltips,
        x=list(range(len(icons))),
        y=[0] * len(icons)
    ))

    plot_width = 60 * len(icons)  # Dynamically adjust width based on icons
    p = figure(title=title, x_range=(-0.5, len(icons) - 0.5), y_range=(-0.5, 0.5),
               width=plot_width, height=80, toolbar_location=None)

    p.image_url(url='url', x='x', y='y', w=0.8, h=0.8, source=source)  # Square ratio
    p.axis.visible = False
    p.grid.visible = False
    p.title.align = "center"
    p.title.text_font_size = "10pt"
    p.add_tools(HoverTool(tooltips=[("Info", "@tooltip")]))
    return p


# Champion Selection
initial_champion = data['champion'].unique()[0]

def update_items(champion):
    # Get item stats
    starter_stats = get_most_common_items(champion, starter_items, count=1)
    boots_stats = get_most_common_items(champion, boots_items, count=1)
    full_item_stats = get_most_common_items(champion, full_items, count=5)
    trinket_stats = get_most_common_items(champion, trinket_items, count=1)

    # Create item figures
    starter_fig = create_item_figure(starter_stats, "Starter Items")
    boots_fig = create_item_figure(boots_stats, "Boots")
    full_items_fig = create_item_figure(full_item_stats, "Full Items")
    trinket_fig = create_item_figure(trinket_stats, "Trinket")

    # Update layout
    layout.children = [starter_fig, boots_fig, full_items_fig, trinket_fig]

# Initial Layout
layout = column()
update_items(initial_champion)

curdoc().add_root(layout)
