import pandas as pd

# Load the filtered data from CSV
file_path = 'filtered_patch_data.csv'  # Ensure this is the correct path to your CSV
data = pd.read_csv(file_path)

# Function to correctly format patch numbers (e.g., 14.2 -> 14.02)
def format_patch(patch):
    parts = str(patch).split(".")
    if len(parts) > 1 and len(parts[1]) == 1:  # If there is one digit after the dot, pad with a zero
        return f"{parts[0]}.{parts[1].zfill(2)}"
    return patch

# Apply the patch formatting
data['game_version'] = data['game_version'].apply(format_patch)

# Convert to numeric for sorting purposes after formatting
data['game_version'] = pd.to_numeric(data['game_version'], errors='coerce')

# Filter for game versions between 14.11 and 14.19 (or whatever patch range you're working with)
filtered_data = data[(data['game_version'] >= 14.11) & (data['game_version'] <= 14.19)]

# Select champion and opponent to check (Aatrox and Garen or others)
selected_champion = 'Aatrox'
selected_opponent = 'Garen'  # You can change this to any opponent you want to check

# Filter for the specific champion and opponent matchups
champion_data = filtered_data[filtered_data['champion'] == selected_champion]
opponent_data = champion_data[champion_data['lane_opponent'] == selected_opponent]

# Group by patch and calculate the total number of games (wins + losses) for each patch
game_counts = opponent_data.groupby('game_version').agg(
    wins=('wins', 'sum'), 
    losses=('losses', 'sum')
).reset_index()

# Calculate total games per patch by adding wins and losses
game_counts['total_games'] = game_counts['wins'] + game_counts['losses']

# Print out the game counts for each patch
print(f"Number of games played as {selected_champion} vs {selected_opponent} per patch:")
print(game_counts[['game_version', 'total_games']])


