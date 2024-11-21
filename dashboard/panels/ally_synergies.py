from bokeh.models import ColumnDataSource, Select, Slider
from bokeh.plotting import figure
from bokeh.layouts import column
import pandas as pd

print("[Ally Synergies] Ally Synergies Panel Loaded.")

class AllySynergiesPanel:
    def __init__(self, global_settings, cleaned_data):
        self.global_settings = global_settings
        self.cleaned_data = cleaned_data
        self.role_column_map = {
            "TOP": ["ally_2", "ally_3", "ally_4", "ally_5"],
            "JUNGLE": ["ally_1", "ally_3", "ally_4", "ally_5"],
            "MID": ["ally_1", "ally_2", "ally_4", "ally_5"],
            "ADC": ["ally_1", "ally_2", "ally_3", "ally_5"],
            "SUP": ["ally_1", "ally_2", "ally_3", "ally_4"],
        }
        self.source = ColumnDataSource(data=dict(ally_champion=[], win_rate_percent=[], n_games=[], color=[]))
        self.local_settings = {
            "selected_ally_role": Select(title="Select Ally Role:", options=list(self.role_column_map.keys()), value="JUNGLE"),
            "min_games": Slider(title="Minimum Games", start=10, end=100, step=10, value=30),
        }
        self.figure = self.create_figure()

    def create_figure(self):
        print(self.source.data)
        fig = figure(
            title="Ally Synergies",
            x_axis_label="Ally Champion",
            y_axis_label="Win Rate (%)",
            height=400,
            width=600,
        )
        fig.vbar(x="ally_champion", top="win_rate_percent", source=self.source, width=0.5, color="color")
        return fig

    def update(self):
        champion = self.global_settings["champion"].value
        role = self.global_settings["role"].value
        ally_role = self.local_settings["selected_ally_role"].value
        min_games = self.local_settings["min_games"].value

        filtered_df = self.cleaned_data[(self.cleaned_data["champion"] == champion) & (self.cleaned_data["team_position"] == role)]
        ally_column = f"ally_{list(self.role_column_map.keys()).index(ally_role) + 1}"
        if ally_column not in filtered_df.columns:
            self.source.data = {"ally_champion": [], "win_rate_percent": [], "n_games": [], "color": []}
            return

        print(filtered_df)

        ally_win_rates = filtered_df.groupby(ally_column)["win"].agg(["mean", "size"]).reset_index()
        ally_win_rates.columns = ["ally_champion", "win_rate", "n_games"]
        ally_win_rates["win_rate_percent"] = (ally_win_rates["win_rate"] * 100).round(2)
        ally_win_rates = ally_win_rates[ally_win_rates["n_games"] >= min_games]

        avg_win_rate = filtered_df["win"].mean() * 100
        ally_win_rates["color"] = ally_win_rates["win_rate_percent"].apply(lambda x: "#2b93b6" if x >= avg_win_rate else "#e54635")
        self.source.data = ally_win_rates.to_dict("list")

    def layout(self):
        return column([self.local_settings["selected_ally_role"], self.local_settings["min_games"], self.figure])
