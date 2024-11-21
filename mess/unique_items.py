import pandas as pd

# Load the data
file_path = 'cleaned_data.csv'  # Replace with your actual file path
output_file = 'unique_items.txt'  # Output file to save the results
data = pd.read_csv(file_path)

# Ensure item columns are strings
item_columns = ['item0', 'item1', 'item2', 'item3', 'item4', 'item5', 'item6']
for col in item_columns:
    data[col] = data[col].astype(str)

# Extract unique values from all item columns
unique_items = pd.concat([data[col] for col in item_columns]).unique()

# Exclude the '0' value (empty slots)
unique_items = [item for item in unique_items if item != '0']

# Sort the unique items
unique_items = sorted(unique_items)

# Save the unique items to a text file
with open(output_file, 'w') as f:
    f.write(f"Unique Items ({len(unique_items)} total):\n")
    for item in unique_items:
        f.write(f"{item}\n")

print(f"Unique items saved to {output_file}")
