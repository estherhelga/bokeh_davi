import pandas as pd
from bokeh.plotting import figure, curdoc
from bokeh.models import ColumnDataSource, HoverTool, MultiSelect, LabelSet, Span
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

# Create figure with a simple text title
p = figure(x_range=initial_champions, height=350, title="Win Rate Comparison by Champion and Sides (Blue and Red)",
           toolbar_location=None, tools="")

# Ensure 50 is shown on the y-axis by customizing the y-axis tick marks
p.yaxis.ticker = [0, 20, 40, 50, 60, 80, 100]

# Clustered vbar plot with adjusted dodge values
width = 0.3  # Width of the bars
blue_dodge = -width / 2  # Shift blue bars to the left
red_dodge = width / 2    # Shift red bars to the right

# Blue bars
p.vbar(x=dodge('champion', blue_dodge, range=p.x_range), top='win_rate_percent', width=width,
       source=blue_source, legend_label='Blue Side', line_color='white', fill_color='#2b93b6')

# Red bars
p.vbar(x=dodge('champion', red_dodge, range=p.x_range), top='win_rate_percent', width=width,
       source=red_source, legend_label='Red Side', line_color='white', fill_color='#e54635')

# Add hover tool
hover = HoverTool(tooltips=[("Win Rate", "@win_rate_percent%"), ("Number of Games", "@n_games")])
p.add_tools(hover)

# Adjust y-axis to show from 0 to 100%
p.y_range.start = 0
p.y_range.end = 100
p.yaxis.axis_label = "Win Rate (%)"
p.xgrid.grid_line_color = None

# Add a dashed line at 50% to show the midpoint
midline = Span(location=50, dimension='width', line_color='black', line_dash='dashed', line_width=2)
p.add_layout(midline)

# Add labels for win rate difference, positioned above the bars
labels = LabelSet(x='champion', y=blue_data['win_rate_percent'].max() + 5, text='win_rate_diff',
                  source=label_source, text_align='center', text_font_size="10pt")

p.add_layout(labels)

# Set legend properties
p.legend.orientation = "horizontal"
p.legend.location = "top_center"

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
