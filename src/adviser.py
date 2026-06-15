"""
adviser.py
----------
Generates honest generic advice for categories where we only know
what was paid — not whether the service was actually used.

Design principle: Never assume what a merchant is if we are not certain.
Never claim to know behaviour (gym attendance, streaming usage) we cannot see.
Only state what the bank data actually tells us.
"""

import pandas as pd
from src.config import get_config, get_currency_symbol


def advise_subscriptions(df: pd.DataFrame, country: str) -> dict | None:
    """
    Analyses subscription and streaming payments.
    We know what was paid. We do NOT claim to know what was watched.
    """
    subs_df = df[df["category"] == "streaming"].copy()
    if subs_df.empty:
        return None

    config = get_config(country)
    symbol = get_currency_symbol(country)

    total  = subs_df["amount"].sum()
    count  = len(subs_df)
    annual = total * 12

    # Identify which services (best effort from description)
    services_found = []
    for _, row in subs_df.iterrows():
        desc = row["description"]
        for service in config["streaming_services"]:
            if service.lower() in desc:
                services_found.append({
                    "name":   service.title(),
                    "amount": row["amount"]
                })
                break

    # Realistic saving: suggest cutting down to 2 active services
    services_to_keep = 2
    if count > services_to_keep:
        sorted_services  = sorted(services_found, key=lambda x: x["amount"])
        services_to_cut  = sorted_services[:count - services_to_keep]
        saving           = sum(s["amount"] for s in services_to_cut)
    else:
        saving           = 0
        services_to_cut  = []

    template = config["generic_advice"]["subscriptions"]
    advice_text = template.format(
        count=count, symbol=symbol,
        total=total, annual=annual, saving=saving,
    )

    return {
        "total":            total,
        "count":            count,
        "annual":           annual,
        "services_found":   services_found,
        "services_to_cut":  services_to_cut,
        "potential_saving": saving,
        "advice_text":      advice_text,
        "currency_symbol":  symbol,
    }


def advise_gym(df: pd.DataFrame, country: str) -> dict | None:
    """
    Analyses gym and fitness membership payments.

    IMPORTANT DESIGN DECISION:
    We know what was paid and to which merchant.
    We do NOT know:
    - Whether the merchant is actually a gym (could be a laundry app, software, etc.)
    - Whether the person attended
    - Whether it is good value for them

    So we ONLY state what we know and ask the user to verify.
    We never assume what a merchant is or judge attendance.
    """
    gym_df = df[df["category"] == "gym"].copy()
    if gym_df.empty:
        return None

    symbol = get_currency_symbol(country)
    total  = gym_df["amount"].sum()
    count  = len(gym_df)

    # Get merchant names
    merchants = gym_df.groupby("raw_desc")["amount"].agg(["sum","count"]).reset_index()
    merchants = merchants.rename(columns={"raw_desc":"merchant","sum":"total","count":"visits"})
    merchant_list = merchants.to_dict("records")

    # Build honest merchant summary
    merchant_lines = []
    for m in merchant_list:
        merchant_lines.append(
            f"{m['merchant']} — {m['visits']} payment{'s' if m['visits']>1 else ''}, "
            f"{symbol}{m['total']:.2f} total"
        )
    merchant_summary = "\n".join(merchant_lines)

    # Honest advice — no assumptions about what the merchant is
    if len(merchant_list) == 1:
        name = merchant_list[0]["merchant"]
        advice_text = (
            f"You have {count} payment{'s' if count>1 else ''} to {name} "
            f"totalling {symbol}{total:.2f} this month. "
            f"We've categorised this as gym or fitness — but if this is something else "
            f"(an app, subscription, or service), check the All Transactions tab. "
            f"Only you know whether you're getting value from this payment."
        )
    else:
        advice_text = (
            f"You have {count} payments totalling {symbol}{total:.2f} "
            f"categorised as gym or fitness:\n{merchant_summary}\n"
            f"Check the All Transactions tab to confirm what each merchant is. "
            f"Only you know whether these are worth keeping."
        )

    return {
        "total":           total,
        "count":           count,
        "merchant_list":   merchant_list,
        "advice_text":     advice_text,
        "currency_symbol": symbol,
    }


def advise_transport(df: pd.DataFrame, country: str) -> dict | None:
    """
    Analyses taxi and ride-hailing spending.
    We know total spent and trip count. We do NOT know trip purpose.
    """
    transport_df = df[df["category"] == "transport"].copy()
    if transport_df.empty:
        return None

    config = get_config(country)
    symbol = get_currency_symbol(country)

    total = transport_df["amount"].sum()
    count = len(transport_df)
    avg   = transport_df["amount"].mean() if count > 0 else 0

    template    = config["generic_advice"]["transport"]
    advice_text = template.format(
        symbol=symbol, total=total, count=count, avg=avg,
    )

    return {
        "total":           total,
        "count":           count,
        "avg":             avg,
        "advice_text":     advice_text,
        "currency_symbol": symbol,
    }


def advise_fast_food(df: pd.DataFrame, country: str) -> dict | None:
    """
    Analyses fast food and walk-in takeaway spending.
    These are walk-in purchases, not delivery apps.
    """
    ff_df = df[df["category"] == "fast_food"].copy()
    if ff_df.empty:
        return None

    symbol = get_currency_symbol(country)
    total  = ff_df["amount"].sum()
    count  = len(ff_df)
    avg    = ff_df["amount"].mean() if count > 0 else 0

    # Top merchants
    top = (
        ff_df.groupby("raw_desc")["amount"]
        .agg(["sum","count"])
        .reset_index()
        .rename(columns={"raw_desc":"merchant","sum":"total","count":"visits"})
        .sort_values("total", ascending=False)
        .head(3)
    )

    merchant_str = ", ".join(
        f"{r['merchant']} ({r['visits']}x)"
        for _, r in top.iterrows()
    )

    advice_text = (
        f"You spent {symbol}{total:.2f} at fast food and walk-in takeaways "
        f"this month across {count} visit{'s' if count>1 else ''}. "
        f"Top merchants: {merchant_str}. "
        f"Average spend per visit: {symbol}{avg:.2f}."
    )

    return {
        "total":           total,
        "count":           count,
        "avg":             avg,
        "top_merchants":   top.to_dict("records"),
        "advice_text":     advice_text,
        "currency_symbol": symbol,
    }


def advise_transfers(df: pd.DataFrame, country: str) -> dict | None:
    """
    Summarises personal transfers detected in the statement.
    These are payments to individuals, not merchants.
    """
    transfer_df = df[df["category"] == "transfer"].copy()
    if transfer_df.empty:
        return None

    symbol = get_currency_symbol(country)
    total  = transfer_df["amount"].sum()
    count  = len(transfer_df)

    recipients = transfer_df["raw_desc"].unique().tolist()
    recipient_str = ", ".join(recipients[:5])

    advice_text = (
        f"You have {count} personal transfer{'s' if count>1 else ''} "
        f"totalling {symbol}{total:.2f} this month "
        f"(to: {recipient_str}). "
        f"These are payments to individuals and are not included in your spending categories."
    )

    return {
        "total":           total,
        "count":           count,
        "recipients":      recipients,
        "advice_text":     advice_text,
        "currency_symbol": symbol,
    }


def advise_other(df: pd.DataFrame, country: str) -> dict | None:
    """
    Summarises uncategorised spending.
    No specific advice — just the total so the user can investigate.
    """
    other_df = df[df["category"] == "other"].copy()
    if other_df.empty:
        return None

    symbol = get_currency_symbol(country)
    total  = other_df["amount"].sum()
    count  = len(other_df)

    top_merchants = (
        other_df.groupby("raw_desc")["amount"]
        .sum()
        .sort_values(ascending=False)
        .head(5)
        .reset_index()
    )

    return {
        "total":         total,
        "count":         count,
        "top_merchants": top_merchants.to_dict("records"),
        "advice_text": (
            f"You have {count} other transactions totalling {symbol}{total:.2f} "
            f"that are not in the main categories. "
            f"Review them in the All Transactions tab — they may include online shopping, "
            f"services, or recurring payments worth checking."
        ),
        "currency_symbol": symbol,
    }


def get_all_generic_advice(df: pd.DataFrame, country: str) -> dict:
    """
    Runs all generic advice modules and returns results dict.
    """
    return {
        "subscriptions": advise_subscriptions(df, country),
        "gym":           advise_gym(df, country),
        "transport":     advise_transport(df, country),
        "fast_food":     advise_fast_food(df, country),
        "transfers":     advise_transfers(df, country),
        "other":         advise_other(df, country),
    }