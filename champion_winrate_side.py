import pandas as pd
from bokeh.plotting import figure, curdoc
from bokeh.models import ColumnDataSource, HoverTool, MultiSelect, LabelSet
from bokeh.layouts import column
from bokeh.transform import dodge

# Load necessary columns
columns_to_load = ["champion", "side", "win"]
df = pd.read_csv("cleaned_data.csv", usecols=columns_to_load)

# Filter data
df["side"] = df["side"].str.capitalize()
df['win'] = df['win'].astype(bool)

# Calculate win rates
win_rates = df.groupby(['champion', 'side'])['win'].mean().reset_index()
win_rates['win_rate_percent'] = (win_rates['win'] * 100).round(2)

# Add number of games played
n_games = df.groupby(['champion', 'side']).size().reset_index(name='n_games')
win_rates = pd.merge(win_rates, n_games, on=['champion', 'side'])

# Calculate win_rate_diff between blue and red sides (absolute value)
blue_win_rates = win_rates[win_rates['side'] == 'Blue'].set_index('champion')
red_win_rates = win_rates[win_rates['side'] == 'Red'].set_index('champion')

win_rate_diff = (blue_win_rates['win_rate_percent'] - red_win_rates['win_rate_percent']).abs().round(1)
win_rate_diff_df = pd.DataFrame({
    'champion': win_rate_diff.index,
    'win_rate_diff': 'Δ ' + win_rate_diff.astype(str) + '%'
}).reset_index(drop=True)

# Merge win_rate_diff into the original DataFrame
win_rates = pd.merge(win_rates, win_rate_diff_df, on='champion', how='left')

# Create initial data sources for blue and red sides
blue_data = win_rates[win_rates['side'] == 'Blue']
red_data = win_rates[win_rates['side'] == 'Red']
blue_source = ColumnDataSource(blue_data)
red_source = ColumnDataSource(red_data)

# Create a label source for the win rate differences
label_source = ColumnDataSource(win_rate_diff_df)

# Initial filter on champions
initial_champions = ["Aatrox", "Camille", "Gnar"]

# Create figure
p = figure(x_range=initial_champions, height=350, title="Win Rate Comparison by Champion and Side",
           toolbar_location=None, tools="")

# Clustered vbar plot with adjusted dodge values
width = 0.2  # Width of the bars
blue_dodge = -width / 2  # Shift blue bars to the left
red_dodge = width / 2    # Shift red bars to the right

# Blue bars
p.vbar(x=dodge('champion', blue_dodge, range=p.x_range), top='win_rate_percent', width=width,
       source=blue_source, legend_label='Blue', line_color='white', fill_color='#2b93b6')

# Red bars
p.vbar(x=dodge('champion', red_dodge, range=p.x_range), top='win_rate_percent', width=width,
       source=red_source, legend_label='Red', line_color='white', fill_color='#e54635')

# Add hover tool
hover = HoverTool(tooltips=[("Win Rate", "@win_rate_percent%"), ("Number of Games", "@n_games")])
p.add_tools(hover)

p.xgrid.grid_line_color = None
p.y_range.start = 0
p.y_range.end = win_rates['win_rate_percent'].max() + 10  # Leave more headroom for labels
p.yaxis.axis_label = "Win Rate (%)"
p.legend.orientation = "horizontal"  # Change legend orientation to horizontal
p.legend.location = "bottom_right"   # Move legend to the bottom right corner

# Add labels for win rate difference, positioned above the bars
labels = LabelSet(x='champion', y=blue_data['win_rate_percent'].max() + 5, text='win_rate_diff',
                  source=label_source, text_align='center', text_font_size="10pt")

p.add_layout(labels)

# Create a MultiSelect widget for champion selection
champion_select = MultiSelect(title="Select Champions:", value=initial_champions,
                              options=sorted(df['champion'].unique().tolist()))

# Update callback function
def update_plot(attr, old, new):
    selected_champions = champion_select.value
    filtered_blue_data = blue_data[blue_data['champion'].isin(selected_champions)]
    filtered_red_data = red_data[red_data['champion'].isin(selected_champions)]
    blue_source.data = ColumnDataSource.from_df(filtered_blue_data)
    red_source.data = ColumnDataSource.from_df(filtered_red_data)
    
    filtered_diff_data = win_rate_diff_df[win_rate_diff_df['champion'].isin(selected_champions)]
    label_source.data = ColumnDataSource.from_df(filtered_diff_data)

    p.x_range.factors = selected_champions  # Update x_range with selected champions

# Attach callback to the widget
champion_select.on_change('value', update_plot)

# Layout setup
layout = column(champion_select, p)

# Bokeh server setup
curdoc().add_root(layout)
