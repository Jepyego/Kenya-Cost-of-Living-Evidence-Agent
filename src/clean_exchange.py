"""Extract the USD/KES monthly period average from the CBK source CSV."""
from pathlib import Path
import pandas as pd

DATA = Path(__file__).resolve().parents[1] / 'data'
source = DATA / 'cbk_monthly_raw.csv'
prices = pd.read_csv(source, skiprows=1, encoding='utf-8-sig')
fx = prices[['Year', 'Month', 'United States dollar']].copy()
fx.columns = ['year', 'month', 'kes_per_usd']
fx['date'] = pd.to_datetime(dict(year=fx.year, month=fx.month, day=1), errors='coerce')
fx['kes_per_usd'] = pd.to_numeric(fx['kes_per_usd'], errors='coerce')
fx = fx[(fx.date >= '2019-02-01') & (fx.date <= '2022-05-01')]
fx = fx[['date', 'kes_per_usd']].dropna().sort_values('date')
if len(fx) != 40 or fx.date.duplicated().any() or (fx.kes_per_usd <= 0).any():
    raise ValueError('Expected 40 unique positive monthly USD/KES averages.')
fx.to_csv(DATA / 'cbk_monthly_usd_kes.csv', index=False)
print(f'Saved {len(fx)} months of USD/KES averages.')
