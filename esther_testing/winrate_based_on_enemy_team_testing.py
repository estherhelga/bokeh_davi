import pandas as pd
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, HoverTool, TextInput, Select, Span

# Load data
file_path = 'cleaned_data.csv'
df = pd.read_csv(file_path)
df['win'] = df['win'].astype(bool)

enemy_role_map = {
    "TOP": "enemy_1",
    "JUNGLE": "enemy_2",
    "MIDDLE": "enemy_3",
    "BOTTOM": "enemy_4",
    "SUPPORT": "enemy_5",
    "ANY": None
}

# Shared variables
min_games_input = TextInput(title="Minimum Games Threshold:", value="10")

# Function to calculate win rates
def calculate_win_rates(champion, role, min_games):
    champion_df = df[(df['champion'] == champion) & (df['team_position'] == role)]
    avg_win_rate = champion_df['win'].mean() * 100

    combined_df = pd.concat([
        champion_df[['win', 'enemy_1']].rename(columns={'enemy_1': 'enemy_champion'}),
        champion_df[['win', 'enemy_2']].rename(columns={'enemy_2': 'enemy_champion'}),
        champion_df[['win', 'enemy_3']].rename(columns={'enemy_3': 'enemy_champion'}),
        champion_df[['win', 'enemy_4']].rename(columns={'enemy_4': 'enemy_champion'}),
        champion_df[['win', 'enemy_5']].rename(columns={'enemy_5': 'enemy_champion'})
    ])

    win_rates = (
        combined_df.groupby('enemy_champion')['win']
        .agg(['mean', 'size'])
        .reset_index()
    )
    win_rates.columns = ['enemy_champion', 'win_rate', 'n_games']
    win_rates['win_rate_percent'] = (win_rates['win_rate'] * 100).round(2)
    win_rates = win_rates[win_rates['n_games'] >= min_games]
    return win_rates.sort_values(by="win_rate", ascending=False), avg_win_rate

# Initialize plot
source = ColumnDataSource(data=dict(enemy_champion=[], win_rate_percent=[], n_games=[]))
p = figure(x_range=[], height=400, title="Win Rate Against Enemies", toolbar_location=None, tools="")
p.vbar(x='enemy_champion', top='win_rate_percent', width=0.5, source=source, line_color="white", fill_color='#2b93b6')
p.add_tools(HoverTool(tooltips=[("Win Rate", "@win_rate_percent%"), ("Games Played", "@n_games")]))
p.y_range.start = 0
p.y_range.end = 100
p.yaxis.axis_label = "Win Rate (%)"
p.xaxis.major_label_orientation = 0.785

avg_win_rate_line = Span(location=0, dimension='width', line_color='black', line_dash='dashed', line_width=2)
p.add_layout(avg_win_rate_line)

# Update function
def update_plot(champion, role):
    min_games = int(min_games_input.value) if min_games_input.value.isdigit() else 10
    updated_win_rates, avg_win_rate = calculate_win_rates(champion, role, min_games)
    source.data = ColumnDataSource.from_df(updated_win_rates)
    p.x_range.factors = list(updated_win_rates['enemy_champion'])
    p.title.text = f"Win Rate Against Enemies as {champion} ({role})"
    avg_win_rate_line.location = avg_win_rate

# Final layout
layout = p



