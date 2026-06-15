# 💰 SpendSmart AI

**AI-powered personal finance assistant that tells you exactly where your money goes — and the smarter alternative for every spending habit.**

[🚀 Live Demo](#) · [📋 Report Example](#) · Built with Python, Groq (Llama 3.3 70B), Pandas, Plotly, Streamlit

---

## The Problem

Most people know roughly what they earn. Almost nobody knows exactly where it goes.

Budgeting apps show you charts. Generic AI gives you generic advice. Neither tells you that the chicken burger you ordered for £28 on Tuesday would cost £4.20 to make at home — or that you have 6 active subscriptions totalling £65/month and haven't opened 3 of them recently.

SpendSmart AI reads your actual bank statement and gives you specific, actionable answers in plain English. No charts to interpret. No advice that sounds the same for everyone.

---

## What It Does

Upload a CSV bank statement export from any major bank in the UK, US, or India. SpendSmart AI:

1. **Automatically detects your bank format** — handles different column names, date formats, and encodings across 19 banks
2. **Categorises every transaction** — food delivery, coffee, groceries, subscriptions, gym, transport, and more
3. **Deep-analyses your three biggest discretionary categories:**
   - 🍔 Food delivery: specific order count, average cost, home cooking alternative with nutrition context
   - ☕ Coffee and cafes: visit frequency, cost per cup, realistic switching saving
   - 🛒 Groceries: tier analysis (budget / mid-range / premium) with switching recommendations
4. **Gives honest generic advice** for categories where we only know payment data, not usage
5. **Generates a personalised plain English report** using Llama 3.3 70B via Groq
6. **Calculates your realistic monthly saving** — what you could save with small, specific changes

---

## Live Example Output

> *"You ordered food delivery 18 times this month (4.5x per week). Average order: £26.00. Total: £468. The same meal cooked at home costs approximately £4.50 — £21.50 less per meal. If you cooked at home just half the time, you would save £221 this month — £2,652 per year. Home-cooked meals typically have 30-50% less sodium and better portion control than delivery food."*

---

## Architecture

```
CSV Upload (any UK/US/India bank)
        │
        ▼
┌─────────────────┐
│   parser.py     │  Auto-detects bank format, normalises columns,
│                 │  parses dates, filters spending transactions only
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ categoriser.py  │  Matches descriptions against merchant lists
│                 │  in config.py → 9 categories deterministically
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────────┐
│   analyser.py          │    adviser.py           │
│   Deep analysis:       │    Honest generic:      │
│   - Food delivery      │    - Subscriptions      │
│   - Coffee             │    - Gym memberships    │
│   - Groceries          │    - Transport          │
│   (specific numbers)   │    (no fake usage data) │
└─────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────┐
│   report.py     │  Groq API (Llama 3.3 70B) synthesises
│                 │  pre-calculated numbers into plain English report
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    app.py       │  Streamlit UI — upload, progress,
│                 │  report, charts, transaction explorer
└─────────────────┘
```

**Key design decision:** The LLM never does the maths. Numbers come from Python (deterministic, accurate). The LLM only writes the plain English explanation around pre-calculated figures. This prevents hallucination of financial data.

---

## Honest Design Principle

SpendSmart AI only claims what bank data actually tells us.

A bank statement shows: what was paid, when, and to whom. It does NOT show whether a streaming service was watched, whether a gym was visited, or what was ordered from a delivery app.

So:
- **Deep analysis categories** (food delivery, coffee, groceries): specific personalised numbers
- **Generic advice categories** (subscriptions, gym, transport): honest general suggestions, no fake behavioural claims

This distinction between what we know and what we assume is a deliberate responsible AI design decision.

---

## Supported Banks

| 🇬🇧 UK | 🇺🇸 US | 🇮🇳 India |
|--------|--------|---------|
| Barclays | Chase | SBI |
| HSBC | Bank of America | HDFC |
| Monzo | Wells Fargo | ICICI |
| Starling | Citibank | Axis Bank |
| NatWest | Capital One | Kotak |
| Lloyds | | Paytm |
| Halifax | | |
| Santander | | |

Any bank exporting standard CSV format will also work via auto-detection.

---

## Tech Stack

| Component | Technology | Why |
|---|---|---|
| LLM | Groq API — Llama 3.3 70B | Free tier, fast, high quality |
| Data processing | Python, Pandas | Reliable, deterministic calculations |
| Visualisation | Plotly | Interactive charts |
| UI | Streamlit | Fast to build, easy to deploy |
| Config | Python dict (config.py) | Adding a country = one config block |
| Cost | £0 / $0 / ₹0 | Groq free tier is sufficient |

---

## Project Structure

```
SpendSmartAI/
├── app.py                    # Streamlit application (UI)
├── src/
│   ├── config.py             # Country configs: UK, US, India
│   ├── parser.py             # CSV parser — auto-detects bank format
│   ├── categoriser.py        # Transaction categorisation engine
│   ├── analyser.py           # Deep analysis: food, coffee, groceries
│   ├── adviser.py            # Generic advice: subscriptions, gym, transport
│   └── report.py             # LLM report generation via Groq
├── data/
│   └── sample_statements/    # Sample CSVs for UK, US, India
├── tests/
│   └── test_pipeline.py      # End-to-end pipeline test (6 checks)
├── requirements.txt
└── README.md
```

---

## Setup and Running

### Prerequisites
- Python 3.10+
- Free Groq API key from console.groq.com (no credit card required)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/SpendSmartAI
cd SpendSmartAI

# Create virtual environment
python -m venv venv

# Activate (Windows)
.\venv\Scripts\Activate.ps1

# Activate (Mac/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Add your Groq API key
echo "GROQ_API_KEY=your_key_here" > .env
```

### Run the pipeline test
```bash
python tests/test_pipeline.py
```
Expected: 6/6 tests passed.

### Start the app
```bash
streamlit run app.py
```
Opens at http://localhost:8501

---

## How to Export Your Bank Statement

### UK Banks
- **Monzo:** App → Account → Statements → Export → CSV
- **Barclays:** Online Banking → Accounts → View Statements → Export → CSV
- **HSBC:** Online Banking → My Accounts → View Statement → Download → CSV
- **NatWest:** Online Banking → Statements → Download → CSV

### US Banks
- **Chase:** chase.com → Accounts → Download Account Activity → CSV
- **Bank of America:** Online Banking → Download → CSV

### Indian Banks
- **HDFC:** NetBanking → Accounts → Download Account Statement → CSV
- **ICICI:** Internet Banking → Account Statement → Download CSV
- **SBI:** OnlineSBI → Account Summary → Download Statement

---

## Limitations (Honest)

- **Item-level detail:** We see "Deliveroo — £28.50" not what was ordered. The home cooking cost comparison uses country-average benchmarks, not your specific meal.
- **Usage data:** We cannot see if you watched Netflix or went to the gym. Generic advice is honest about this.
- **Scanned PDFs:** Does not support image-based PDFs. CSV export from your bank required.
- **Multi-currency accounts:** Analyses one currency per upload session.
- **Historical comparison:** Single-period analysis only. Month-over-month comparison is a planned V2 feature.

---

## Roadmap

**V1 (current):** UK, US, India · 3 deep categories · 4 generic categories · Groq LLM report · Streamlit UI

**V2 (planned):**
- Month-over-month comparison
- Personalised saving goals with timeline
- Canada, Australia support
- Weekly email digest export
- Dark mode UI

---

## For Interviewers

This project was built to demonstrate:

1. **End-to-end ML/AI system design** — from raw CSV to natural language output
2. **Responsible AI thinking** — the distinction between what data tells us vs what we assume
3. **Global extensibility** — adding a country requires one config block, zero code changes
4. **Production-minded architecture** — numbers computed deterministically, LLM used only for language
5. **User-first design** — built for non-specialists, not financial experts

Paired with **CreditGuard** (credit risk prediction with SHAP explainability), these two projects cover both sides of personal finance AI: the lender's risk model and the borrower's spending reality.

---

## Author

**Arfat Mushtaq**
MSc Artificial Intelligence for Business Intelligence — University of Leicester

[LinkedIn](#) · [GitHub](#) · arfatmushtaq62@gmail.com
