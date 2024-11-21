from bokeh.layouts import row
from bokeh.io import curdoc

# Import the layouts from the two scripts
from winrate_based_on_enemy_team import layout as winrate_layout
from ally_synergies_plot import layout as synergies_layout

# Combine the two layouts in a side-by-side arrangement
combined_layout = row(winrate_layout, synergies_layout)

# Add the combined layout to the Bokeh document
curdoc().add_root(combined_layout)



