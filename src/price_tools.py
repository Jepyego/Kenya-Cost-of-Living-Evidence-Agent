from pathlib import Path
import pandas as pd

DATA_FILE = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "commodity_prices_clean.csv"
)


def compare_months(start_month: str, end_month: str) -> pd.DataFrame:
    """Compare commodity prices for two months, written as YYYY-MM."""
    df = pd.read_csv(DATA_FILE, parse_dates=["date"])
    start = pd.Timestamp(start_month)
    end = pd.Timestamp(end_month)

    if start >= end:
        raise ValueError("The start month must be earlier than the end month.")

    first = df[df["date"] == start][["commodity", "unit", "price_kes"]]
    last = df[df["date"] == end][["commodity", "price_kes"]]

    result = first.merge(
        last,
        on="commodity",
        suffixes=("_start", "_end"),
        validate="one_to_one"
    )

    if result.empty:
        raise ValueError("One or both months are not in the dataset.")

    result["change_kes"] = (
        result["price_kes_end"] - result["price_kes_start"]
    )
    result["change_pct"] = (
        result["change_kes"] / result["price_kes_start"] * 100
    )

    return result.sort_values("change_pct", ascending=False)

def commodity_trend(commodity: str) -> pd.DataFrame:
    """Return all monthly prices for one commodity."""
    df = pd.read_csv(DATA_FILE, parse_dates=["date"])

    matches = df[
        df["commodity"].str.casefold() == commodity.strip().casefold()
    ][["date", "commodity", "unit", "price_kes"]]

    if matches.empty:
        available = ", ".join(sorted(df["commodity"].unique()))
        raise ValueError(
            f"Commodity not found. Available commodities: {available}"
        )

    return matches.sort_values("date").reset_index(drop=True)

if __name__ == "__main__":
    comparison = compare_months("2019-02", "2022-05")
    print(comparison.round(2).to_string(index=False))

    oil = commodity_trend("Cooking oil")
    print(f"\nCooking oil: {len(oil)} months")
    print(oil.tail(3).to_string(index=False))

def compare_with_fuel(commodity: str, fuel: str = "Petrol",
                      start_month: str | None = None,
                      end_month: str | None = None) -> tuple[pd.DataFrame, dict]:
    """Monthly price indices (first selected month = 100) and endpoint changes.

    Both series come from the same KNBS dataset; this is descriptive, not causal.
    """
    fuels = {"petrol": "Petrol", "diesel": "Diesel", "kerosene": "Kerosene"}
    fuel_name = fuels.get(fuel.strip().casefold())
    if fuel_name is None:
        raise ValueError("Fuel must be Petrol, Diesel, or Kerosene.")
    item = commodity_trend(commodity)
    if item["commodity"].iloc[0].casefold() in fuels:
        raise ValueError("Choose a non-fuel commodity to compare with fuel.")
    fuel_prices = commodity_trend(fuel_name)
    joined = item[["date", "price_kes"]].merge(
        fuel_prices[["date", "price_kes"]], on="date",
        suffixes=("_commodity", "_fuel"), validate="one_to_one"
    )
    if start_month:
        joined = joined[joined["date"] >= pd.Timestamp(start_month)]
    if end_month:
        joined = joined[joined["date"] <= pd.Timestamp(end_month)]
    joined = joined.sort_values("date").reset_index(drop=True)
    if len(joined) < 2:
        raise ValueError("Select at least two shared months in the dataset.")
    start_values = joined.iloc[0]
    end_values = joined.iloc[-1]
    item_name = item["commodity"].iloc[0]
    indices = pd.DataFrame({
        "date": joined["date"],
        item_name: joined["price_kes_commodity"] / start_values["price_kes_commodity"] * 100,
        fuel_name: joined["price_kes_fuel"] / start_values["price_kes_fuel"] * 100,
    })
    summary = {
        "commodity": item_name, "fuel": fuel_name,
        "start": start_values["date"].strftime("%Y-%m"),
        "end": end_values["date"].strftime("%Y-%m"),
        "commodity_change_pct": (end_values["price_kes_commodity"] / start_values["price_kes_commodity"] - 1) * 100,
        "fuel_change_pct": (end_values["price_kes_fuel"] / start_values["price_kes_fuel"] - 1) * 100,
        "months": len(joined),
    }
    return indices, summary

FX_FILE = DATA_FILE.with_name('cbk_monthly_usd_kes.csv')


def compare_with_exchange(commodity: str, fuel: str | None = 'Petrol',
                          start_month: str | None = None,
                          end_month: str | None = None) -> tuple[pd.DataFrame, dict]:
    """Align KNBS prices and CBK monthly USD/KES averages; index at 100."""
    item = commodity_trend(commodity)
    item_name = item['commodity'].iloc[0]
    if item_name in {'Petrol', 'Diesel', 'Kerosene'}:
        raise ValueError('Choose a non-fuel commodity.')
    merged = item[['date', 'price_kes']].rename(columns={'price_kes': item_name})
    if fuel:
        fuel_names = {'petrol': 'Petrol', 'diesel': 'Diesel', 'kerosene': 'Kerosene'}
        fuel_name = fuel_names.get(fuel.strip().casefold())
        if fuel_name is None:
            raise ValueError('Fuel must be Petrol, Diesel, or Kerosene.')
        fuel_df = commodity_trend(fuel_name)[['date', 'price_kes']].rename(
            columns={'price_kes': fuel_name})
        merged = merged.merge(fuel_df, on='date', validate='one_to_one')
    fx = pd.read_csv(FX_FILE, parse_dates=['date'])
    merged = merged.merge(fx, on='date', validate='one_to_one')
    if start_month:
        merged = merged[merged.date >= pd.Timestamp(start_month)]
    if end_month:
        merged = merged[merged.date <= pd.Timestamp(end_month)]
    merged = merged.sort_values('date').reset_index(drop=True)
    if len(merged) < 2:
        raise ValueError('Select at least two shared months in the data.')
    merged = merged.rename(columns={'kes_per_usd': 'USD/KES (KES per USD)'})
    columns = [c for c in merged.columns if c != 'date']
    start, end = merged.iloc[0], merged.iloc[-1]
    indices = merged[['date']].copy()
    changes = {}
    for name in columns:
        if start[name] <= 0:
            raise ValueError(f'Cannot index nonpositive start value for {name}.')
        indices[name] = merged[name] / start[name] * 100
        changes[name] = (end[name] / start[name] - 1) * 100
    return indices, {
        'start': start.date.strftime('%Y-%m'),
        'end': end.date.strftime('%Y-%m'),
        'months': len(merged),
        'changes': changes,
    }
