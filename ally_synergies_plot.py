import pandas as pd
from bokeh.plotting import figure, curdoc
from bokeh.models import ColumnDataSource, HoverTool, MultiSelect, Select
from bokeh.layouts import column

# Load data
columns_to_load = ["champion", "lane", "win", "ally_1", "ally_2", "ally_3", "ally_4", "ally_5"]
df = pd.read_csv("cleaned_data.csv", usecols=columns_to_load)

# Filter relevant roles for analysis (JUNGLE and SUP)
df['win'] = df['win'].astype(bool)  # Ensure 'win' column is boolean

# Define initial variables
role_column_map = {"Jungler": "ally_2", "Support": "ally_5"}  # Mapping of roles to ally columns
initial_role = "Jungler"
ally_column = role_column_map[initial_role]

# Calculate win rates for each ally in the selected role
def calculate_win_rates(role):
    ally_column = role_column_map[role]
    win_rates = df.groupby([ally_column])['win'].mean().reset_index()
    win_rates.columns = ['ally_champion', 'win_rate']
    win_rates['win_rate_percent'] = (win_rates['win_rate'] * 100).round(2)
    win_rates['n_games'] = df.groupby([ally_column])['win'].size().values
    return win_rates.sort_values(by="win_rate", ascending=False)

# Initial data source for plotting
initial_win_rates = calculate_win_rates(initial_role)
source = ColumnDataSource(initial_win_rates)

# Create the figure
p = figure(x_range=initial_win_rates['ally_champion'], height=400, title=f"Win Rate with Different {initial_role}s",
           toolbar_location=None, tools="")

# Plot bars
p.vbar(x='ally_champion', top='win_rate_percent', width=0.5, source=source, line_color="white")

# Add HoverTool
hover = HoverTool(tooltips=[("Win Rate", "@win_rate_percent%"), ("Games Played", "@n_games")])
p.add_tools(hover)

# Set y-axis properties
p.y_range.start = 0
p.y_range.end = 100
p.yaxis.axis_label = "Win Rate (%)"
p.xgrid.grid_line_color = None

# MultiSelect for selecting specific ally champions
ally_select = MultiSelect(title="Select Teammates:", value=initial_win_rates['ally_champion'].tolist()[:5],
                          options=initial_win_rates['ally_champion'].tolist())

# Role selection dropdown
role_select = Select(title="Select Role:", value=initial_role, options=list(role_column_map.keys()))

# Update plot based on selected role and teammates
def update_plot(attr, old, new):
    selected_role = role_select.value
    ally_column = role_column_map[selected_role]
    selected_win_rates = calculate_win_rates(selected_role)
    
    # Filter for selected allies if any selected
    selected_allies = ally_select.value
    filtered_data = selected_win_rates[selected_win_rates['ally_champion'].isin(selected_allies)]
    
    # Update data source and x_range factors
    source.data = ColumnDataSource.from_df(filtered_data)
    p.x_range.factors = filtered_data['ally_champion'].tolist()
    p.title.text = f"Win Rate with Different {selected_role}s"

# Attach callback to both selectors
role_select.on_change('value', update_plot)
ally_select.on_change('value', update_plot)

# Layout setup
layout = column(role_select, ally_select, p)

# Add layout to document
curdoc().add_root(layout)