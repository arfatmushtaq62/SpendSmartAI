"""
report.py
---------
Generates the final plain English money report using Groq.

Key rule: For gym, transport, and subscriptions — the pre-written
advice_text from adviser.py is used VERBATIM. The LLM must not
rewrite or add assumptions to these sections.

The LLM only writes sections where we have real calculated data
(food delivery, coffee, groceries, summary, actions).
"""

import os
from groq import Groq
from dotenv import load_dotenv
from src.config import get_currency_symbol

load_dotenv()


def _get_client() -> Groq:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not found in .env file")
    return Groq(api_key=api_key)


def generate_report(
    country: str,
    summary: dict,
    food_analysis: dict | None,
    coffee_analysis: dict | None,
    grocery_analysis: dict | None,
    generic_advice: dict,
    food_message: str,
    coffee_message: str,
    grocery_message: str,
    other_analysis: dict | None = None,
    other_message: str = "",
    frequent_merchants: list | None = None,
) -> str:
    """
    Generates the complete plain English money report.

    Strategy:
    - Sections with calculated data (food, coffee, groceries): LLM writes these
    - Sections with generic advice (gym, transport, subscriptions): use verbatim text
    - This prevents the LLM from adding assumptions to uncertain categories
    """
    client   = _get_client()
    symbol   = get_currency_symbol(country)
    frequent = frequent_merchants or []

    food_found    = bool(food_analysis)
    coffee_found  = bool(coffee_analysis)
    grocery_found = bool(grocery_analysis)
    has_generic   = any(
        a and a.get("advice_text") for a in generic_advice.values()
    )
    has_other = bool(other_analysis and other_analysis.get("top_merchants"))

    if not any([food_found, coffee_found, grocery_found, has_generic, has_other]):
        return _no_data_report(country, summary, symbol)

    # ── Build context for the LLM ─────────────────────────────────────────────
    parts = []
    parts.append(f"Country: {country} | Currency: {symbol}")
    parts.append(
        f"Statement: {summary.get('date_from','?')} to {summary.get('date_to','?')} | "
        f"{summary.get('total_transactions',0)} transactions | "
        f"Total: {symbol}{summary.get('total_spent',0):.2f}"
    )

    # Frequent merchants
    if frequent:
        lines = []
        for m in frequent[:6]:
            lines.append(
                f"  - {m['merchant']}: {m['count']}x, "
                f"{symbol}{m['total']:.2f} total ({m['category_label']})"
            )
        parts.append(f"\nFREQUENT MERCHANTS:\n" + "\n".join(lines))

    # Deep categories
    parts.append("\n=== DEEP ANALYSIS (LLM writes these) ===")
    if food_found:
        parts.append(f"\n[FOOD DELIVERY]\n{food_message}")
    else:
        parts.append("\n[FOOD DELIVERY]\nNo food delivery transactions found this month.")

    if coffee_found:
        parts.append(f"\n[COFFEE & CAFES]\n{coffee_message}")
    else:
        parts.append("\n[COFFEE & CAFES]\nNo coffee shop transactions found this month.")

    if grocery_found:
        parts.append(f"\n[GROCERIES]\n{grocery_message}")
    else:
        parts.append("\n[GROCERIES]\nNo supermarket transactions found this month.")

    if has_other and other_message:
        parts.append(f"\n[OTHER TOP SPENDS]\n{other_message}")

    # Savings
    total_saving = sum([
        food_analysis.get("realistic_saving", 0)    if food_analysis    else 0,
        coffee_analysis.get("realistic_saving", 0)  if coffee_analysis  else 0,
        grocery_analysis.get("realistic_saving", 0) if grocery_analysis else 0,
        (generic_advice.get("subscriptions") or {}).get("potential_saving", 0),
    ])

    if total_saving > 0:
        parts.append(
            f"\nSAVING: {symbol}{total_saving:.2f}/month | "
            f"{symbol}{total_saving*12:.2f}/year"
        )

    context = "\n".join(parts)

    # ── Pre-written verbatim sections ─────────────────────────────────────────
    # These are written by adviser.py and must not be changed by the LLM
    verbatim_sections = []

    subs = generic_advice.get("subscriptions")
    if subs and subs.get("advice_text"):
        verbatim_sections.append(
            f"## 📺 Subscriptions & Streaming\n{subs['advice_text']}"
        )

    gym = generic_advice.get("gym")
    if gym and gym.get("advice_text"):
        verbatim_sections.append(
            f"## 🏋️ Gym & Fitness\n{gym['advice_text']}"
        )

    transport = generic_advice.get("transport")
    if transport and transport.get("advice_text"):
        verbatim_sections.append(
            f"## 🚗 Transport\n{transport['advice_text']}"
        )

    fast_food = generic_advice.get("fast_food")
    if fast_food and fast_food.get("advice_text"):
        verbatim_sections.append(
            f"## 🍟 Fast Food & Takeaway\n{fast_food['advice_text']}"
        )

    transfers = generic_advice.get("transfers")
    if transfers and transfers.get("advice_text"):
        verbatim_sections.append(
            f"## 💸 Personal Transfers\n{transfers['advice_text']}"
        )

    verbatim_block = "\n\n".join(verbatim_sections)

    # ── System prompt ─────────────────────────────────────────────────────────
    system_prompt = f"""You are SpendSmart AI — a warm, honest personal finance assistant.

Write a personalised money report. All numbers are pre-calculated — never invent figures.

You will write ONLY these sections:
## 👋 Your Money Summary
## 🍔 Food Delivery
## ☕ Coffee & Daily Habits
## 🛒 Groceries
## 🔍 Your Actual Top Spends  (ONLY if other spending data is provided)
## 💰 Your Savings Opportunity  (ONLY if saving > {symbol}0)
## ✅ Your Actions This Week

After your sections, the following pre-written sections will be appended exactly as-is.
DO NOT write these yourself — they will be added automatically:
- Subscriptions & Streaming
- Gym & Fitness
- Transport
- Fast Food & Takeaway
- Personal Transfers

RULES:
- Sections WITH data: 3-4 sentences, use the exact numbers provided
- Sections WITHOUT data: exactly 1 sentence, positive framing
- If a frequent merchant appears 3+ times, name it specifically
- Actions section: only for categories with real calculated data
- Never invent, assume, or add information not in the data provided
- Never claim to know usage behaviour (gym attendance, streaming viewing)
- Tone: warm, specific, never preachy"""

    user_prompt = f"""Write the SpendSmart AI report using this data:

{context}

Write ONLY the sections listed above (Summary, Food Delivery, Coffee, Groceries, 
optionally Other Top Spends, optionally Savings, and Actions).

Do NOT write Gym, Transport, Subscriptions, Fast Food, or Transfers sections.
Those will be appended automatically after your output."""

    response = _get_client().chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ],
        temperature=0.4,
        max_tokens=1200,
    )

    llm_output = response.choices[0].message.content.strip()

    # ── Combine: LLM sections + verbatim sections ─────────────────────────────
    if verbatim_block:
        final_report = llm_output + "\n\n" + verbatim_block
    else:
        final_report = llm_output

    return final_report


def _no_data_report(country: str, summary: dict, symbol: str) -> str:
    total = summary.get("total_spent", 0)
    count = summary.get("total_transactions", 0)
    return f"""## 👋 Your Money Summary

Your statement was read — {count} transactions totalling {symbol}{total:.2f}. However, the merchant names did not match our recognised categories for {country}.

## 🔍 What to Do

Check the **All Transactions** tab to see every transaction. Your full spending history is there.

## ✅ Your Actions This Week

1. Review the All Transactions tab manually
2. Try exporting as CSV from your bank's website for better results
3. If using a photo, ensure merchant names are clearly visible"""


def generate_quick_summary(
    total_spent: float,
    total_saving: float,
    country: str,
) -> str:
    """2-sentence headline summary."""
    symbol = get_currency_symbol(country)

    if total_saving > 0:
        prompt = (
            f"Write a 2-sentence friendly summary for someone who spent "
            f"{symbol}{total_spent:.2f} this month and could save "
            f"{symbol}{total_saving:.2f} with small changes. "
            f"Be encouraging. Do not use 'however'."
        )
    else:
        prompt = (
            f"Write a 2-sentence friendly summary for someone who spent "
            f"{symbol}{total_spent:.2f} this month. "
            f"Be encouraging and suggest reviewing their report. "
            f"Do not use 'however'."
        )

    response = _get_client().chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "Write very short friendly financial summaries. Max 2 sentences."},
            {"role": "user",   "content": prompt},
        ],
        temperature=0.5,
        max_tokens=80,
    )
    return response.choices[0].message.content