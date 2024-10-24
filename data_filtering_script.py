
import pandas as pd

# Load your dataset (replace 'your_data.csv' with your actual file path)
df = pd.read_csv(r'C:\Users\esthe\Documents\programming\uni_semester_1\davi\bokeh_davi\combined_matches.csv')

# Apply the filters
# 1. Remove rows where 'game_duration' is less than 900
df_filtered = df[df['game_duration'] >= 900]

# 2. Keep only rows where 'team_position' is 'TOP'
df_filtered = df_filtered[df_filtered['team_position'] == 'TOP']

# Save the cleaned dataset to a new CSV file
df_filtered.to_csv('cleaned_data.csv', index=False)

print("Cleaned dataset saved as 'cleaned_data.csv'")
