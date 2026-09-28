from pathlib import Path
import pandas as pd

data_folder = Path(__file__).resolve().parents[1] / "data"
file = data_folder / "Monthly-Prices-of-Selected-Commodities.xlsx"
df = pd.read_excel(file)

print(f"Rows and columns: {df.shape}")
print("\nCounty values:")
print(df["County"].fillna("(blank)").value_counts().to_string())

print("\nCommodities and measurements:")
print(df[["Commodities", "Price measurement"]].to_string(index=False))

print("\nMissing values in the first three columns:")
print(df[["County", "Commodities", "Price measurement"]].isna().sum().to_string())