import pandas as pd
from sklearn.preprocessing import MinMaxScaler

# Load data
data = pd.read_csv("cleaned_data.csv")

# Step 1: Extract relevant columns
columns_to_extract = [
    "champion", "enemy_1", "lane_minions_first_10_minutes",
    "max_cs_advantage_on_lane_opponent", "max_level_lead_lane_opponent",
    "turret_plates_taken", "solo_kills", "deaths", "win", "team_position"
]
extracted_data = data[columns_to_extract]

# Step 2: Add Role Column for Opponents
# The role of the opponent is the same as the player's role for a specific game
extracted_data.rename(columns={"team_position": "role"}, inplace=True)

# Step 3: Aggregate by Opponent
# Count the number of games (n_games) and wins (n_wins), and calculate winrate
aggregated_counts = extracted_data.groupby(["champion", "enemy_1", "role"]).agg(
    n_games=("win", "count"),
    n_wins=("win", "sum")
).reset_index()
aggregated_counts["winrate"] = aggregated_counts["n_wins"] / aggregated_counts["n_games"]

# Calculate mean values for performance metrics
metrics = [
    "lane_minions_first_10_minutes", "max_cs_advantage_on_lane_opponent",
    "max_level_lead_lane_opponent", "turret_plates_taken", "solo_kills", "deaths"
]
aggregated_metrics = extracted_data.groupby(["champion", "enemy_1", "role"])[metrics].mean().reset_index()

# Merge aggregated counts with metrics
aggregated_data = pd.merge(aggregated_counts, aggregated_metrics, on=["champion", "enemy_1", "role"])

# Step 4: Calculate Overall Averages per Champion
# Overall averages across all matchups for each champion
overall_averages = extracted_data.groupby("champion").agg(
    overall_n_games=("win", "count"),
    overall_n_wins=("win", "sum"),
    **{f"overall_avg_{metric}": (metric, "mean") for metric in metrics}
).reset_index()

# Add overall winrate
overall_averages["overall_winrate"] = overall_averages["overall_n_wins"] / overall_averages["overall_n_games"]

# Merge overall averages with aggregated data
aggregated_data = pd.merge(aggregated_data, overall_averages, on="champion")

# Step 5: Normalize metrics per champion
def normalize_group(group):
    scaler = MinMaxScaler()
    normalized = scaler.fit_transform(group[metrics])
    normalized_df = pd.DataFrame(
        normalized, columns=[f"normalized_{metric}" for metric in metrics]
    )
    return pd.concat([group.reset_index(drop=True), normalized_df], axis=1)

# Apply normalization for each champion group
final_data = aggregated_data.groupby("champion").apply(normalize_group).reset_index(drop=True)

# Reverse normalization for deaths
final_data["normalized_deaths"] = 1 - final_data["normalized_deaths"]

# Rename enemy_1 column to lane_opponent
final_data.rename(columns={"enemy_1": "lane_opponent"}, inplace=True)

# Step 6: Save to CSV
final_data.to_csv("heatmap_data.csv", index=False)
print("Processed data saved to heatmap_data.csv")
