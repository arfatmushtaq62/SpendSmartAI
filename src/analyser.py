"""
analyser.py
-----------
Deep analysis engine for the three priority categories:
  1. Food Delivery
  2. Coffee and Daily Habits
  3. Groceries

For each category, produces:
  - Specific numbers from the user's actual data
  - The smarter alternative with cost and nutrition context
  - Personalised savings calculation
  - Actionable recommendation

This is what makes SpendSmart AI different from generic finance apps.
We do not guess. We calculate from real transaction data.
"""

import pandas as pd
from src.config import get_config, get_currency_symbol, get_benchmarks


# ── FOOD DELIVERY ANALYSIS ───────────────────────────────────────────────────

def analyse_food_delivery(df: pd.DataFrame, country: str) -> dict | None:
    """
    Analyses food delivery spending.
    Returns None if no delivery transactions found.
    """
    delivery_df = df[df["category"] == "food_delivery"].copy()
    if delivery_df.empty:
        return None

    config = get_config(country)
    benchmarks = get_benchmarks(country)
    symbol = get_currency_symbol(country)

    total_spent = delivery_df["amount"].sum()
    order_count = len(delivery_df)
    avg_order = delivery_df["amount"].mean()

    # Home cooking equivalent cost
    home_cost_total = order_count * benchmarks["home_cooking_meal_avg"]
    potential_saving = total_spent - home_cost_total

    # Pattern: which days do they order most?
    delivery_df["day"] = delivery_df["date"].dt.day_name()
    day_counts = delivery_df["day"].value_counts()
    most_common_day = day_counts.index[0] if not day_counts.empty else "weekdays"
    most_common_day_count = int(day_counts.iloc[0]) if not day_counts.empty else 0

    # Which platforms do they use?
    platforms_used = {}
    for _, row in delivery_df.iterrows():
        desc = row["description"]
        for platform in config["delivery_platforms"]:
            if platform in desc:
                clean_name = platform.title()
                platforms_used[clean_name] = platforms_used.get(clean_name, 0) + row["amount"]
                break

    # How many times per week on average?
    if not delivery_df["date"].empty:
        date_range = (delivery_df["date"].max() - delivery_df["date"].min()).days
        weeks = max(date_range / 7, 1)
        orders_per_week = order_count / weeks
    else:
        orders_per_week = 0

    # Realistic saving: if they cook at home half the time
    realistic_saving = potential_saving * 0.5

    return {
        "total_spent": total_spent,
        "order_count": order_count,
        "avg_order": avg_order,
        "orders_per_week": round(orders_per_week, 1),
        "home_cost_total": home_cost_total,
        "home_cost_per_meal": benchmarks["home_cooking_meal_avg"],
        "potential_saving_full": potential_saving,
        "realistic_saving": realistic_saving,
        "annual_saving": realistic_saving * 12,
        "most_common_day": most_common_day,
        "most_common_day_count": most_common_day_count,
        "platforms_used": platforms_used,
        "currency_symbol": symbol,
        "nutrition_note": (
            "Home-cooked meals typically have 30-50% less sodium, "
            "fewer additives, and better portion control than delivery food."
        )
    }


def build_food_delivery_message(analysis: dict) -> str:
    """Builds the plain English explanation for food delivery."""
    if not analysis:
        return ""

    s = analysis["currency_symbol"]
    lines = []

    lines.append(
        f"You ordered food delivery {analysis['order_count']} times "
        f"({analysis['orders_per_week']}x per week on average). "
        f"Average order: {s}{analysis['avg_order']:.2f}. "
        f"Total this month: {s}{analysis['total_spent']:.2f}."
    )

    if analysis["platforms_used"]:
        top_platforms = sorted(
            analysis["platforms_used"].items(), key=lambda x: x[1], reverse=True
        )[:3]
        platform_str = ", ".join(
            f"{p} ({s}{v:.2f})" for p, v in top_platforms
        )
        lines.append(f"Platforms used: {platform_str}.")

    lines.append(
        f"\n💡 The smarter alternative: The same meal cooked at home costs "
        f"approximately {s}{analysis['home_cost_per_meal']:.2f}. "
        f"That is {s}{analysis['avg_order'] - analysis['home_cost_per_meal']:.2f} "
        f"less per meal."
    )

    lines.append(analysis["nutrition_note"])

    lines.append(
        f"\n📊 If you cooked at home just half the time: "
        f"you would save approximately {s}{analysis['realistic_saving']:.2f} this month "
        f"— that is {s}{analysis['annual_saving']:.2f} per year."
    )

    if analysis["most_common_day_count"] > 1:
        lines.append(
            f"Your most common delivery day is {analysis['most_common_day']} "
            f"({analysis['most_common_day_count']} orders). "
            f"Meal prepping on Sundays for the week ahead is the single habit "
            f"that has the highest ROI here."
        )

    return " ".join(lines)


# ── COFFEE ANALYSIS ──────────────────────────────────────────────────────────

def analyse_coffee(df: pd.DataFrame, country: str) -> dict | None:
    """
    Analyses coffee and cafe spending.
    Returns None if no coffee transactions found.
    """
    coffee_df = df[df["category"] == "coffee"].copy()
    if coffee_df.empty:
        return None

    benchmarks = get_benchmarks(country)
    symbol = get_currency_symbol(country)

    total_spent = coffee_df["amount"].sum()
    visit_count = len(coffee_df)
    avg_spend = coffee_df["amount"].mean()

    home_cost_total = visit_count * benchmarks["home_coffee_avg"]
    potential_saving = total_spent - home_cost_total

    # Pattern: which days?
    coffee_df["day"] = coffee_df["date"].dt.day_name()
    day_counts = coffee_df["day"].value_counts()
    most_common_day = day_counts.index[0] if not day_counts.empty else "weekdays"

    # Visits per week
    if not coffee_df["date"].empty:
        date_range = (coffee_df["date"].max() - coffee_df["date"].min()).days
        weeks = max(date_range / 7, 1)
        visits_per_week = visit_count / weeks
    else:
        visits_per_week = 0

    # Realistic saving: switch 60% of visits to home
    realistic_saving = potential_saving * 0.6

    # Calorie note — average coffee shop drink with milk and syrup
    monthly_calories_saved = visit_count * 150  # avg latte = ~150 cal

    return {
        "total_spent": total_spent,
        "visit_count": visit_count,
        "avg_spend": avg_spend,
        "visits_per_week": round(visits_per_week, 1),
        "home_cost_per_cup": benchmarks["home_coffee_avg"],
        "home_cost_total": home_cost_total,
        "potential_saving_full": potential_saving,
        "realistic_saving": realistic_saving,
        "annual_saving": realistic_saving * 12,
        "most_common_day": most_common_day,
        "monthly_calories_saved": monthly_calories_saved,
        "currency_symbol": symbol,
    }


def build_coffee_message(analysis: dict) -> str:
    """Builds the plain English explanation for coffee spending."""
    if not analysis:
        return ""

    s = analysis["currency_symbol"]
    lines = []

    lines.append(
        f"You visited coffee shops {analysis['visit_count']} times this month "
        f"({analysis['visits_per_week']}x per week). "
        f"Average spend per visit: {s}{analysis['avg_spend']:.2f}. "
        f"Total: {s}{analysis['total_spent']:.2f}."
    )

    lines.append(
        f"\n💡 The smarter alternative: A good quality home coffee costs "
        f"approximately {s}{analysis['home_cost_per_cup']:.2f} per cup — "
        f"a cafetiere or a simple filter coffee machine pays for itself "
        f"within a few weeks."
    )

    lines.append(
        f"\n📊 If you made coffee at home for 60% of those visits: "
        f"you would save approximately {s}{analysis['realistic_saving']:.2f} this month "
        f"— {s}{analysis['annual_saving']:.2f} per year. "
        f"You would also avoid around {analysis['monthly_calories_saved']:,} calories "
        f"from syrups and milk in shop-bought drinks."
    )

    lines.append(
        f"Keep the visits you genuinely enjoy — a coffee shop as a treat or "
        f"a place to work is a reasonable spend. The habit purchases "
        f"(quick grab on the way somewhere) are the ones worth replacing."
    )

    return " ".join(lines)


# ── GROCERIES ANALYSIS ───────────────────────────────────────────────────────

def analyse_groceries(df: pd.DataFrame, country: str) -> dict | None:
    """
    Analyses grocery spending across budget, mid, and premium supermarkets.
    Returns None if no grocery transactions found.
    """
    budget_df = df[df["category"] == "groceries_budget"].copy()
    mid_df = df[df["category"] == "groceries_mid"].copy()
    premium_df = df[df["category"] == "groceries_premium"].copy()

    all_grocery = pd.concat([budget_df, mid_df, premium_df])
    if all_grocery.empty:
        return None

    benchmarks = get_benchmarks(country)
    symbol = get_currency_symbol(country)

    budget_total = budget_df["amount"].sum()
    mid_total = mid_df["amount"].sum()
    premium_total = premium_df["amount"].sum()
    total_spent = all_grocery["amount"].sum()

    # Determine where they mainly shop
    if premium_total > 0 and premium_total >= (mid_total + budget_total):
        primary_tier = "premium"
        saving_pct = benchmarks["budget_supermarket_saving_pct"]
        potential_saving = premium_total * (saving_pct / 100)
        # Realistic: switch 60% of premium shop to budget/mid
        realistic_saving = potential_saving * 0.6
    elif mid_total >= budget_total and mid_total > 0:
        primary_tier = "mid"
        saving_pct = int(benchmarks["budget_supermarket_saving_pct"] * 0.6)
        potential_saving = mid_total * (saving_pct / 100)
        realistic_saving = potential_saving * 0.5
    else:
        primary_tier = "budget"
        potential_saving = 0
        realistic_saving = 0
        saving_pct = 0

    shop_count = len(all_grocery)

    return {
        "total_spent": total_spent,
        "budget_total": budget_total,
        "mid_total": mid_total,
        "premium_total": premium_total,
        "shop_count": shop_count,
        "primary_tier": primary_tier,
        "saving_pct": saving_pct,
        "potential_saving": potential_saving,
        "realistic_saving": realistic_saving,
        "annual_saving": realistic_saving * 12,
        "currency_symbol": symbol,
        "country": country,
    }


def build_groceries_message(analysis: dict) -> str:
    """Builds the plain English explanation for grocery spending."""
    if not analysis:
        return ""

    s = analysis["currency_symbol"]
    tier = analysis["primary_tier"]
    lines = []

    lines.append(
        f"You made {analysis['shop_count']} grocery shops this month, "
        f"spending {s}{analysis['total_spent']:.2f} in total."
    )

    if analysis["budget_total"] > 0:
        lines.append(f"Budget stores (Aldi/Lidl/Walmart etc.): {s}{analysis['budget_total']:.2f}.")
    if analysis["mid_total"] > 0:
        lines.append(f"Mid-range stores: {s}{analysis['mid_total']:.2f}.")
    if analysis["premium_total"] > 0:
        lines.append(f"Premium stores: {s}{analysis['premium_total']:.2f}.")

    if tier == "premium" and analysis["realistic_saving"] > 0:
        lines.append(
            f"\n💡 The smarter alternative: Studies consistently show that "
            f"budget supermarkets like Aldi and Lidl are {analysis['saving_pct']}% cheaper "
            f"on average for equivalent products. The quality difference on staples "
            f"(pasta, rice, eggs, milk, frozen vegetables, tinned goods) is minimal."
        )
        lines.append(
            f"\n📊 A split-shop approach — budget store for staples, premium store "
            f"for items where quality genuinely matters to you — could save approximately "
            f"{s}{analysis['realistic_saving']:.2f}/month ({s}{analysis['annual_saving']:.2f}/year) "
            f"while keeping the products you actually notice a difference in."
        )
    elif tier == "mid" and analysis["realistic_saving"] > 0:
        lines.append(
            f"\n💡 You are already shopping at reasonable value supermarkets. "
            f"Switching some of your staples to a budget store like Aldi or Lidl "
            f"could save approximately {s}{analysis['realistic_saving']:.2f}/month "
            f"without a big lifestyle change."
        )
    else:
        lines.append(
            f"\n✅ You are already shopping at budget-friendly supermarkets. "
            f"Good habit — this is one of the highest-ROI financial decisions you can make."
        )

    return " ".join(lines)


# ── OTHER SPENDING ANALYSIS (fallback when deep categories missing) ────────────

def analyse_other_spending(
    df,
    country: str,
    missing_categories: list,
) -> dict | None:
    """
    When one or more of the top 3 categories are missing, this function
    analyses the actual top spends in the 'other' bucket using the LLM.

    Ensures the report always reflects what the person ACTUALLY spent on,
    rather than apologising for missing categories.
    """
    import os
    from groq import Groq
    from dotenv import load_dotenv
    load_dotenv()

    from src.categoriser import get_top_other_merchants
    from src.config import get_currency_symbol

    symbol     = get_currency_symbol(country)
    other_data = get_top_other_merchants(df, top_n=8)

    if not other_data or not other_data.get("top_merchants"):
        return None

    total_other = other_data["total_other"]
    merchants   = other_data["top_merchants"]
    if total_other < 1:
        return None

    # Build merchant summary for the LLM
    merchant_lines = []
    for m in merchants:
        merchant_lines.append(
            f"  - {m['merchant']}: {symbol}{m['total']:.2f} "
            f"({m['transactions']} transaction{'s' if m['transactions'] > 1 else ''})"
        )
    merchant_summary = "\n".join(merchant_lines)

    missing_labels = {
        "food_delivery": "food delivery",
        "coffee":        "coffee shops",
        "groceries":     "supermarkets / groceries",
    }
    missing_text = ", ".join(missing_labels.get(c, c) for c in missing_categories)

    prompt = f"""A person's bank statement was analysed for {country}.
The following categories had NO transactions: {missing_text}.

Instead, here are their top actual spending merchants this month:
{merchant_summary}

Total in these uncategorised transactions: {symbol}{total_other:.2f}

Write a SHORT, friendly analysis (3-5 sentences) of their actual spending.
Include:
1. What their top spends appear to be (name the merchants)
2. One honest observation about the spending pattern
3. One practical suggestion for the biggest spend

Tone: warm, specific, non-judgmental. Plain English. No jargon.
Do NOT mention the missing categories. Focus only on what IS there.
Do NOT start with "I" or "Based on"."""

    try:
        api_key = os.getenv("GROQ_API_KEY")
        client  = Groq(api_key=api_key)

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are SpendSmart AI, a friendly personal finance assistant. "
                        "Give short, specific, actionable spending insights. Maximum 5 sentences."
                    )
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.4,
            max_tokens=300,
        )

        return {
            "total_other":        total_other,
            "top_merchants":      merchants,
            "analysis_text":      response.choices[0].message.content.strip(),
            "missing_categories": missing_categories,
            "currency_symbol":    symbol,
        }

    except Exception:
        return {
            "total_other":        total_other,
            "top_merchants":      merchants,
            "analysis_text":      None,
            "missing_categories": missing_categories,
            "currency_symbol":    symbol,
        }


def build_other_spending_message(analysis: dict | None) -> str:
    """Builds the display message for other spending analysis."""
    if not analysis:
        return ""

    s         = analysis["currency_symbol"]
    merchants = analysis["top_merchants"]

    if analysis.get("analysis_text"):
        return analysis["analysis_text"]

    # Fallback if LLM failed
    lines = [f"Your top spending this month ({s}{analysis['total_other']:.2f} total):"]
    for m in merchants[:5]:
        lines.append(
            f"• {m['merchant']}: {s}{m['total']:.2f} "
            f"({m['transactions']} transaction{'s' if m['transactions'] > 1 else ''})"
        )
    return "\n".join(lines)