from bokeh.models import ColumnDataSource, Select
from bokeh.plotting import figure
from bokeh.layouts import column
import pandas as pd

print("[Enemy Matchups] Enemy Matchups Panel Loaded.")

class EnemyMatchupsPanel:
    def __init__(self, global_settings, cleaned_data):
        self.global_settings = global_settings
        self.cleaned_data = cleaned_data
        self.enemy_role_map = {
            "TOP": "enemy_1",
            "JUNGLE": "enemy_2",
            "MID": "enemy_3",
            "ADC": "enemy_4",
            "SUP": "enemy_5",
            "ANY": None,
        }
        self.source = ColumnDataSource(data=dict(enemy_champion=[], win_rate_percent=[], n_games=[], color=[]))
        self.local_settings = {
            "selected_enemy_role": Select(title="Select Enemy Role:", options=list(self.enemy_role_map.keys()), value="ANY"),
        }
        self.figure = self.create_figure()

    def create_figure(self):
        fig = figure(
            title="Enemy Matchups",
            x_axis_label="Enemy Champion",
            y_axis_label="Win Rate (%)",
            height=400,
            width=600,
        )
        fig.vbar(x="enemy_champion", top="win_rate_percent", source=self.source, width=0.5, color="color")
        return fig

    def update(self):
        champion = self.global_settings["champion"].value
        role = self.local_settings["selected_enemy_role"].value

        filtered_df = self.cleaned_data[self.cleaned_data["champion"] == champion]
        if role == "ANY":
            combined = pd.concat([filtered_df[["win", col]].rename(columns={col: "enemy_champion"}) for col in self.enemy_role_map.values() if col])
        else:
            combined = filtered_df[["win", self.enemy_role_map[role]]].rename(columns={self.enemy_role_map[role]: "enemy_champion"})

        print(filtered_df)

        win_rates = combined.groupby("enemy_champion")["win"].agg(["mean", "size"]).reset_index()
        win_rates.columns = ["enemy_champion", "win_rate", "n_games"]
        win_rates["win_rate_percent"] = (win_rates["win_rate"] * 100).round(2)
        win_rates["color"] = win_rates["win_rate_percent"].apply(lambda x: "#2b93b6" if x >= filtered_df["win"].mean() * 100 else "#e54635")
        self.source.data = win_rates.to_dict("list")

    def layout(self):
        return column([self.local_settings["selected_enemy_role"], self.figure])
