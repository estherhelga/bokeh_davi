import pandas as pd

# Load the dataset
file_path = 'cleaned_data.csv'  # Replace with the path to your actual dataset
data = pd.read_csv(file_path)

# Select the relevant columns
filtered_data = data[['champion', 'lane_opponent', 'game_version', 'win']].copy()  # Explicitly create a copy

# Function to properly format the patch numbers
def correct_patch_format(patch):
    parts = str(patch).split(".")
    # If the second part exists and is a single digit, we pad it with a zero (14.2 -> 14.02)
    if len(parts) > 1 and len(parts[1]) == 1:
        return f"{parts[0]}.0{parts[1]}"
    return patch

# Apply the patch formatting function to ensure 14.2 becomes 14.02 but 14.20 remains as is
filtered_data['game_version'] = filtered_data['game_version'].apply(correct_patch_format)

# Ensure 'game_version' is treated as numeric after formatting
filtered_data['game_version'] = pd.to_numeric(filtered_data['game_version'], errors='coerce')

# Filter for game versions starting with 14.x (numerical filtering)
filtered_data = filtered_data[(filtered_data['game_version'] >= 14.0) & (filtered_data['game_version'] < 15.0)]

# Inspect the patch versions: Print the lowest patch version and counts for each patch
patch_summary = filtered_data.groupby('game_version').size().reset_index(name='game_count')

# Print the patch version summary
print("Patch Version Summary:")
print(patch_summary)

# Print the lowest patch version
print("\nLowest Patch Version:", patch_summary['game_version'].min())

# Group the data by champion, game version, and lane opponent, then count wins and losses
grouped_data = filtered_data.groupby(['champion', 'game_version', 'lane_opponent', 'win']).size().unstack(fill_value=0).reset_index()

# Rename the columns for better understanding
grouped_data.columns = ['champion', 'game_version', 'lane_opponent', 'losses', 'wins']

# Save the filtered and grouped data to a new CSV file
output_file_path = 'filtered_patch_data.csv'  # Choose the desired file path
grouped_data.to_csv(output_file_path, index=False)

print(f"Filtered data has been saved to {output_file_path}")



