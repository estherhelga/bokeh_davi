import pandas as pd
from bokeh.plotting import figure, curdoc
from bokeh.models import ColumnDataSource, HoverTool, Select, MultiChoice, Div, CDSView, GroupFilter, BooleanFilter
from bokeh.layouts import column, row
from bokeh.palettes import Category10
from bokeh.transform import factor_cmap


# Load all necessary columns (add more if needed)
columns_to_load = ["champion", "game_duration", "kills", "deaths", "assists", "total_minions_killed",
                  "lane_minions_first_10_minutes", "max_cs_advantage_on_lane_opponent",
                  "max_level_lead_lane_opponent", "lane_opponent", "game_version", "win"]
df = pd.read_csv("cleaned_data.csv", usecols=columns_to_load)



# Filter for patch 14.x  (Adapt the string matching if your data format is different)
# df = df[df['game_version'].str.startswith('14.')]

# Calculate KDA ratio (handle potential division by zero)
df['kda'] = (df['kills'] + df['assists']) / df['deaths'].replace(0, 1)

# Convert win to boolean
df['win'] = df['win'].astype(bool)

# Create ColumnDataSource
source = ColumnDataSource(df)

# Champion selection widget (unchanged)
champion_select = Select(title="Select Your Champion:", value="Aatrox", options=sorted(df['champion'].unique()))

#Opponent selection widget
opponent_options = sorted(list(df['lane_opponent'].unique()))  # Sort opponents alphabetically
opponent_dropdown = MultiChoice(value=[], options=opponent_options, title="Select Opponent Champions")
warning_div = Div(text="")  # Div to show a warning if more than 3 selections


# Create figures
p1 = figure(title="Win Rate vs. Game Duration", x_axis_label="Game Duration (seconds)", y_axis_label="Win Rate", width=450, height=300)
p2 = figure(title="Win Rate vs. KDA", x_axis_label="KDA Ratio", y_axis_label="Win Rate", width=450, height=300)
p3 = figure(title="Win Rate vs. Creep Score Advantage", x_axis_label="Creep Score Advantage at 10 Minutes", y_axis_label="Win Rate", width=450, height=300)

#HoverTools for all plots
hover1 = HoverTool(tooltips=[("Game Duration", "@game_duration seconds"),("Win", "@win")])
p1.add_tools(hover1)

hover2 = HoverTool(tooltips=[("KDA", "@kda"),("Win", "@win")])
p2.add_tools(hover2)

hover3 = HoverTool(tooltips=[("CS Advantage at 10", "@max_cs_advantage_on_lane_opponent"),("Win", "@win")])
p3.add_tools(hover3)




# Function to update plots
def update_plots(attr, old, new):
    selected_champion = champion_select.value
    selected_opponents = opponent_dropdown.value

    # Check if more than 3 opponents are selected
    if len(selected_opponents) > 3:
        warning_div.text = '<p style="color:red;">You can select a maximum of 3 opponents.</p>'
        return
    else:
        warning_div.text = ""

    # Champion filter
    champion_view = CDSView(source=source, filters=[GroupFilter(column_name='champion', group=selected_champion)])

    if selected_opponents:
        opponent_filter = BooleanFilter([x in selected_opponents for x in source.data["lane_opponent"]])
        champion_view.filters.append(opponent_filter)


    # Color mapping for opponents (up to 10 distinct colors)
    if selected_opponents:
      color_mapper = factor_cmap('lane_opponent', palette=Category10[len(selected_opponents)], factors=selected_opponents)


    # Plot 1: Win Rate vs. Game Duration (using view for filtering)
    p1.circle(x='game_duration', y='win', source=source, view=champion_view, size=8, color=color_mapper if selected_opponents else "navy", alpha=0.6)

    #Plot 2: Win rate vs KDA
    p2.circle(x='kda', y='win', source=source, view=champion_view, size=8, color=color_mapper if selected_opponents else "navy", alpha=0.6)
    
    #Plot 3: Win rate vs. Creep Score Advantage at 10
    p3.circle(x="max_cs_advantage_on_lane_opponent", y = 'win', source=source, view=champion_view, size=8, color=color_mapper if selected_opponents else "navy", alpha=0.6)




# Initial update
update_plots(None, None, None)

champion_select.on_change('value', update_plots)
opponent_dropdown.on_change("value", update_plots)


# Layout
layout = column(champion_select, opponent_dropdown, warning_div,row(p1, p2, p3))
curdoc().add_root(layout)