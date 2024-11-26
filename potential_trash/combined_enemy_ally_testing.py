import pandas as pd
from bokeh.layouts import column, row
from bokeh.io import curdoc
from bokeh.models import Select

# Load data
file_path = 'cleaned_data.csv'
df = pd.read_csv(file_path)
champions = sorted(df['champion'].unique().tolist())
roles = sorted(df['team_position'].unique().tolist())

# Shared widgets
champion_select = Select(title="Select Your Champion:", value=champions[0], options=champions)
role_select = Select(title="Select Your Role:", value=roles[0], options=roles)

# Import the layouts and update functions from the two scripts
from winrate_based_on_enemy_team import layout as winrate_layout, update_plot as update_winrate_plot
from ally_synergies_plot import layout as synergies_layout, update_plot as update_synergies_plot

# Shared callback
def update_all(attr, old, new):
    selected_champion = champion_select.value
    selected_role = role_select.value
    update_winrate_plot(selected_champion, selected_role)
    update_synergies_plot(selected_champion, selected_role)

champion_select.on_change('value', update_all)
role_select.on_change('value', update_all)

# Layout
combined_layout = column(
    row(champion_select, role_select),
    row(winrate_layout, synergies_layout)
)

curdoc().add_root(combined_layout)





