import pandas as pd

# Load the cleaned data
df = pd.read_csv('cleaned_data.csv')

# Count the occurrences of each opponent in 'lane_opponent'
opponent_counts = df['lane_opponent'].value_counts()

# Filter the dataset to keep only rows where 'lane_opponent' appears 20 or more times
df_filtered = df[df['lane_opponent'].isin(opponent_counts[opponent_counts >= 20].index)]

# Save the newly filtered dataset to a new CSV file
df_filtered.to_csv('scatterplot_filtered_data.csv', index=False)

print("Filtered dataset saved as 'scatterplot_filtered_data.csv'")

print(opponent_counts)
print(opponent_counts[opponent_counts < 20])
print(f"Number of opponents with fewer than 20 games: {len(opponent_counts[opponent_counts < 20])}")


print(f"Original dataset size: {len(df)}")
print(f"Filtered dataset size: {len(df_filtered)}")
