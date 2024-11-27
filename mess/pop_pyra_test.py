import numpy as np
import pandas as pd
from bokeh.models import CustomJSTickFormatter, Label
from bokeh.plotting import figure
from bokeh.palettes import Category20c
from bokeh.io import curdoc

# Load and preprocess the data
item_data = pd.read_csv('final_item_champion_stats.csv')

# Filter the data for a specific champion, e.g., Aatrox
champion_name = "Aatrox"
item_data_filtered = item_data[(item_data['Category'].isin(['Full Item'])) & (item_data['champion'] == champion_name)].copy()

# Calculate frequency and win rate percentages
item_data_filtered['frequency_percentage'] = (
    item_data_filtered['occurrence_count'] / item_data_filtered['total_games_champion'] * 100
)
item_data_filtered['win_rate'] = (
    item_data_filtered['win_count'] / item_data_filtered['occurrence_count'] * 100
)
item_data_filtered = item_data_filtered[item_data_filtered['frequency_percentage'] >= 3]

# Select specific items (top N or filter criteria)
top_items = item_data_filtered['item_name'].unique()

# Prepare data for the pyramid
freq = item_data_filtered[['item_name', 'frequency_percentage']]
winrate = item_data_filtered[['item_name', 'win_rate']]

# Merge and ensure alignment
merged_data = pd.merge(freq, winrate, on='item_name', suffixes=('_freq', '_winrate'))
merged_data.sort_values('frequency_percentage', ascending=False, inplace=True)

# Set up Bokeh plot
bin_width = 0.8
color_frequency = Category20c[20][0]  # First color in the palette
color_winrate = Category20c[20][1]   # Second color in the palette

p = figure(
    title=f"Population Pyramid for {champion_name}: Frequency % vs Win Rate %",
    height=400, width=800,
    x_range=(-merged_data['win_rate'].max() - 5, merged_data['frequency_percentage'].max() + 5),
    y_range=list(merged_data['item_name']),
    y_axis_label="Items"
)

# Add bars for frequency %
p.hbar(
    y=merged_data['item_name'],
    right=merged_data['frequency_percentage'],
    height=bin_width,
    color=color_frequency,
    legend_label="Frequency %"
)

# Add bars for win rate %
p.hbar(
    y=merged_data['item_name'],
    right=-merged_data['win_rate'],  # Negate for left side
    height=bin_width,
    color=color_winrate,
    legend_label="Win Rate %"
)

# Customize x-axis and y-axis
p.xaxis.ticker = list(range(-100, 101, 10))  # Symmetrical ticks
p.xaxis.major_tick_out = 0
p.xaxis.formatter = CustomJSTickFormatter(code="return Math.abs(tick);")
p.xaxis.axis_label = "Percentage"

p.yaxis.axis_label = "Items"
p.yaxis.axis_label_text_font_size = "14pt"
p.yaxis.axis_label_standoff = 10

# Add labels for sides
p.add_layout(Label(x=-20, y=len(top_items)+1, text="Win Rate %", text_color=color_winrate))
p.add_layout(Label(x=20, y=len(top_items)+1, text="Frequency %", text_color=color_frequency))

p.legend.orientation = "horizontal"
p.legend.location = "top_center"

# Add the plot to the document
curdoc().add_root(p)
