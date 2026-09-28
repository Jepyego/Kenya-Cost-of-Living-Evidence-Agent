from pathlib import Path
import pandas as pd

data_folder = Path(__file__).resolve().parents[1] / "data"
source = data_folder / "Monthly-Prices-of-Selected-Commodities.xlsx"

df = pd.read_excel(source)

# County is blank in every row.
df = df.drop(columns="County")
df["Commodities"] = df["Commodities"].astype(str).str.strip()
df["Price measurement"] = df["Price measurement"].astype(str).str.strip()

prices = df.melt(
    id_vars=["Commodities", "Price measurement"],
    var_name="date",
    value_name="price_kes"
)

prices = prices.rename(columns={
    "Commodities": "commodity",
    "Price measurement": "unit"
})
prices["date"] = pd.to_datetime(prices["date"], errors="coerce")
prices["price_kes"] = pd.to_numeric(prices["price_kes"], errors="coerce")
prices = prices.sort_values(["commodity", "date"]).reset_index(drop=True)

print(f"Rows after reshaping: {len(prices):,}")
print(f"Commodities: {prices['commodity'].nunique()}")
print(f"Months: {prices['date'].nunique()}")
print(f"Missing dates: {prices['date'].isna().sum()}")
print(f"Missing prices: {prices['price_kes'].isna().sum()}")
print(f"Repeated commodity/date pairs: "
      f"{prices.duplicated(['commodity', 'date']).sum()}")

output = data_folder / "commodity_prices_clean.csv"
prices.to_csv(output, index=False)
print(f"Saved to: {output}")