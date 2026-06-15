"""
categoriser.py
--------------
Two-pass categorisation system:

Pass 1 — Fast deterministic matching:
  Uses merchant lists from config.py. Instant, no API cost.
  Catches: Deliveroo, Starbucks, Tesco, Netflix, PureGym, Uber etc.

Pass 2 — LLM smart re-categorisation:
  Sends unrecognised "other" merchants to the LLM.
  Catches: Tea Time, Raj's Kitchen, The Brew House, local shops etc.
  Only runs on merchants not caught in Pass 1.

Also handles: frequent merchant detection across all categories.
"""

import os
import json
import pandas as pd
from src.config import get_config


CATEGORY_LABELS = {
    "food_delivery":      "Food Delivery",
    "coffee":             "Coffee & Cafes",
    "groceries_budget":   "Groceries (Budget)",
    "groceries_mid":      "Groceries (Mid-range)",
    "groceries_premium":  "Groceries (Premium)",
    "streaming":          "Subscriptions & Streaming",
    "gym":                "Gym & Fitness",
    "transport":          "Taxis & Ride-hailing",
    "other":              "Other Spending",
}

# These categories are "groceries" for grouping purposes
GROCERY_CATEGORIES = {"groceries_budget", "groceries_mid", "groceries_premium"}


def _matches_any(description: str, merchant_list: list) -> bool:
    desc = description.lower()
    return any(merchant.lower() in desc for merchant in merchant_list)


def _categorise_one(description: str, config: dict) -> str:
    """Pass 1: fast deterministic matching against known merchant lists."""
    if _matches_any(description, config["delivery_platforms"]):
        return "food_delivery"
    if _matches_any(description, config["coffee_chains"]):
        return "coffee"
    if _matches_any(description, config["premium_supermarkets"]):
        return "groceries_premium"
    if _matches_any(description, config["mid_supermarkets"]):
        return "groceries_mid"
    if _matches_any(description, config["budget_supermarkets"]):
        return "groceries_budget"
    if _matches_any(description, config["streaming_services"]):
        return "streaming"
    if _matches_any(description, config["gym_merchants"]):
        return "gym"
    if _matches_any(description, config["taxi_services"]):
        return "transport"
    return "other"


def _llm_recategorise(merchants: list, country: str) -> dict:
    """
    Pass 2: send unrecognised merchant names to the LLM for smart categorisation.

    The LLM uses real-world knowledge to identify:
    - Local cafes and tea shops → coffee
    - Local restaurants and takeaways → food_delivery
    - Local grocery/corner shops → groceries_mid
    - Local gyms and fitness studios → gym
    - Anything unclear → other

    Returns a dict: {merchant_name: category_string}
    """
    if not merchants:
        return {}

    try:
        from groq import Groq
        from dotenv import load_dotenv
        load_dotenv()

        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            return {}

        client = Groq(api_key=api_key)

        # Build the merchant list for the prompt
        merchant_list = "\n".join(f"- {m}" for m in merchants[:50])  # cap at 50

        prompt = f"""You are categorising bank statement merchant names for a {country} bank statement.

For each merchant name below, assign exactly one category from this list:
- food_delivery (restaurants, takeaways, fast food, food delivery apps)
- coffee (cafes, coffee shops, tea rooms, bakeries, juice bars)
- groceries_mid (supermarkets, grocery stores, corner shops, convenience stores, off licences)
- gym (gyms, fitness studios, sports centres, yoga, swimming pools)
- transport (taxis, trains, buses, parking, petrol stations, car parks)
- streaming (streaming services, apps, software subscriptions, online services)
- other (anything that does not clearly fit the above)

Rules:
- Use your real-world knowledge — "Tea Time" is likely a cafe → coffee
- "Arfat Mushtaq" is a person's name with no clear business type → other
- If unclear, use "other"
- Respond ONLY with valid JSON — no explanation, no markdown

Merchant names:
{merchant_list}

Respond with JSON in this exact format:
{{"merchant_name": "category", "merchant_name_2": "category"}}"""

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a bank transaction categoriser. "
                        "Respond only with valid JSON. No markdown, no explanation."
                    )
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            max_tokens=1000,
        )

        raw = response.choices[0].message.content.strip()

        # Strip any markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        result = json.loads(raw)

        # Validate — only keep known categories
        valid = set(CATEGORY_LABELS.keys())
        return {
            merchant: cat
            for merchant, cat in result.items()
            if cat in valid
        }

    except Exception:
        # If LLM fails, return empty dict — Pass 1 categories stand
        return {}


def categorise_all(df: pd.DataFrame, country: str, use_llm: bool = True) -> pd.DataFrame:
    """
    Full two-pass categorisation.

    Pass 1: fast deterministic matching (always runs)
    Pass 2: LLM re-categorisation of unknown merchants (runs if use_llm=True)

    Parameters
    ----------
    df       : DataFrame from parser
    country  : 'UK', 'US', or 'India'
    use_llm  : whether to run Pass 2 LLM categorisation (default True)
    """
    config = get_config(country)
    df = df.copy()

    # ── Pass 1: deterministic ─────────────────────────────────────────────────
    df["category"] = df["description"].apply(
        lambda desc: _categorise_one(desc, config)
    )

    # ── Pass 2: LLM re-categorisation for unknowns ────────────────────────────
    if use_llm:
        # Get unique merchants that landed in "other"
        other_mask = df["category"] == "other"
        if other_mask.any():
            # Get unique merchants by raw_desc (cleaner names than description)
            unknown_merchants = df.loc[other_mask, "raw_desc"].unique().tolist()

            if unknown_merchants:
                # Ask LLM to categorise them
                llm_categories = _llm_recategorise(unknown_merchants, country)

                # Apply LLM categories back to DataFrame
                if llm_categories:
                    def apply_llm_cat(row):
                        if row["category"] == "other":
                            return llm_categories.get(row["raw_desc"], "other")
                        return row["category"]

                    df["category"] = df.apply(apply_llm_cat, axis=1)

    # ── Add label column ──────────────────────────────────────────────────────
    df["category_label"] = df["category"].map(CATEGORY_LABELS)
    return df


def get_category_totals(df: pd.DataFrame) -> dict:
    """
    Returns a dict of {category: data} for all categories with transactions.
    """
    totals = {}
    for cat in CATEGORY_LABELS:
        subset = df[df["category"] == cat]
        if not subset.empty:
            totals[cat] = {
                "total":        subset["amount"].sum(),
                "count":        len(subset),
                "avg":          subset["amount"].mean(),
                "label":        CATEGORY_LABELS[cat],
                "transactions": subset[["date","raw_desc","amount"]].to_dict("records")
            }
    return totals


def get_frequent_merchants(df: pd.DataFrame, min_transactions: int = 3) -> list:
    """
    Finds merchants the user visits frequently (3+ times).
    These are worth calling out specifically in the report regardless of category.

    Returns a list of dicts sorted by transaction count descending.
    Each dict: {merchant, count, total, avg, category, category_label}
    """
    # Group by merchant name
    grouped = (
        df.groupby("raw_desc")
        .agg(
            count=("amount", "count"),
            total=("amount", "sum"),
            avg=("amount", "mean"),
            category=("category", "first"),
            category_label=("category_label", "first"),
        )
        .reset_index()
        .rename(columns={"raw_desc": "merchant"})
    )

    # Filter: only merchants with 3+ transactions
    frequent = grouped[grouped["count"] >= min_transactions].copy()
    frequent = frequent.sort_values("count", ascending=False)

    # Exclude income/salary rows (shouldn't be here but just in case)
    frequent = frequent[frequent["total"] > 0]

    return frequent.to_dict("records")


def get_top_other_merchants(df: pd.DataFrame, top_n: int = 8) -> dict:
    """
    Analyses the 'other' category transactions.
    Groups by merchant, returns top spenders with totals.
    """
    other_df = df[df["category"] == "other"].copy()
    if other_df.empty:
        return {}

    grouped = (
        other_df.groupby("raw_desc")["amount"]
        .agg(["sum","count","mean"])
        .reset_index()
        .rename(columns={"raw_desc":"merchant","sum":"total",
                         "count":"transactions","mean":"avg"})
        .sort_values("total", ascending=False)
        .head(top_n)
    )

    return {
        "total_other":       other_df["amount"].sum(),
        "transaction_count": len(other_df),
        "top_merchants":     grouped.to_dict("records"),
    }


def get_spending_by_week(df: pd.DataFrame) -> pd.DataFrame:
    """Returns total spending grouped by week."""
    df = df.copy()
    df["week"] = df["date"].dt.to_period("W")
    return df.groupby("week")["amount"].sum().reset_index()


def get_spending_by_day_of_week(df: pd.DataFrame) -> pd.DataFrame:
    """Returns total spending grouped by day of week."""
    df = df.copy()
    df["day_of_week"] = df["date"].dt.day_name()
    order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    result = df.groupby("day_of_week")["amount"].sum().reindex(order).fillna(0)
    return result.reset_index()