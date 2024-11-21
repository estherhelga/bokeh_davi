from bokeh.layouts import column, row
from bokeh.io import curdoc
from data_loader import DataLoader
from panels.global_settings import GlobalSettings
from panels.ally_synergies import AllySynergiesPanel
from panels.enemy_matchups import EnemyMatchupsPanel

# Load shared data
data_loader = DataLoader()

print(data_loader.cleaned_data)
print(data_loader.items_data)
print(data_loader.get_unique_champions())
print(data_loader.get_roles())

# Initialize global settings
global_settings = GlobalSettings(data_loader)

print(global_settings.global_settings)

# Initialize panels
ally_synergies = AllySynergiesPanel(global_settings.global_settings, data_loader.cleaned_data)
enemy_matchups = EnemyMatchupsPanel(global_settings.global_settings, data_loader.cleaned_data)

print(ally_synergies.local_settings)
print(enemy_matchups.local_settings)
print(ally_synergies.cleaned_data)
print(enemy_matchups.cleaned_data)

# Combine layouts
dashboard_layout = column(
    *global_settings.layout(),
    row(ally_synergies.layout(), enemy_matchups.layout())
)

# Add update callbacks
def update_all(attr, old, new):
    ally_synergies.update()
    enemy_matchups.update()

for setting in global_settings.global_settings.values():
    setting.on_change("value", update_all)

# Attach layout to document
curdoc().add_root(dashboard_layout)
curdoc().title = "LoL Dashboard"
