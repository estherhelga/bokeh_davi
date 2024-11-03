import pandas as pd
from bokeh.plotting import figure, curdoc, output_file
from bokeh.models import ColumnDataSource, HoverTool
from bokeh.transform import dodge, factor_cmap
from bokeh.palettes import Category10_3

# Load necessary columns
columns_to_load = ["champion", "side", "win"]
df = pd.read_csv("cleaned_data.csv", usecols=columns_to_load)

# Filter data
df = df[df["champion"].isin(["Aatrox", "Camille", "Gnar"])]
df["side"] = df["side"].str.capitalize()

# Convert win to boolean
df['win'] = df['win'].astype(bool)

# Calculate win rates
win_rates = df.groupby(['champion', 'side'])['win'].mean().reset_index()

# Convert win rates to percentages
win_rates['win_rate_percent'] = (win_rates['win'] * 100).round(2)

#Add number of games played
n_games = df.groupby(['champion', 'side']).size().reset_index(name='n_games')
win_rates = pd.merge(win_rates, n_games, on=['champion', 'side'])

# Create ColumnDataSource
source = ColumnDataSource(win_rates)

# Split the data into two separate DataFrames for Blue and Red
blue_data = win_rates[win_rates['side'] == 'Blue']
red_data = win_rates[win_rates['side'] == 'Red']

# Create figure
p = figure(x_range=win_rates['champion'].unique(), height=350, title="Win Rate Comparison by Champion and Side",
           toolbar_location=None, tools="")

# Clustered vbar plot with adjusted dodge values
width = 0.2  # Width of the bars
blue_dodge = -width / 2  # Shift blue bars to the left
red_dodge = width / 2    # Shift red bars to the right

# Blue bars
p.vbar(x=dodge('champion', blue_dodge, range=p.x_range), top='win_rate_percent', width=width, source=ColumnDataSource(blue_data),
       legend_label='Blue', line_color='white', fill_color='blue')

# Red bars
p.vbar(x=dodge('champion', red_dodge, range=p.x_range), top='win_rate_percent', width=width, source=ColumnDataSource(red_data),
       legend_label='Red', line_color='white', fill_color='red')

# Add hover tool (shows win rate and number of games)
hover = HoverTool(tooltips=[("Win Rate", "@win_rate_percent%"), ("Number of Games", "@n_games")])
p.add_tools(hover)

p.xgrid.grid_line_color = None
p.y_range.start = 0
p.y_range.end = win_rates['win_rate_percent'].max() + 5  # Leave some headroom
p.yaxis.axis_label = "Win Rate (%)"
p.legend.orientation = "horizontal"  # Change legend orientation to vertical
p.legend.location = "top_right"     # Move legend to the top right corner

# Bokeh server setupp
curdoc().add_root(p)
