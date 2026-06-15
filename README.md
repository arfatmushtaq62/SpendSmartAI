---
title: SpendSmart AI
emoji: 💰
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
---

# 💰 SpendSmart AI

**AI-powered personal finance assistant that tells you exactly where your money goes — and the smarter alternative for every spending habit.**

[🚀 Live App](https://arfatmushtaq62-spendsmartai.hf.space) · [📖 API Docs](https://arfatmushtaq62-spendsmartai.hf.space/docs) · [🤗 Hugging Face](https://huggingface.co/spaces/arfatmushtaq62/SpendSmartAI)

Built with Python · FastAPI · Groq (Llama 3.3 70B) · Pandas · Chart.js · Docker

---

## The Problem

Most people know roughly what they earn. Almost nobody knows exactly where it goes.

Budgeting apps show you charts. Generic AI gives you generic advice. Neither tells you that the chicken burger you ordered for £28 on Tuesday would cost £4.20 to make at home — or that you have 6 active subscriptions totalling £65/month you've barely used.

SpendSmart AI reads your actual bank statement and gives you specific, actionable answers in plain English. No charts to interpret. No advice that sounds the same for everyone.

---

## Live Demo

🚀 **[https://arfatmushtaq62-spendsmartai.hf.space](https://arfatmushtaq62-spendsmartai.hf.space)**

Upload any of the sample statements in `data/sample_statements/` to try it instantly — no real bank data needed.

---

## What It Does

Upload a bank statement (CSV, PDF, photo, or screenshot) from any major UK, US, or Indian bank. SpendSmart AI:

1. **Auto-detects your bank format** — handles different column names, date formats, and encodings across 19 banks
2. **Two-pass categorisation** — fast keyword matching (Pass 1) + LLM smart re-categorisation of unknown local merchants like "Tea Time" or "Raj's Kitchen" (Pass 2)
3. **Deep-analyses three key categories:**
   - 🍔 Food delivery — order count, average cost, home cooking alternative with nutrition context
   - ☕ Coffee and cafes — visit frequency, home coffee saving calculation
   - 🛒 Groceries — budget vs premium tier analysis with switching recommendations
4. **Honest generic advice** for categories where we only know payment data, not usage (gym, subscriptions, transport)
5. **Frequent merchant detection** — calls out merchants you visit 3+ times by name
6. **Personal transfer detection** — separates payments to individuals from merchant spending
7. **AI-generated plain English report** using Llama 3.3 70B via Groq
8. **PDF download** of your full report
9. **REST API** with full interactive documentation at `/docs`

---

## Live Example Output

> *"You visited Tea Time 8 times this month — at £8.25 average, that's £66 just on this one cafe. Making coffee at home for 60% of those visits would save approximately £23 this month — £276 per year."*

---

## Architecture

```
Bank Statement (CSV / PDF / Photo / Screenshot)
        │
        ▼
┌─────────────────┐
│   parser.py     │  Auto-detects format, normalises columns,
│                 │  LLM vision for images, PyMuPDF for PDFs
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────────┐
│           categoriser.py (Two-pass)             │
│  Pass 1: keyword matching (fast, free)          │
│  Pass 2: LLM re-categorises unknown merchants   │
│          "Tea Time" → coffee ✅                  │
│          "Circuit Go" → uncertain → honest msg  │
└────────┬────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────┐
│   analyser.py          │    adviser.py           │
│   Deep analysis:       │    Honest generic:      │
│   - Food delivery      │    - Subscriptions      │
│   - Coffee             │    - Gym & fitness      │
│   - Groceries          │    - Transport          │
│   (real numbers)       │    (no fake claims)     │
└─────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────┐
│   report.py     │  LLM writes narrative sections only.
│                 │  Gym/transport/subscriptions appended
│                 │  verbatim — LLM cannot add assumptions.
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  api/main.py    │  FastAPI REST backend — serves HTML
│  templates/     │  frontend + JSON API endpoints
│  index.html     │
└─────────────────┘
```

**Key design decisions:**

- **LLM never does the maths** — numbers come from Python (deterministic). LLM only writes language.
- **Verbatim sections for uncertain categories** — gym/transport advice is pre-written by `adviser.py` and appended directly. The LLM cannot rewrite it and add assumptions like "if attendance has dropped."
- **Honesty principle** — we only claim what bank data tells us. We never say "you haven't used Netflix" because we cannot know that from a payment.

---

## Honest Design Principle

A bank statement tells us: what was paid, when, and to whom. Nothing else.

| Category | What we know | What we say |
|---|---|---|
| Food delivery | Amount, frequency, platform | Specific numbers + home cooking cost |
| Coffee | Amount, visit count | Specific saving calculation |
| Groceries | Supermarket tier | Switching recommendation |
| Gym | Payment amount, merchant name | "We've categorised this as gym — but only you know if you're attending" |
| Subscriptions | Monthly charges | Generic rationalisation advice |
| Transport | Trip count, total spend | Compare against public transport |

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

Any bank exporting standard CSV also works via auto-detection.

---

## Tech Stack

| Component | Technology | Why |
|---|---|---|
| Backend | FastAPI | REST API + serves frontend from one server |
| LLM | Groq — Llama 3.3 70B | Free tier, fast inference |
| PDF parsing | PyMuPDF | Extracts text from digital PDFs |
| Image parsing | Groq vision | Reads photos and screenshots |
| Data processing | Python, Pandas | Deterministic calculations |
| Charts | Chart.js | Lightweight, no framework needed |
| Frontend | HTML/CSS/JS | No framework — pure web standards |
| Deployment | Docker + Hugging Face Spaces | Free, public, permanent URL |
| Cost | £0 / $0 / ₹0 | Entirely free stack |

---

## Project Structure

```
SpendSmartAI/
├── api/
│   └── main.py               # FastAPI app — serves frontend + REST API
├── src/
│   ├── config.py             # Country configs: UK, US, India
│   ├── parser.py             # Universal parser: CSV, PDF, image
│   ├── categoriser.py        # Two-pass categorisation engine
│   ├── analyser.py           # Deep analysis: food, coffee, groceries
│   ├── adviser.py            # Honest generic advice engine
│   └── report.py             # LLM report generation via Groq
├── templates/
│   └── index.html            # Complete frontend (HTML/CSS/JS)
├── static/                   # Static assets
├── data/
│   └── sample_statements/    # Sample CSVs: UK, US, India
├── tests/
│   ├── test_pipeline.py      # End-to-end pipeline test
│   └── test_api.py           # API endpoint tests
├── Dockerfile                # Docker config for Hugging Face
├── requirements.txt
└── README.md
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/analyse` | Upload statement, get full JSON analysis |
| `GET` | `/report/{session_id}` | Retrieve previous analysis |
| `GET` | `/countries` | List supported countries and banks |
| `GET` | `/health` | Health check |
| `GET` | `/docs` | Interactive API documentation |

Full interactive docs: **[https://arfatmushtaq62-spendsmartai.hf.space/docs](https://arfatmushtaq62-spendsmartai.hf.space/docs)**

---

## Local Setup

### Prerequisites
- Python 3.10+
- Free Groq API key from [console.groq.com](https://console.groq.com) (no credit card)

### Installation

```bash
git clone https://github.com/arfatmushtaq62/SpendSmartAI
cd SpendSmartAI

python -m venv venv

# Windows
.\venv\Scripts\Activate.ps1

# Mac/Linux
source venv/bin/activate

pip install -r requirements.txt

echo "GROQ_API_KEY=your_key_here" > .env
```

### Run

```bash
uvicorn api.main:app --reload --port 8000
```

Open: [http://localhost:8000](http://localhost:8000)
API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

### Test

```bash
python tests/test_pipeline.py
```

---

## How to Export Your Bank Statement

### 🇬🇧 UK
- **Monzo** → App → Account → Statements → Export → CSV
- **Barclays** → Online Banking → Accounts → View Statements → Export → CSV
- **HSBC** → Online Banking → My Accounts → View Statement → Download → CSV
- **NatWest** → Online Banking → Statements → Download → CSV
- **Lloyds / Halifax** → Online Banking → View Statements → Export → CSV

### 🇺🇸 US
- **Chase** → chase.com → Accounts → Download Account Activity → CSV
- **Bank of America** → Online Banking → Accounts → Download → CSV
- **Wells Fargo** → wellsfargo.com → Account Activity → Download → CSV

### 🇮🇳 India
- **HDFC** → NetBanking → Accounts → Download Account Statement → CSV
- **ICICI** → Internet Banking → Account Statement → Download CSV
- **SBI** → OnlineSBI → Account Summary → Download Statement

---

## Limitations

- **Item-level detail** — we see "Deliveroo — £28.50" not what was ordered. Home cooking comparisons use country-average benchmarks.
- **Usage data** — we cannot see if you watched Netflix or attended the gym. Generic advice is honest about this.
- **Scanned PDFs** — image-based PDFs require the photo upload path, not PDF upload.
- **Multi-currency** — analyses one currency per session.

---

## Roadmap

**V1 (current):** UK · US · India · CSV/PDF/photo · FastAPI · Docker deployment

**V2 (planned):**
- Month-over-month comparison
- Personalised saving goals with timeline
- Canada, Australia support
- Recurring payment detection
- Weekly summary email export

---

## For Interviewers

This project demonstrates:

1. **Full-stack AI system** — file parsing → LLM categorisation → analysis → REST API → frontend
2. **Responsible AI design** — verbatim sections prevent LLM from adding unverifiable claims
3. **Global extensibility** — adding a new country = one config block, zero code changes
4. **Production architecture** — deterministic Python for numbers, LLM only for language
5. **API-first thinking** — FastAPI backend with full OpenAPI documentation

Paired with **CreditGuard** (ML credit risk prediction with SHAP explainability for GDPR Article 22 compliance), these projects cover both sides of personal finance AI: the lender's risk model and the borrower's spending reality.

---

## Author

**Arfat Mushtaq**
MSc Artificial Intelligence for Business Intelligence — University of Leicester, UK

[💼 LinkedIn](https://www.linkedin.com/in/arfat-mushtaq-0b756824a/) · [🐙 GitHub](https://github.com/arfatmushtaq62) · [✉️ arfatmushtaq62@gmail.com](mailto:arfatmushtaq62@gmail.com)