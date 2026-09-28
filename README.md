# Kenya Cost-of-Living Evidence Agent

This continues the KNBS commodity-price agent and adds CBK's monthly USD/KES period average. The app shows indexed monthly comparisons between an essential, a fuel, and the exchange rate. It answers explicit comparison questions using calculations from the files, not prices invented by the language model.

## Run on Windows

Extract this ZIP into a folder, open **that folder** in VS Code, and use a terminal in the folder that directly contains `src` and `data`:

```powershell
py -m pip install pandas streamlit ollama pydantic
py -m streamlit run src/app.py
```

Keep Ollama running locally with `qwen3:1.7b` for the chat feature. The charts work without Ollama. Try:

> Compare cooking oil, petrol, and the USD/KES exchange rate from February 2021 to May 2022

Expected: cooking oil +56.78%, petrol +30.09%, USD/KES +6.02% over 16 shared months. These movements do not prove a causal link.

## Data

- `data/commodity_prices_clean.csv`: KNBS monthly commodity prices, 10 series × 40 months, February 2019–May 2022. The source Excel workbook is not included. The optional `src/clean_prices.py` only runs if that original workbook is present.
- `data/cbk_monthly_raw.csv`: CBK's [monthly exchange-rate (period average) CSV](https://www.centralbank.go.ke/statistics/exchange-rates/monthly-exchange-rate-period-average/), downloaded September 28, 2026. `src/clean_exchange.py` extracts the `United States dollar` column to `data/cbk_monthly_usd_kes.csv`. Values are Kenyan shillings per US dollar, not a dollar price in shillings.
- KNBS fuel prices in this project are separate from EPRA's maximum pump-price series. Do not label them as EPRA or interpret co-movement as proof of cause.

For the first release, this is a historical evidence agent. It does not answer current 2026 price questions. Next enhancement: incorporate EPRA's pump-price series with explicit location and 15th-to-14th periods.
