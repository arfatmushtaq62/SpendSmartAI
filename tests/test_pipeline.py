"""
test_pipeline.py
----------------
Full end-to-end test of the SpendSmart AI pipeline.
Tests: config, parser, categoriser, analyser, adviser, and LLM connection.

Run with: python tests/test_pipeline.py
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

print("=" * 60)
print("  SpendSmart AI — Pipeline Test")
print("=" * 60)

# ── TEST 1: Config ────────────────────────────────────────────────────────────
print("\n[1/6] Testing config system...")
from src.config import get_config, get_all_countries, get_currency_symbol

countries = get_all_countries()
assert "UK" in countries and "US" in countries and "India" in countries, \
    "Missing countries in config"

for country in countries:
    symbol = get_currency_symbol(country)
    config = get_config(country)
    assert symbol, f"No currency symbol for {country}"
    assert len(config["delivery_platforms"]) > 0, f"No delivery platforms for {country}"
    assert len(config["coffee_chains"]) > 0, f"No coffee chains for {country}"
    print(f"  ✅ {country}: {symbol} · {len(config['delivery_platforms'])} delivery platforms")

print("  ✅ Config test passed")


# ── TEST 2: Parser ────────────────────────────────────────────────────────────
print("\n[2/6] Testing CSV parser...")
from src.parser import parse_statement, get_statement_summary

test_files = {
    "UK":    "data/sample_statements/sample_uk.csv",
    "US":    "data/sample_statements/sample_us.csv",
    "India": "data/sample_statements/sample_india.csv",
}

for country, path in test_files.items():
    assert os.path.exists(path), f"Sample file not found: {path}"
    df = parse_statement(path, country)
    assert not df.empty, f"Parser returned empty DataFrame for {country}"
    assert "date" in df.columns, "Missing date column"
    assert "description" in df.columns, "Missing description column"
    assert "amount" in df.columns, "Missing amount column"
    assert (df["amount"] > 0).all(), "All amounts should be positive (spending only)"
    symbol = get_currency_symbol(country)
    summary = get_statement_summary(df, country)
    print(f"  ✅ {country}: {len(df)} transactions · {symbol}{summary['total_spent']:.2f} total")

print("  ✅ Parser test passed")


# ── TEST 3: Categoriser ───────────────────────────────────────────────────────
print("\n[3/6] Testing categoriser...")
from src.categoriser import categorise_all, get_category_totals

for country, path in test_files.items():
    df = parse_statement(path, country)
    df = categorise_all(df, country)
    assert "category" in df.columns, "Missing category column"
    assert "category_label" in df.columns, "Missing category_label column"

    cat_totals = get_category_totals(df)
    categories_found = list(cat_totals.keys())
    symbol = get_currency_symbol(country)

    print(f"  ✅ {country}: {len(categories_found)} categories detected: {categories_found}")

    # Verify food delivery is detected in each country
    assert "food_delivery" in categories_found, \
        f"Food delivery not detected for {country} — check merchant list in config"

print("  ✅ Categoriser test passed")


# ── TEST 4: Analyser ──────────────────────────────────────────────────────────
print("\n[4/6] Testing deep analysis engine...")
from src.analyser import (
    analyse_food_delivery, build_food_delivery_message,
    analyse_coffee, build_coffee_message,
    analyse_groceries, build_groceries_message,
)

for country, path in test_files.items():
    df = parse_statement(path, country)
    df = categorise_all(df, country)
    symbol = get_currency_symbol(country)

    food = analyse_food_delivery(df, country)
    coffee = analyse_coffee(df, country)
    groceries = analyse_groceries(df, country)

    if food:
        msg = build_food_delivery_message(food)
        assert len(msg) > 50, "Food message too short"
        print(f"  ✅ {country} food: {symbol}{food['total_spent']:.2f} · saving {symbol}{food['realistic_saving']:.2f}")

    if coffee:
        msg = build_coffee_message(coffee)
        assert len(msg) > 50, "Coffee message too short"
        print(f"  ✅ {country} coffee: {symbol}{coffee['total_spent']:.2f} · saving {symbol}{coffee['realistic_saving']:.2f}")

    if groceries:
        msg = build_groceries_message(groceries)
        assert len(msg) > 50, "Groceries message too short"
        print(f"  ✅ {country} groceries: {symbol}{groceries['total_spent']:.2f} · tier: {groceries['primary_tier']}")

print("  ✅ Analyser test passed")


# ── TEST 5: Adviser ───────────────────────────────────────────────────────────
print("\n[5/6] Testing generic advice engine...")
from src.adviser import get_all_generic_advice

for country, path in test_files.items():
    df = parse_statement(path, country)
    df = categorise_all(df, country)
    advice = get_all_generic_advice(df, country)

    assert isinstance(advice, dict), "Advice should be a dict"
    assert "subscriptions" in advice, "Missing subscriptions advice"
    assert "gym" in advice, "Missing gym advice"
    assert "transport" in advice, "Missing transport advice"

    for key, val in advice.items():
        if val:
            assert "advice_text" in val, f"Missing advice_text for {key}"

    print(f"  ✅ {country}: {sum(1 for v in advice.values() if v)} advice sections generated")

print("  ✅ Adviser test passed")


# ── TEST 6: Groq API Connection ───────────────────────────────────────────────
print("\n[6/6] Testing Groq API connection...")
from groq import Groq

api_key = os.getenv("GROQ_API_KEY")
assert api_key, "GROQ_API_KEY not found in .env file"

client = Groq(api_key=api_key)
response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[
        {"role": "system", "content": "You are SpendSmart AI. Be concise."},
        {"role": "user", "content": "In one sentence, what do you help people with?"}
    ],
    temperature=0.3,
    max_tokens=60,
)

answer = response.choices[0].message.content
tokens = response.usage.total_tokens
assert len(answer) > 10, "LLM response too short"
print(f"  ✅ LLM response: {answer}")
print(f"  ✅ Tokens used: {tokens}")

print("\n" + "=" * 60)
print("  ✅ ALL 6 TESTS PASSED")
print("  SpendSmart AI is ready to run.")
print("  Start the app with: streamlit run app.py")
print("=" * 60)
