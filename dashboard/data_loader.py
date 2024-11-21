import pandas as pd

class DataLoader:
    def __init__(self):
        self.cleaned_data = self.load_cleaned_data()
        self.items_data = self.load_items_data()

    def load_cleaned_data(self):
        """Load cleaned_data.csv."""
        try:
            data = pd.read_csv("data/cleaned_data.csv")  # Adjusted path
            print(f"Cleaned Data Loaded: {data.head()}")
            return data
        except FileNotFoundError:
            raise Exception("cleaned_data.csv not found in the 'data/' folder!")


    def load_items_data(self):
        """Load items.csv."""
        try:
            return pd.read_csv("data/items.csv")  # Adjusted path
        except FileNotFoundError:
            return pd.DataFrame()  # Return empty if items.csv is missing

    def get_unique_champions(self):
        """Get unique champion names from cleaned_data."""
        if self.cleaned_data is not None and "champion" in self.cleaned_data.columns:
            return sorted(self.cleaned_data["champion"].unique().tolist())
        return []
    
    def get_roles(self):
        """Return available roles with 'ANY' included."""
        roles = ["ANY", "TOP", "JUNGLE", "MID", "ADC", "SUP"]
        return roles
