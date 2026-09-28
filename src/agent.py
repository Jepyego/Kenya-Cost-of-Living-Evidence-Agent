from typing import Literal

import pandas as pd
from ollama import chat
from pydantic import BaseModel
import re
from datetime import datetime

from price_tools import DATA_FILE, compare_months, commodity_trend, compare_with_fuel, compare_with_exchange

MODEL = "qwen3:1.7b"


class ToolChoice(BaseModel):
    tool: Literal["compare", "trend", "fuel", "exchange", "unknown"]
    start_month: str
    end_month: str
    commodity: str
    fuel: Literal["Petrol", "Diesel", "Kerosene"] = "Petrol"


def select_tool(question: str) -> ToolChoice:
    response = chat(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "Select one data tool for the user's question. "
                    "Choose 'compare' for price changes or rankings between "
                    "two months. Choose 'trend' for the history of one commodity. "
                    "Choose 'fuel' when comparing an essential with petrol, diesel, or kerosene. "
                    "Choose 'exchange' for a commodity versus USD/KES exchange rates. "
                    "Choose 'unknown' for questions the data cannot answer. "
                    "Available dates: 2019-02 through 2022-05. "
                    "Return only the requested JSON fields. "
                    "Do not calculate or invent prices."
                ),
            },
            {"role": "user", "content": question},
        ],
        format=ToolChoice.model_json_schema(),
        options={"temperature": 0},
        think=False,
    )
    return ToolChoice.model_validate_json(response.message.content)

def months_in_question(question: str) -> list[str]:
    pattern = (
        r"\b(January|February|March|April|May|June|July|August|"
        r"September|October|November|December)\s+(20\d{2})\b"
    )
    matches = re.findall(pattern, question, flags=re.IGNORECASE)
    return [
        datetime.strptime(
            f"{month.title()} {year}", "%B %Y"
        ).strftime("%Y-%m")
        for month, year in matches
    ]

def explicit_comparison_question(question: str) -> ToolChoice | None:
    """Route explicit commodity-versus-fuel requests before model classification."""
    normalized = " ".join(question.casefold().split())
    fuels = ("Petrol", "Diesel", "Kerosene")
    exchange = bool(re.search(r"exchange rate|usd/kes|dollar.+shilling", normalized))
    fuel = next((name for name in fuels if name.casefold() in normalized), None)
    if not exchange and (fuel is None or not re.search(
        r"\b(with|against|versus|vs|alongside)\b", normalized
    )):
        return None
    names = pd.read_csv(DATA_FILE)["commodity"].drop_duplicates()
    for name in names:
        if name in fuels:
            continue
        if " ".join(name.casefold().split()) in normalized:
            dates = months_in_question(question)
            return ToolChoice(
                tool="exchange" if exchange else "fuel",
                commodity=name, fuel=fuel or "Petrol",
                start_month=dates[0] if len(dates) == 2 else "",
                end_month=dates[1] if len(dates) == 2 else "",
            )
    return None


def answer_question(question: str) -> str:
    choice = explicit_comparison_question(question) or select_tool(question)
    print(f"[Agent selected: {choice.tool}]")

    try:
        if choice.tool == "compare":
            requested_months = months_in_question(question)
            if len(requested_months) == 2:
                choice.start_month, choice.end_month = requested_months

            result = compare_months(
                choice.start_month, choice.end_month
            ).head(3)

            lines = [
                f"Top price increases, {choice.start_month} to "
                f"{choice.end_month}:"
            ]
            for rank, row in enumerate(
                result.itertuples(index=False), start=1
            ):
                lines.append(
                    f"{rank}. {row.commodity}: {row.change_pct:.2f}% "
                    f"(KES {row.price_kes_start:.2f} to "
                    f"KES {row.price_kes_end:.2f}, {row.unit})"
                )
            return "\n".join(lines)

        if choice.tool == "exchange":
            dates = months_in_question(question)
            start = dates[0] if len(dates) == 2 else None
            end = dates[1] if len(dates) == 2 else None
            normalized = " ".join(question.casefold().split())
            requested_fuel = next(
                (name for name in ("Petrol", "Diesel", "Kerosene")
                 if name.casefold() in normalized), None
            )
            _, summary = compare_with_exchange(
                choice.commodity, requested_fuel, start, end
            )
            changes = "; ".join(
                f"{name} {pct:+.2f}%" for name, pct in summary["changes"].items()
            )
            return (
                f"From {summary['start']} to {summary['end']} "
                f"({summary['months']} shared months): {changes}. "
                "KNBS supplies commodity and fuel prices; CBK supplies the "
                "monthly USD/KES average. Co-movement does not establish causation."
            )

        if choice.tool == "fuel":
            requested_months = months_in_question(question)
            start = requested_months[0] if len(requested_months) == 2 else None
            end = requested_months[1] if len(requested_months) == 2 else None
            _, summary = compare_with_fuel(choice.commodity, choice.fuel, start, end)
            return (
                f"From {summary['start']} to {summary['end']}, "
                f"{summary['commodity']} changed {summary['commodity_change_pct']:+.2f}% "
                f"and {summary['fuel']} changed {summary['fuel_change_pct']:+.2f}% "
                f"across {summary['months']} shared months. "
                "These are movements in the KNBS dataset; the comparison "
                "does not establish that fuel caused the commodity price change."
            )

        if choice.tool == "trend":
            trend = commodity_trend(choice.commodity)
            first = trend.iloc[0]
            last = trend.iloc[-1]
            change_pct = (
                (last["price_kes"] / first["price_kes"] - 1) * 100
            )
            return (
                f"{first['commodity']} ({first['unit']}): "
                f"KES {first['price_kes']:.2f} in "
                f"{first['date'].strftime('%Y-%m')} to "
                f"KES {last['price_kes']:.2f} in "
                f"{last['date'].strftime('%Y-%m')}; "
                f"change: {change_pct:.2f}% across "
                f"{len(trend)} recorded months."
            )

        return (
            "I can compare months, show a commodity trend, or compare it with fuel "
            "from February 2019 to May 2022."
        )

    except (ValueError, TypeError) as error:
        return f"I could not run that data tool: {error}"


if __name__ == "__main__":
    question = "Show the price trend for Cooking oil"
    print(f"Question: {question}\n")
    print(answer_question(question))
