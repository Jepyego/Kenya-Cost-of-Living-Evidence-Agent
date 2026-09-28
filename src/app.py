import streamlit as st
import pandas as pd
from price_tools import DATA_FILE, commodity_trend, compare_with_fuel, compare_with_exchange

from agent import answer_question

st.set_page_config(
    page_title="Kenya Cost-of-Living Agent",
    page_icon="📊",
    layout="centered",
)

st.title("Kenya Cost-of-Living Agent")
st.caption(
    "Explore prices for 10 commodities from February 2019 "
    "to May 2022. Prices are in Kenyan shillings."
)

st.info(
    "The source data does not specify a county. Price changes "
    "show trends in this dataset, not what caused them."
)

all_prices = pd.read_csv(DATA_FILE)
commodities = sorted(all_prices["commodity"].unique())

selected = st.selectbox(
    "Explore a commodity's monthly prices",
    commodities
)

trend = commodity_trend(selected)
st.line_chart(
    trend.set_index("date")["price_kes"],
    y_label="Price (KES)"
)
st.caption(f"Measurement: {trend['unit'].iloc[0]}")

st.subheader("Compare with fuel")
non_fuel = [c for c in commodities if c not in {"Petrol", "Diesel", "Kerosene"}]
item = st.selectbox("Essential", non_fuel, index=non_fuel.index("Cooking oil"))
fuel = st.selectbox("Fuel", ["Petrol", "Diesel", "Kerosene"])
indices, summary = compare_with_fuel(item, fuel)
st.line_chart(indices.set_index("date"), y_label="Price index (first month = 100)")
st.write(
    f"{summary['start']} to {summary['end']}: {item} "
    f"{summary['commodity_change_pct']:+.1f}%; {fuel} "
    f"{summary['fuel_change_pct']:+.1f}%."
)
st.caption(
    "Both lines use KNBS prices and begin at 100 for easy comparison. "
    "Moving together does not prove one price caused the other to change."
)

st.subheader("Compare with USD/KES exchange rate")
exchange_item = st.selectbox("Essential for exchange-rate comparison", non_fuel, index=non_fuel.index("Cooking oil"))
exchange_fuel = st.selectbox("Include a fuel series", ["Petrol", "Diesel", "Kerosene", "None"])
fx_indices, fx_summary = compare_with_exchange(
    exchange_item, None if exchange_fuel == "None" else exchange_fuel
)
st.line_chart(fx_indices.set_index("date"), y_label="Index (first month = 100)")
st.write(
    f"{fx_summary['start']} to {fx_summary['end']}: " + "; ".join(
        f"{name} {pct:+.1f}%" for name, pct in fx_summary["changes"].items()
    )
)
st.caption(
    "USD/KES is the CBK monthly average in shillings per US dollar. "
    "The other prices come from KNBS. Similar movements do not show causation."
)

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

question = st.chat_input(
    "Ask about a commodity trend or compare two months"
)

if question:
    st.session_state.messages.append(
        {"role": "user", "content": question}
    )
    with st.chat_message("user"):
        st.write(question)

    with st.chat_message("assistant"):
        with st.spinner("Checking the price data..."):
            try:
                answer = answer_question(question)
            except Exception as error:
                answer = f"I couldn't complete the analysis: {error}"
        st.write(answer)

    st.session_state.messages.append(
        {"role": "assistant", "content": answer}
    )

st.markdown(
    "[Data source: KNBS commodity prices]"
    "(https://nipfn.knbs.or.ke/download/"
    "monthly-prices-of-selected-commodities-"
    "feb-2019-to-may-2022-source-cpi-knbs/)"
)
st.markdown("[CBK monthly exchange-rate source](https://www.centralbank.go.ke/statistics/exchange-rates/monthly-exchange-rate-period-average/)")
