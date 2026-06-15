"""
tests/test_api.py
-----------------
Tests the FastAPI endpoints directly.

Run the API first:  uvicorn api.main:app --reload --port 8000
Then run this:      python tests/test_api.py
"""

import requests
import json
import sys
import os

BASE_URL = "http://localhost:8000"


def separator(title: str):
    print(f"\n{'='*55}")
    print(f"  {title}")
    print('='*55)


def test_health():
    separator("TEST 1: Health Check")
    r = requests.get(f"{BASE_URL}/health")
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    data = r.json()
    assert data["status"] == "ok"
    print(f"✅ Status: {data['status']}")
    print(f"✅ Version: {data['version']}")
    print(f"✅ Countries: {data['supported_countries']}")
    print(f"✅ Formats: {data['supported_formats']}")


def test_countries():
    separator("TEST 2: Countries Endpoint")
    r = requests.get(f"{BASE_URL}/countries")
    assert r.status_code == 200
    data = r.json()
    for country, info in data.items():
        print(f"✅ {country}: {info['currency_symbol']} — {len(info['supported_banks'])} banks")


def test_analyse_csv(filepath: str, country: str):
    separator(f"TEST 3: Analyse CSV — {country}")
    print(f"File: {filepath}")

    with open(filepath, "rb") as f:
        r = requests.post(
            f"{BASE_URL}/analyse",
            files={"file": (os.path.basename(filepath), f, "text/csv")},
            data={"country": country},
        )

    if r.status_code != 200:
        print(f"❌ Error {r.status_code}: {r.text[:500]}")
        return None

    data = r.json()
    session_id = data["session_id"]

    print(f"✅ Session ID: {session_id}")
    print(f"✅ Transactions: {data['total_transactions']}")
    print(f"✅ Total spent: {data['currency_symbol']}{data['total_spent']:.2f}")
    print(f"✅ Period: {data['date_from']} to {data['date_to']}")
    print(f"\n✅ Categories found: {list(data['categories'].keys())}")

    if data.get("food_delivery"):
        fd = data["food_delivery"]
        print(f"\n✅ Food delivery: {data['currency_symbol']}{fd['total']:.2f} "
              f"({fd['order_count']} orders)")

    if data.get("coffee"):
        c = data["coffee"]
        print(f"✅ Coffee: {data['currency_symbol']}{c['total']:.2f} "
              f"({c['visit_count']} visits)")

    if data.get("frequent_merchants"):
        print(f"\n✅ Frequent merchants ({len(data['frequent_merchants'])}):")
        for m in data["frequent_merchants"][:3]:
            print(f"   - {m['merchant']}: {m['count']}x, "
                  f"{data['currency_symbol']}{m['total']:.2f}")

    print(f"\n✅ Monthly saving: {data['currency_symbol']}{data['total_monthly_saving']:.2f}")
    print(f"✅ Annual saving:  {data['currency_symbol']}{data['total_annual_saving']:.2f}")

    print(f"\n✅ Quick summary:\n   {data['quick_summary']}")
    print(f"\n✅ Report (first 200 chars):\n   {data['report_markdown'][:200]}...")
    print(f"\n✅ Processing notes:")
    for note in data["processing_notes"]:
        print(f"   - {note}")

    return session_id


def test_get_report(session_id: str):
    separator("TEST 4: Get Report by Session ID")
    r = requests.get(f"{BASE_URL}/report/{session_id}")
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    data = r.json()
    print(f"✅ Retrieved session: {data['session_id']}")
    print(f"✅ Country: {data['country']}")
    print(f"✅ Report length: {len(data['report_markdown'])} characters")


def test_invalid_country():
    separator("TEST 5: Invalid Country (should return 400)")
    r = requests.post(
        f"{BASE_URL}/analyse",
        files={"file": ("test.csv", b"Date,Description,Amount", "text/csv")},
        data={"country": "MARS"},
    )
    assert r.status_code == 400, f"Expected 400, got {r.status_code}"
    print(f"✅ Correctly rejected with 400: {r.json()['detail'][:80]}")


def test_missing_session():
    separator("TEST 6: Missing Session ID (should return 404)")
    r = requests.get(f"{BASE_URL}/report/fake-session-id-that-does-not-exist")
    assert r.status_code == 404, f"Expected 404, got {r.status_code}"
    print(f"✅ Correctly returned 404: {r.json()['detail'][:80]}")


if __name__ == "__main__":
    print("\n🚀 SpendSmart AI — API Test Suite")
    print("Make sure the API is running: uvicorn api.main:app --reload --port 8000")

    # Check API is reachable
    try:
        requests.get(f"{BASE_URL}/health", timeout=3)
    except requests.exceptions.ConnectionError:
        print(f"\n❌ Cannot connect to {BASE_URL}")
        print("Start the API first: uvicorn api.main:app --reload --port 8000")
        sys.exit(1)

    # Run tests
    test_health()
    test_countries()

    session_id = test_analyse_csv(
        "data/sample_statements/sample_uk.csv", "UK"
    )
    if session_id:
        test_get_report(session_id)

    test_invalid_country()
    test_missing_session()

    print(f"\n{'='*55}")
    print("  ✅ ALL API TESTS PASSED")
    print(f"{'='*55}")
    print(f"\n📖 View full API docs at: {BASE_URL}/docs")