import pandas as pd
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, HoverTool, Select, Slider, Span

# Load data
file_path = 'cleaned_data.csv'
df = pd.read_csv(file_path)
df['win'] = df['win'].astype(bool)

# Shared variables
min_games_slider = Slider(title="Minimum Games", value=30, start=10, end=100, step=10)

# Function to calculate win rates
def calculate_win_rates(champion, role, min_games):
    filtered_df = df[(df['champion'] == champion) & (df['team_position'] == role)]
    ally_columns = ['ally_1', 'ally_2', 'ally_3', 'ally_4', 'ally_5']
    ally_win_rates = pd.concat(
        [filtered_df.groupby(col)['win'].agg(['mean', 'size']).reset_index() for col in ally_columns]
    )
    ally_win_rates.columns = ['ally_champion', 'win_rate', 'n_games']
    ally_win_rates['win_rate_percent'] = (ally_win_rates['win_rate'] * 100).round(2)
    ally_win_rates = ally_win_rates[ally_win_rates['n_games'] >= min_games]
    return ally_win_rates.sort_values(by="win_rate", ascending=False)

# Initialize plot
source = ColumnDataSource(data=dict(ally_champion=[], win_rate_percent=[], n_games=[]))
p = figure(x_range=[], height=400, title="Win Rate with Allies", toolbar_location=None, tools="")
p.vbar(x='ally_champion', top='win_rate_percent', width=0.5, source=source, line_color="white", fill_color='#2b93b6')
p.add_tools(HoverTool(tooltips=[("Win Rate", "@win_rate_percent%"), ("Games Played", "@n_games")]))
p.y_range.start = 0
p.y_range.end = 100
p.yaxis.axis_label = "Win Rate (%)"
p.xaxis.major_label_orientation = 0.785

midline = Span(location=0, dimension='width', line_color='black', line_dash='dashed', line_width=2)
p.add_layout(midline)

# Update function
def update_plot(champion, role):
    min_games = min_games_slider.value
    updated_win_rates = calculate_win_rates(champion, role, min_games)
    source.data = ColumnDataSource.from_df(updated_win_rates)
    p.x_range.factors = list(updated_win_rates['ally_champion'])
    p.title.text = f"Win Rate with Allies as {champion} ({role})"

# Final layout
layout = p





