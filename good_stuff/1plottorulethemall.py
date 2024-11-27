import pandas as pd
from bokeh.layouts import column, row
from bokeh.models import Select, TextInput, MultiSelect, ColumnDataSource, HoverTool, Span, Spacer
from bokeh.plotting import figure, curdoc
from bokeh.models import Button, Div

# Load the data
file_path = 'cleaned_data.csv'
df = pd.read_csv(file_path)
df['win'] = df['win'].astype(bool)

# Extract unique champions from the dataset
champions = sorted(df['champion'].unique().tolist())

# Define standard roles
roles = ['TOP', 'JUNGLE', 'MID', 'ADC', 'SUP']

# Create shared global widgets
champion_select = Select(title="Select Your Champion:", value=champions[0], options=champions)
role_select = Select(title="Select Your Role:", value=roles[0], options=roles)

# Create plot-specific widgets for the enemy plot
enemy_roles = ["ANY", "TOP", "JUNGLE", "MID", "ADC", "SUPPORT"]
enemy_role_select = Select(title="Enemy Role:", value="ANY", options=enemy_roles)
enemy_champion_select = Select(title="Compare Against Specific Enemy:", value="", options=[])
min_games_input = TextInput(title="Minimum Games Threshold:", value="50")

# Create plot-specific widgets for the ally plot
ally_role_select = Select(title="Select Ally Role:", value="JUNGLE", options=roles)
ally_min_games_input = TextInput(title="Minimum Games Threshold for Allies:", value="50")
ally_champion_select = Select(title="Select an Ally to Compare:", value="", options=[])
selected_allies = []  # Keep track of selected allies

# -------------------------------------------------------------------------------- #
# Supporting Functions                                                             #
# -------------------------------------------------------------------------------- #

def calculate_overall_win_rate(champion):
    """Calculate the overall win rate for a champion."""
    champion_df = df[df['champion'] == champion]
    if champion_df.empty:
        return 0
    return (champion_df['win'].mean() * 100).round(2)

def update_enemy_champion_options(attr, old, new):
    """Update the enemy champion options based on the selected enemy role and refresh the plot."""
    selected_role = enemy_role_select.value  # Ensure it reads the current selection

    if selected_role == "ANY":
        # Concatenate all enemy columns to find unique enemies
        unique_enemies = pd.concat([df['enemy_1'], df['enemy_2'], df['enemy_3'], df['enemy_4'], df['enemy_5']]).unique()
    else:
        # Map selected role to a specific enemy column
        role_column_map = {
            "TOP": "enemy_1",
            "JUNGLE": "enemy_2",
            "MID": "enemy_3",
            "ADC": "enemy_4",
            "SUPPORT": "enemy_5"
        }
        column = role_column_map.get(selected_role, None)
        if column:
            unique_enemies = df[column].unique()
        else:
            unique_enemies = []

    # Update the dropdown options
    enemy_champion_select.options = sorted(unique_enemies.tolist())
    enemy_champion_select.value = ""  # Reset to no specific enemy

    # Trigger the plot update after updating the dropdown
    update_winrate_plot_with_filters(attr, old, new)

def add_ally_to_selection(attr, old, new):
    """Add the selected ally to the list of selected allies."""
    global selected_allies
    if new and new not in selected_allies and len(selected_allies) < 3:
        selected_allies.append(new)  # Add to selected allies
        update_ally_synergy_plot(None, None, None)  # Update the plot
        update_ally_dropdown_options()  # Refresh the dropdown options
        ally_champion_select.value = ""  # Reset dropdown after selection

def update_ally_dropdown_options():
    """Update the dropdown to exclude already-selected allies."""
    ally_role = ally_role_select.value  # Get the selected ally role
    role_column_map = {
        "TOP": "ally_1",
        "JUNGLE": "ally_2",
        "MID": "ally_3",
        "ADC": "ally_4",
        "SUP": "ally_5",
    }
    ally_column = role_column_map.get(ally_role)
    
    # Ensure the ally column exists
    if not ally_column:
        ally_champion_select.options = []
        return

    # Get all allies in the selected role
    allies_in_role = df[ally_column].dropna().unique()

    # Exclude already-selected allies
    remaining_allies = [ally for ally in allies_in_role if ally not in selected_allies]
    ally_champion_select.options = sorted(remaining_allies)

def remove_ally_from_selection(ally):
    """Remove an ally from the selected list and update the plot."""
    global selected_allies
    if ally in selected_allies:
        selected_allies.remove(ally)
        update_ally_dropdown_options()  # Refresh dropdown options
        update_ally_synergy_plot(None, None, None)  # Update the plot


# -------------------------------------------------------------------------------- #
# Creation of the Winrate against Enemies Plot                                     #
# -------------------------------------------------------------------------------- #

# Initialize empty data source for the plot
winrate_source = ColumnDataSource(data=dict(enemy_champion=[], win_rate_percent=[], n_games=[], color=[], hatch=[]))

def create_winrate_plot():
    p = figure(x_range=[], height=400, title="Win Rate Against Enemies", toolbar_location=None, tools="")

    p.vbar(
        x='enemy_champion',
        top='win_rate_percent',
        width=0.5,
        source=winrate_source,
        line_color="white",
        fill_color='color',
        hatch_pattern='hatch',
        hatch_color="white",
        hatch_alpha=0.5,
        hatch_weight=2
    )

    hover = HoverTool(tooltips=[("Win Rate", "@win_rate_percent%"), ("Games Played", "@n_games")])
    p.add_tools(hover)

    p.y_range.start = 0
    p.y_range.end = 100
    p.yaxis.axis_label = "Win Rate (%)"
    p.xaxis.major_label_orientation = 0.785

    avg_win_rate_line = Span(location=0, dimension='width', line_color='black', line_dash='dashed', line_width=2)
    p.add_layout(avg_win_rate_line)

    return p, avg_win_rate_line

# Initialize the plot
winrate_plot, avg_win_rate_line = create_winrate_plot()

def update_winrate_plot_with_filters(attr, old, new):
    """Update the Win Rate plot based on filters."""
    global overall_avg_win_rate

    overall_avg_win_rate = calculate_overall_win_rate(champion_select.value)

    min_games = int(min_games_input.value) if min_games_input.value.isdigit() else 10
    selected_role = enemy_role_select.value
    selected_enemy = enemy_champion_select.value if enemy_champion_select.value else None

    # Filter data for the selected champion and role
    filtered_df = df[(df['champion'] == champion_select.value) & (df['team_position'] == role_select.value)]

    # Filter by selected enemy role
    if selected_role == "ANY":
        filtered_df = pd.concat([
            filtered_df[['win', 'enemy_1']].rename(columns={'enemy_1': 'enemy_champion'}),
            filtered_df[['win', 'enemy_2']].rename(columns={'enemy_2': 'enemy_champion'}),
            filtered_df[['win', 'enemy_3']].rename(columns={'enemy_3': 'enemy_champion'}),
            filtered_df[['win', 'enemy_4']].rename(columns={'enemy_4': 'enemy_champion'}),
            filtered_df[['win', 'enemy_5']].rename(columns={'enemy_5': 'enemy_champion'})
        ])
    else:
        role_column_map = {
            "TOP": "enemy_1",
            "JUNGLE": "enemy_2",
            "MID": "enemy_3",
            "ADC": "enemy_4",
            "SUPPORT": "enemy_5"
        }
        column = role_column_map.get(selected_role)
        if column:
            filtered_df = filtered_df.rename(columns={column: "enemy_champion"})

    # Calculate win rates
    win_rates = (
        filtered_df.groupby('enemy_champion')['win']
        .agg(['mean', 'size'])
        .reset_index()
    )
    win_rates.columns = ['enemy_champion', 'win_rate', 'n_games']
    win_rates['win_rate_percent'] = (win_rates['win_rate'] * 100).round(2)
    win_rates = win_rates[win_rates['n_games'] >= min_games]

    # Sort and assign colors/hatches
    win_rates_sorted = win_rates.sort_values(by="win_rate", ascending=False)
    top_5 = win_rates_sorted.head(5).copy()
    bottom_5 = win_rates_sorted.tail(5).copy()

    top_5['color'] = '#2b93b6'  # Blue for top matchups
    bottom_5['color'] = '#e54635'  # Red for bottom matchups
    top_5['hatch'] = ' '
    bottom_5['hatch'] = ' '

    # Handle specific enemy selection
    if selected_enemy and selected_enemy in win_rates['enemy_champion'].values:
        selected_enemy_row = win_rates[win_rates['enemy_champion'] == selected_enemy].copy()
        selected_enemy_row['color'] = '#2b93b6' if selected_enemy_row['win_rate_percent'].iloc[0] > overall_avg_win_rate else '#e54635'
        selected_enemy_row['hatch'] = '/'
        combined = pd.concat([top_5, bottom_5, selected_enemy_row]).drop_duplicates(subset=['enemy_champion'])
    else:
        combined = pd.concat([top_5, bottom_5])

    combined = combined.sort_values(by="win_rate", ascending=False)
    winrate_source.data = combined.to_dict(orient='list')
    winrate_plot.x_range.factors = list(combined['enemy_champion'])
    winrate_plot.title.text = f"Win Rate Against Enemies as {champion_select.value} ({role_select.value})"

    avg_win_rate_line.location = overall_avg_win_rate


# -------------------------------------------------------------------------------- #
# Creation of Ally Synergies plot                                                    #
# -------------------------------------------------------------------------------- #

# Initialize empty data source for the ally synergies plot
ally_synergy_source = ColumnDataSource(data=dict(ally_champion=[], win_rate_percent=[], n_games=[]))

def calculate_ally_synergies(champion, role, selected_allies, ally_role):
    """Calculate ally synergies considering the ally role."""
    # If no allies are selected, return an empty DataFrame
    if not selected_allies:
        return pd.DataFrame(columns=['ally_champion', 'win_rate', 'n_games', 'win_rate_percent'])

    # Filter data for the selected champion and role
    filtered_df = df[(df['champion'] == champion) & (df['team_position'] == role)]

    # Map roles to ally columns
    role_column_map = {
        "TOP": "ally_1",
        "JUNGLE": "ally_2",
        "MID": "ally_3",
        "ADC": "ally_4",
        "SUP": "ally_5",
    }
    ally_column = role_column_map.get(ally_role)  # Get the ally column for the selected role

    if not ally_column:
        return pd.DataFrame()  # Invalid ally role

    # Filter data by the selected allies and the ally role
    combined_df = filtered_df[['win', ally_column]].rename(columns={ally_column: 'ally_champion'})
    combined_df = combined_df[combined_df['ally_champion'].isin(selected_allies)]

    # Calculate win rates
    win_rates = (
        combined_df.groupby('ally_champion')['win']
        .agg(['mean', 'size'])
        .reset_index()
        .rename(columns={'mean': 'win_rate', 'size': 'n_games'})
    )
    win_rates['win_rate_percent'] = (win_rates['win_rate'] * 100).round(2)

    # Filter by minimum games
    min_games = int(ally_min_games_input.value) if ally_min_games_input.value.isdigit() else 10
    win_rates = win_rates[win_rates['n_games'] >= min_games]

    return win_rates


def update_ally_synergy_plot_on_role(attr, old, new):
    """Update the ally synergy plot based on the selected ally role."""
    ally_role = ally_role_select.value  # Get the selected ally role
    user_role = role_select.value       # Get the user's own role

    # If ally role matches the user's role, clear the plot
    if ally_role == user_role:
        ally_synergy_source.data = dict(ally_champion=[], win_rate_percent=[], n_games=[], color=[])
        ally_synergy_plot.x_range.factors = []
        ally_synergy_plot.title.text = f"No allies in the same role ({ally_role}) as {champion_select.value}"
        overall_winrate_line.location = None  # Hide the line
        return

    # Get allies for the selected ally role
    role_column_map = {
        "TOP": "ally_1",
        "JUNGLE": "ally_2",
        "MID": "ally_3",
        "ADC": "ally_4",
        "SUP": "ally_5",
    }
    ally_column = role_column_map.get(ally_role)

    if not ally_column:
        # Invalid ally role; clear the plot
        ally_synergy_source.data = dict(ally_champion=[], win_rate_percent=[], n_games=[], color=[])
        ally_synergy_plot.x_range.factors = []
        ally_synergy_plot.title.text = "Invalid role selected"
        overall_winrate_line.location = None  # Hide the line
        return

    # Filter allies in the selected role
    allies_in_role = df[ally_column].dropna().unique().tolist()

    # Use all allies in the selected role for the initial display
    ally_data = calculate_ally_synergies(
        champion=champion_select.value,
        role=user_role,
        selected_allies=allies_in_role,
        ally_role=ally_role
    )

    # Calculate overall winrate for the selected champion
    overall_winrate = calculate_overall_win_rate(champion_select.value)

    # Sort allies by win rate in descending order
    ally_data = ally_data.sort_values(by='win_rate_percent', ascending=False)

    # Assign colors to all allies
    ally_data['color'] = ally_data['win_rate_percent'].apply(
        lambda x: '#2b93b6' if x >= overall_winrate else '#e54635'
    )

    # Initialize the plot with all allies above the overall winrate
    displayed_allies = ally_data[ally_data['win_rate_percent'] >= overall_winrate]

    # If no allies meet the criteria, show the top 5 allies
    if displayed_allies.empty:
        displayed_allies = ally_data.head(5)

    # Update the plot
    ally_synergy_source.data = displayed_allies.to_dict(orient='list')
    ally_synergy_plot.x_range.factors = list(displayed_allies['ally_champion'])
    ally_synergy_plot.title.text = f"Ally Synergies for {champion_select.value} ({user_role}) with {ally_role} Allies"

    # Update the dashed line for the overall winrate
    overall_winrate_line.location = overall_winrate

def update_ally_synergy_plot(attr, old, new):
    """Update the ally synergy plot based on selected allies."""
    global selected_allies
    ally_role = ally_role_select.value  # Get selected ally role
    ally_data = calculate_ally_synergies(champion_select.value, role_select.value, selected_allies, ally_role)

    # Update the plot with new data
    ally_synergy_source.data = ally_data.to_dict(orient='list')
    ally_synergy_plot.x_range.factors = list(ally_data['ally_champion'])
    ally_synergy_plot.title.text = f"Ally Synergies for {champion_select.value} ({role_select.value}) with Selected Allies"



def create_ally_synergy_plot():
    p = figure(x_range=[], height=400, title="Ally Synergies", toolbar_location=None, tools="")

    p.vbar(
        x='ally_champion',
        top='win_rate_percent',
        width=0.5,
        source=ally_synergy_source,
        line_color="white",
        fill_color='color'  # Use the dynamic color column
    )

    hover = HoverTool(tooltips=[("Win Rate", "@win_rate_percent%"), ("Games Played", "@n_games")])
    p.add_tools(hover)

    p.y_range.start = 0
    p.y_range.end = 100
    p.yaxis.axis_label = "Win Rate (%)"
    p.xaxis.major_label_orientation = 0.785

    # Add a horizontal dashed line for the overall winrate
    overall_winrate_line = Span(
        location=0,  # This will be dynamically updated
        dimension='width',
        line_color='black',
        line_dash='dashed',
        line_width=2
    )
    p.add_layout(overall_winrate_line)

    return p, overall_winrate_line



# Initialize the ally synergies plot and line
ally_synergy_plot, overall_winrate_line = create_ally_synergy_plot()


# -------------------------------------------------------------------------------- #
# Global Settings function                                                         #
# -------------------------------------------------------------------------------- #

def create_dummy_plot(title):
    """Create a simple dummy plot as a placeholder."""
    p = figure(title=title, height=400, width=600, toolbar_location=None)
    p.xaxis.axis_label = "X-Axis"
    p.yaxis.axis_label = "Y-Axis"
    return p

# Create two dummy plots
dummy_plot_1 = create_dummy_plot("Dummy Plot 1")
dummy_plot_2 = create_dummy_plot("Dummy Plot 2")



# -------------------------------------------------------------------------------- #
# Global Settings function                                                         #
# -------------------------------------------------------------------------------- #

# Global callback for Champion and Role selections
def update_global_settings(attr, old, new):
    update_winrate_plot_with_filters(attr, old, new)
    update_ally_synergy_plot_on_role(attr, old, new)

# Attach the global callback
champion_select.on_change('value', update_global_settings)
role_select.on_change('value', update_global_settings)


# -------------------------------------------------------------------------------- #
# Layout and Initial Update                                                        #
# -------------------------------------------------------------------------------- #

spacer = Spacer(width=300, height=100)

# Layout for the enemy winrate plot with its widgets
winrate_section = column(
    row(champion_select, role_select),
    row(enemy_role_select, min_games_input, enemy_champion_select),
    winrate_plot
)

# Layout for ally synergies plot with widgets
ally_synergy_section = column(
    row(ally_role_select, ally_min_games_input),  # Widgets for Ally Role and Min Games
    ally_champion_select,  # Ally Champion widget
    ally_synergy_plot  # Only the figure (not the tuple)
)

# Create buttons and a display for selected allies
ally_buttons = []
for ally in selected_allies:
    button = Button(label=f"Remove {ally}", button_type="danger")
    button.on_click(lambda ally=ally: remove_ally_from_selection(ally))
    ally_buttons.append(button)

selected_allies_display = column(*ally_buttons)

# Create the full 2x2 grid layout

layout = column(
    row(winrate_section, spacer, ally_synergy_section),
    row(dummy_plot_1, dummy_plot_2),
    selected_allies_display
)

# Attach callbacks
champion_select.on_change('value', update_global_settings)
role_select.on_change('value', update_global_settings)
min_games_input.on_change('value', update_winrate_plot_with_filters)
enemy_role_select.on_change('value', update_enemy_champion_options)
enemy_champion_select.on_change('value', update_winrate_plot_with_filters)

ally_role_select.on_change('value', update_ally_synergy_plot_on_role)
ally_min_games_input.on_change('value', update_ally_synergy_plot)
ally_champion_select.on_change('value', add_ally_to_selection)

# Initial update
# Initial update
update_enemy_champion_options(None, None, None)
update_winrate_plot_with_filters(None, None, None)
update_ally_dropdown_options()  # Ensure dropdown options are initialized
update_ally_synergy_plot_on_role(None, None, None)  # Initialize the ally plot


# Add the layout to curdoc
curdoc().clear()  # Clear any previous layouts
curdoc().add_root(layout)