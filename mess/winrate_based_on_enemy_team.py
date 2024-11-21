import pandas as pd
from bokeh.plotting import figure, curdoc
from bokeh.models import ColumnDataSource, HoverTool, Select, TextInput, Span, Legend, LegendItem
from bokeh.layouts import column

# Load data
file_path = 'cleaned_data.csv'  # Ensure this file path is correct if saved locally
df = pd.read_csv(file_path)

# Ensure 'win' column is boolean
df['win'] = df['win'].astype(bool)

# Define enemy role mapping, with 'ANY' to represent all enemy columns
enemy_role_map = {
    "TOP": "enemy_1",
    "JUNGLE": "enemy_2",
    "MIDDLE": "enemy_3",
    "BOTTOM": "enemy_4",
    "SUPPORT": "enemy_5",
    "ANY": None  # Use None to represent any role, which will consider all enemy columns
}

# Initial values for dropdowns and minimum games threshold
initial_champion = df['champion'].unique()[0]
initial_enemy_role = "TOP"
initial_min_games = 10

# Function to calculate win rates against specific enemies in a role
def calculate_win_rates(champion, enemy_role, min_games, selected_enemy=None):
    # Filter data for the selected champion
    champion_df = df[df['champion'] == champion]
    
    # Calculate the average win rate for the chosen champion
    avg_win_rate = champion_df['win'].mean() * 100  # Convert to percentage
    
    if enemy_role == "ANY":
        # Combine all enemy columns into a single column for "ANY" role
        combined_df = pd.concat([
            champion_df[['win', 'enemy_1']].rename(columns={'enemy_1': 'enemy_champion'}),
            champion_df[['win', 'enemy_2']].rename(columns={'enemy_2': 'enemy_champion'}),
            champion_df[['win', 'enemy_3']].rename(columns={'enemy_3': 'enemy_champion'}),
            champion_df[['win', 'enemy_4']].rename(columns={'enemy_4': 'enemy_champion'}),
            champion_df[['win', 'enemy_5']].rename(columns={'enemy_5': 'enemy_champion'})
        ])
    else:
        # Use the specified enemy role column
        enemy_column = enemy_role_map[enemy_role]
        combined_df = champion_df[['win', enemy_column]].rename(columns={enemy_column: 'enemy_champion'})
    
    # Group by the enemy champion, calculate win rate and count games
    win_rates = (
        combined_df.groupby('enemy_champion')['win']
        .agg(['mean', 'size'])  # Calculate mean win rate and number of games
        .reset_index()
    )
    win_rates.columns = ['enemy_champion', 'win_rate', 'n_games']
    win_rates['win_rate_percent'] = (win_rates['win_rate'] * 100).round(2)
    
    # Filter based on the minimum games threshold
    win_rates = win_rates[win_rates['n_games'] >= min_games]
    
    # Sort by win rate and select top 5 highest and bottom 5 lowest
    win_rates_sorted = win_rates.sort_values(by="win_rate", ascending=False)
    top_5_best = win_rates_sorted.head(5)
    top_5_worst = win_rates_sorted.tail(5)
    
    # Combine results and add color for visualization
    combined = pd.concat([top_5_best, top_5_worst])
    combined['color'] = ['#2b93b6'] * len(top_5_best) + ['#e54635'] * len(top_5_worst)
    
    # If a specific enemy champion is selected for comparison, add it to the DataFrame
    if selected_enemy and selected_enemy in win_rates['enemy_champion'].values:
        selected_enemy_row = win_rates[win_rates['enemy_champion'] == selected_enemy].copy()
        selected_enemy_row['color'] = '#d3d3d3'  # Light grey for comparison champion
        combined = pd.concat([combined, selected_enemy_row]).drop_duplicates(subset=['enemy_champion'])
    
    # Sort again to keep the chosen enemy in its correct position by win rate
    combined = combined.sort_values(by="win_rate", ascending=False).reset_index(drop=True)
    
    return combined, avg_win_rate

# Calculate initial win rates and average win rate
initial_win_rates, initial_avg_win_rate = calculate_win_rates(initial_champion, initial_enemy_role, initial_min_games)
source = ColumnDataSource(initial_win_rates)

# Create Bokeh figure
p = figure(x_range=list(initial_win_rates['enemy_champion']), height=400,
           title=f"Win Rate Against {initial_enemy_role} Enemies as {initial_champion}",
           toolbar_location=None, tools="")

# Add bars to the plot
bars = p.vbar(x='enemy_champion', top='win_rate_percent', width=0.5, source=source, line_color="white", fill_color='color')

# Add HoverTool
hover = HoverTool(tooltips=[("Win Rate", "@win_rate_percent%"), ("Games Played", "@n_games")])
p.add_tools(hover)

# Set y-axis properties
p.y_range.start = 0
p.y_range.end = 100
p.yaxis.axis_label = "Win Rate (%)"

# Rotate x-axis labels for clarity
p.xaxis.major_label_orientation = 0.785  # 45 degrees

# Add dashed line for the average win rate
avg_win_rate_line = Span(location=initial_avg_win_rate, dimension='width', line_color='black',
                         line_dash='dashed', line_width=2)
p.add_layout(avg_win_rate_line)

# Add invisible glyphs for legend entries
above_avg_glyph = p.vbar(x=[0], top=[1], fill_color='#2b93b6', line_color='white', width=0.1, visible=False)
below_avg_glyph = p.vbar(x=[0], top=[1], fill_color='#e54635', line_color='white', width=0.1, visible=False)
comparison_glyph = p.vbar(x=[0], top=[1], fill_color='#d3d3d3', line_color='white', width=0.1, visible=False)
avg_line_glyph = p.line(x=[0, 1], y=[initial_avg_win_rate, initial_avg_win_rate], 
                        line_color="black", line_dash="dashed", line_width=2, visible=False)

# Add legend
legend_items = [
    LegendItem(label="Top 5 Best Matchups", renderers=[above_avg_glyph]),
    LegendItem(label="Bottom 5 Worst Matchups", renderers=[below_avg_glyph]),
    LegendItem(label="Selected Enemy Champion", renderers=[comparison_glyph]),
    LegendItem(label="Average Win Rate", renderers=[avg_line_glyph])
]
legend = Legend(items=legend_items, location="top_right", label_text_font_size="10pt")
legend.background_fill_alpha = 0  # Make the legend background transparent
p.add_layout(legend)

# Selection Widgets
champion_select = Select(title="Select Your Champion:", value=initial_champion,
                         options=sorted(df['champion'].unique().tolist()))
enemy_role_select = Select(title="Select Enemy Role:", value=initial_enemy_role, options=list(enemy_role_map.keys()))
min_games_input = TextInput(title="Minimum Games Threshold:", value=str(initial_min_games))
enemy_champion_select = Select(title="Compare Against Specific Enemy Champion:", options=[])

# Update options for the enemy champion based on the selected role
def update_enemy_champion_options(attr, old, new):
    selected_enemy_role = enemy_role_select.value
    if selected_enemy_role == "ANY":
        unique_enemies = pd.concat([
            df["enemy_1"], df["enemy_2"], df["enemy_3"], df["enemy_4"], df["enemy_5"]
        ]).unique().tolist()
    else:
        enemy_column = enemy_role_map[selected_enemy_role]
        unique_enemies = df[enemy_column].unique().tolist()
    enemy_champion_select.options = sorted(unique_enemies)

# Initial population of enemy champion options
update_enemy_champion_options(None, None, None)

# Update plot based on selected champion, enemy role, minimum games, and chosen enemy champion
def update_plot(attr, old, new):
    selected_champion = champion_select.value
    selected_enemy_role = enemy_role_select.value
    min_games = int(min_games_input.value) if min_games_input.value.isdigit() else initial_min_games
    chosen_enemy = enemy_champion_select.value if enemy_champion_select.value else None
    updated_win_rates, avg_win_rate = calculate_win_rates(selected_champion, selected_enemy_role, min_games, chosen_enemy)
    
    # Update data source and x_range factors
    source.data = ColumnDataSource.from_df(updated_win_rates)
    p.x_range.factors = list(updated_win_rates['enemy_champion'])
    p.title.text = f"Win Rate Against {selected_enemy_role} Enemies as {selected_champion}"
    
    # Update the dashed line for the average win rate
    avg_win_rate_line.location = avg_win_rate

# Attach callback to selectors and text input
champion_select.on_change('value', update_plot)
enemy_role_select.on_change('value', update_plot)
enemy_role_select.on_change('value', update_enemy_champion_options)
min_games_input.on_change('value', update_plot)
enemy_champion_select.on_change('value', update_plot)

# Layout and display
layout = column(champion_select, enemy_role_select, min_games_input, enemy_champion_select, p)
#curdoc().add_root(layout)
