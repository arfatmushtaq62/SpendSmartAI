"""
config.py
---------
Country-specific configuration for SpendSmart AI.
Supports UK, US, and India.

IMPORTANT: Merchant lists should only contain names we are CERTAIN about.
Do NOT add vague keywords that could match unrelated businesses.
e.g. "circuit" removed from gym list because Circuit Go is a laundry app.
"""

COUNTRY_CONFIG = {

    # ══════════════════════════════════════════════════════
    # UNITED KINGDOM
    # ══════════════════════════════════════════════════════
    "UK": {
        "currency_symbol": "£",
        "currency_code": "GBP",
        "date_formats": ["%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%d %b %Y"],

        # Actual delivery platforms only — apps where food is delivered to you
        "delivery_platforms": [
            "deliveroo", "uber eats", "ubereats", "just eat", "justeat",
            "dominos", "domino", "pizza hut", "pizzahut",
            "papa john", "papajohn", "hungry house", "hungryhouse"
        ],

        # Walk-in fast food — NOT delivery
        "fast_food": [
            "mcdonald", "mcdonalds", "kfc", "nandos", "nando",
            "five guys", "burger king", "subway", "greggs",
            "leon", "itsu", "wasabi", "shake shack", "wingstop",
            "taco bell", "pret a manger", "pret"
        ],

        "coffee_chains": [
            "costa", "starbucks", "caffe nero", "caffè nero", "nero",
            "pod", "benugo", "boston tea party", "coffee#1",
            "the coffee house", "coffee republic"
        ],

        "budget_supermarkets": ["aldi", "lidl"],

        "mid_supermarkets": [
            "tesco", "asda", "sainsbury", "sainsburys",
            "morrisons", "morrison", "co-op", "coop", "co op",
            "iceland", "farmfoods", "spar"
        ],

        "premium_supermarkets": [
            "waitrose", "marks and spencer", "m&s", "m & s",
            "whole foods", "wholefoods", "booths"
        ],

        "streaming_services": [
            "netflix", "amazon prime", "disney", "disney+",
            "apple tv", "appletv", "now tv", "nowtv",
            "paramount", "discovery+", "dazn", "britbox",
            "youtube premium", "spotify", "apple music",
            "tidal", "deezer", "audible", "mubi"
        ],

        # Only include gym names we are CERTAIN are gyms
        # Do NOT include generic words like "fitness", "active", "circuit"
        # that could match unrelated apps or businesses
        "gym_merchants": [
            "puregym", "pure gym",
            "virgin active",
            "david lloyd",
            "gym group",
            "the gym group",
            "anytime fitness",
            "nuffield health",
            "snap fitness",
            "bannatyne",
            "everyone active",
            "jd gyms",
            "fitness first",
            "better leisure",
            "energie fitness",
            "xercise4less",
            "total fitness",
        ],

        "taxi_services": [
            "uber", "bolt", "addison lee", "gett",
            "free now", "freenow", "kapten"
        ],

        "benchmarks": {
            "home_cooking_meal_avg": 4.50,
            "home_coffee_avg": 0.25,
            "budget_supermarket_saving_pct": 35,
            "typical_delivery_markup_pct": 30,
            "avg_coffee_shop_price": 5.50,
            "avg_delivery_order": 26.00,
        },

        "bank_formats": {
            "barclays":  {"date": "Date", "description": "Memo",                     "amount": "Amount",           "date_format": "%d/%m/%Y"},
            "hsbc":      {"date": "Date", "description": "Description",               "amount": "Amount",           "date_format": "%d/%m/%Y"},
            "monzo":     {"date": "Date", "description": "Name",                      "amount": "Amount",           "date_format": "%d/%m/%Y"},
            "starling":  {"date": "Date", "description": "Counter Party",             "amount": "Amount (GBP)",     "date_format": "%d/%m/%Y"},
            "natwest":   {"date": "Date", "description": "Description",               "amount": "Value",            "date_format": "%d/%m/%Y"},
            "lloyds":    {"date": "Transaction Date", "description": "Transaction Description", "amount": "Debit Amount", "date_format": "%d/%m/%Y"},
            "halifax":   {"date": "Date", "description": "Transaction Description",   "amount": "Debit Amount",     "date_format": "%d/%m/%Y"},
            "santander": {"date": "Date", "description": "Description",               "amount": "Amount",           "date_format": "%d/%m/%Y"},
        },

        "generic_advice": {
            "subscriptions": (
                "You are paying for {count} subscription services totalling "
                "{symbol}{total:.2f}/month ({symbol}{annual:.2f}/year). "
                "Most people actively use 2-3 platforms. Review each one — "
                "if you have not opened it in the past few weeks, consider pausing it. "
                "Most platforms let you cancel and rejoin without losing history. "
                "Cutting just 2 unused services could save you around {symbol}{saving:.2f}/month."
            ),
            "transport": (
                "You spent {symbol}{total:.2f} on taxis and ride-hailing this month "
                "across {count} trips (average {symbol}{avg:.2f} per trip). "
                "For regular routes, compare this against a monthly bus or tram pass "
                "— most UK cities offer passes from £55-80/month unlimited. "
                "Evening and weekend rides are usually worth keeping for safety."
            ),
        }
    },

    # ══════════════════════════════════════════════════════
    # UNITED STATES
    # ══════════════════════════════════════════════════════
    "US": {
        "currency_symbol": "$",
        "currency_code": "USD",
        "date_formats": ["%m/%d/%Y", "%Y-%m-%d", "%m-%d-%Y"],

        "delivery_platforms": [
            "doordash", "door dash", "uber eats", "ubereats",
            "grubhub", "instacart", "postmates", "seamless",
            "dominos", "domino", "papa john", "pizza hut",
        ],

        "fast_food": [
            "mcdonald", "mcdonalds", "chick-fil-a", "chickfila",
            "chipotle", "taco bell", "wendy", "wendys",
            "burger king", "subway", "five guys", "shake shack",
            "popeyes", "in-n-out", "whataburger", "sonic"
        ],

        "coffee_chains": [
            "starbucks", "dunkin", "dunkin donuts", "dunkin'",
            "dutch bros", "peet", "peets coffee", "caribou coffee",
            "tim hortons", "panera", "biggby"
        ],

        "budget_supermarkets": [
            "aldi", "lidl", "walmart", "grocery outlet",
            "winco", "food4less", "save a lot"
        ],

        "mid_supermarkets": [
            "kroger", "safeway", "albertsons", "publix",
            "heb", "meijer", "giant", "stop and shop",
            "food lion", "harris teeter", "wegmans",
            "vons", "ralphs", "fred meyer"
        ],

        "premium_supermarkets": [
            "whole foods", "wholefoods", "trader joe",
            "trader joes", "sprouts", "fresh market", "bristol farms"
        ],

        "streaming_services": [
            "netflix", "hulu", "disney", "disney+",
            "hbo", "max", "peacock", "paramount+",
            "apple tv", "amazon prime", "youtube premium",
            "spotify", "apple music", "tidal",
            "audible", "kindle", "sirius", "siriusxm",
            "fubo", "sling", "philo", "discovery+"
        ],

        "gym_merchants": [
            "planet fitness",
            "la fitness",
            "24 hour fitness",
            "anytime fitness",
            "golds gym",
            "gold gym",
            "equinox",
            "crunch fitness",
            "lifetime fitness",
            "ymca",
            "snap fitness",
            "orangetheory",
            "orange theory",
            "f45",
            "pure barre",
            "solidcore",
        ],

        "taxi_services": [
            "uber", "lyft", "via", "curb", "alto", "wingz"
        ],

        "benchmarks": {
            "home_cooking_meal_avg": 4.00,
            "home_coffee_avg": 0.30,
            "budget_supermarket_saving_pct": 30,
            "typical_delivery_markup_pct": 35,
            "avg_coffee_shop_price": 6.50,
            "avg_delivery_order": 30.00,
        },

        "bank_formats": {
            "chase":           {"date": "Transaction Date", "description": "Description", "amount": "Amount",  "date_format": "%m/%d/%Y"},
            "bank_of_america": {"date": "Date",             "description": "Description", "amount": "Amount",  "date_format": "%m/%d/%Y"},
            "wells_fargo":     {"date": "Date",             "description": "Description", "amount": "Amount",  "date_format": "%m/%d/%Y"},
            "citibank":        {"date": "Date",             "description": "Description", "amount": "Debit",   "date_format": "%m/%d/%Y"},
            "capital_one":     {"date": "Transaction Date", "description": "Description", "amount": "Debit",   "date_format": "%m/%d/%Y"},
        },

        "generic_advice": {
            "subscriptions": (
                "You are paying for {count} subscription services totalling "
                "{symbol}{total:.2f}/month ({symbol}{annual:.2f}/year). "
                "Most people actively use 2-3 platforms. Review each one — "
                "if you have not opened it recently, pause it. "
                "Cutting 2 unused subscriptions could save {symbol}{saving:.2f}/month."
            ),
            "transport": (
                "You spent {symbol}{total:.2f} on Uber and Lyft this month across "
                "{count} trips (average {symbol}{avg:.2f} per trip). "
                "For regular commute routes, check whether a monthly transit pass "
                "saves money — most US city passes range $65-130/month unlimited. "
                "Rideshare is worth keeping for late nights and areas transit does not reach."
            ),
        }
    },

    # ══════════════════════════════════════════════════════
    # INDIA
    # ══════════════════════════════════════════════════════
    "India": {
        "currency_symbol": "₹",
        "currency_code": "INR",
        "date_formats": ["%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%d %b %Y"],

        "delivery_platforms": [
            "swiggy", "zomato", "dunzo", "magicpin",
            "faaso", "faasos", "freshmenu", "box8", "biryani by kilo"
        ],

        "fast_food": [
            "mcdonald", "mcdonalds", "kfc", "dominos", "domino",
            "pizza hut", "pizzahut", "burger king", "subway",
            "barbeque nation", "haldiram", "wow momo",
        ],

        "coffee_chains": [
            "cafe coffee day", "ccd", "starbucks", "costa",
            "barista", "third wave coffee", "blue tokai",
            "chaayos", "the coffee bean", "mccafe",
            "tim hortons", "lavazza"
        ],

        "budget_supermarkets": [
            "dmart", "d-mart", "d mart", "reliance smart",
            "more supermarket", "star bazaar", "big bazaar",
            "easyday", "vishal mega mart"
        ],

        "mid_supermarkets": [
            "reliance fresh", "food bazaar", "lulu hypermarket",
            "hypercity", "spar india", "smart bazaar", "spencer"
        ],

        "premium_supermarkets": [
            "godrej nature basket", "nature basket",
            "foodhall", "le marche", "dorabjees"
        ],

        "streaming_services": [
            "netflix", "amazon prime", "hotstar", "disney+ hotstar",
            "disney hotstar", "sony liv", "sonyliv", "zee5",
            "voot", "jiocinema", "jio cinema", "mxplayer", "mx player",
            "spotify", "gaana", "wynk", "jio saavn", "jiosaavn",
            "apple music", "youtube premium", "hungama",
            "erosnow", "eros now", "altbalaji", "alt balaji"
        ],

        "gym_merchants": [
            "cult fit", "cult.fit", "cultfit",
            "golds gym", "gold gym",
            "fitness first",
            "anytime fitness",
            "talwalkars",
            "snap fitness",
            "powerhouse gym",
            "true fit",
        ],

        "taxi_services": [
            "ola", "uber", "rapido", "meru",
            "blu smart", "blusmart", "namma yatri", "indrive"
        ],

        "benchmarks": {
            "home_cooking_meal_avg": 80.00,
            "home_coffee_avg": 15.00,
            "budget_supermarket_saving_pct": 25,
            "typical_delivery_markup_pct": 40,
            "avg_coffee_shop_price": 300.00,
            "avg_delivery_order": 400.00,
        },

        "bank_formats": {
            "sbi":   {"date": "Txn Date",        "description": "Description",         "amount": "Debit",                    "date_format": "%d/%m/%Y"},
            "hdfc":  {"date": "Date",             "description": "Narration",           "amount": "Withdrawal Amt.",          "date_format": "%d/%m/%Y"},
            "icici": {"date": "Transaction Date", "description": "Transaction Remarks", "amount": "Withdrawal Amount (INR )", "date_format": "%d/%m/%Y"},
            "axis":  {"date": "Tran Date",        "description": "PARTICULARS",         "amount": "DR",                       "date_format": "%d/%m/%Y"},
            "kotak": {"date": "Transaction Date", "description": "Description",         "amount": "Debit",                    "date_format": "%d/%m/%Y"},
            "paytm": {"date": "Date",             "description": "Description",         "amount": "Debit",                    "date_format": "%d/%m/%Y"},
        },

        "generic_advice": {
            "subscriptions": (
                "You are paying for {count} subscription services totalling "
                "{symbol}{total:.2f}/month ({symbol}{annual:.2f}/year). "
                "India has many affordable streaming options — consider whether "
                "you need both Hotstar and Netflix, or both Spotify and Gaana. "
                "Cutting 2 unused services could save {symbol}{saving:.2f}/month."
            ),
            "transport": (
                "You spent {symbol}{total:.2f} on Ola, Uber, and Rapido this month "
                "across {count} trips (average {symbol}{avg:.2f} per trip). "
                "For regular routes, metro passes in most Indian cities cost "
                "₹300-800/month for unlimited travel — worth comparing. "
                "Auto-rickshaws are often cheaper for short distances."
            ),
        }
    }
}


def get_config(country: str) -> dict:
    return COUNTRY_CONFIG.get(country, COUNTRY_CONFIG["UK"])

def get_all_countries() -> list:
    return list(COUNTRY_CONFIG.keys())

def get_currency_symbol(country: str) -> str:
    return get_config(country)["currency_symbol"]

def get_benchmarks(country: str) -> dict:
    return get_config(country)["benchmarks"]