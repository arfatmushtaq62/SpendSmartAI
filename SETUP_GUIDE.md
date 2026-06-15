# SpendSmart AI — Complete Setup Guide

Follow this step by step. Do not skip steps.
Every command is written for Windows PowerShell.

---

## STEP 1: Create the project folder

Open PowerShell. Run:

```powershell
cd Desktop
mkdir SpendSmartAI
cd SpendSmartAI
```

---

## STEP 2: Create and activate virtual environment

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

If you get an execution policy error:
```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```
Type Y, press Enter, then retry the activate command.

You should see (venv) at the start of your prompt.

---

## STEP 3: Get your free Groq API key

1. Go to console.groq.com
2. Sign up (Google login, no credit card needed)
3. Click API Keys in the left sidebar
4. Click Create API Key
5. Name it SpendSmartAI
6. COPY the key immediately — it starts with gsk_
7. Keep it in Notepad temporarily

---

## STEP 4: Open in VS Code

```powershell
code .
```

Open the terminal inside VS Code with Ctrl + ~
Confirm (venv) is showing in the terminal.

---

## STEP 5: Install packages

```powershell
pip install groq python-dotenv pandas streamlit plotly openpyxl
```

Wait for "Successfully installed..." to appear.

---

## STEP 6: Download the project files

Copy all files from the repository into your SpendSmartAI folder.
The structure should look like this:

```
SpendSmartAI/
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── .env                    ← you create this
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── parser.py
│   ├── categoriser.py
│   ├── analyser.py
│   ├── adviser.py
│   └── report.py
├── data/
│   └── sample_statements/
│       ├── sample_uk.csv
│       ├── sample_us.csv
│       └── sample_india.csv
└── tests/
    └── test_pipeline.py
```

---

## STEP 7: Create your .env file

In VS Code, create a new file called .env in the root folder.
Add this line, replacing with your actual key:

```
GROQ_API_KEY=gsk_your_actual_key_here
```

No quotes. No spaces around the = sign. Save.

---

## STEP 8: Run the pipeline test

```powershell
python tests/test_pipeline.py
```

Expected output:
```
[1/6] Testing config system...       ✅
[2/6] Testing CSV parser...          ✅
[3/6] Testing categoriser...         ✅
[4/6] Testing deep analysis...       ✅
[5/6] Testing adviser...             ✅
[6/6] Testing Groq API connection... ✅
ALL 6 TESTS PASSED
```

If any test fails, read the error message and check:
- Is (venv) showing in your terminal?
- Is your .env file in the root folder (not inside src/)?
- Is your Groq API key correct?

---

## STEP 9: Run the app

```powershell
streamlit run app.py
```

Your browser opens automatically at http://localhost:8501

---

## STEP 10: Test with sample data

1. In the app, select your country (UK, US, or India)
2. Upload the matching sample CSV from data/sample_statements/
3. Click Analyse My Statement
4. Wait ~30 seconds for the report to generate
5. Review the three tabs: Report, Charts, Transactions

---

## STEP 11: Test with your real bank statement

1. Log into your bank's website or app
2. Export your statement as CSV (last 1-3 months recommended)
3. Upload it to the app
4. Select your correct country
5. Click Analyse

---

## STEP 12: Deploy to Streamlit Community Cloud (free)

1. Push your project to GitHub (do NOT include .env file — it is in .gitignore)
2. Go to share.streamlit.io
3. Sign in with GitHub
4. Click New App
5. Select your repository and set Main file path to: app.py
6. In Advanced settings → Secrets, add:
   ```
   GROQ_API_KEY = "your_groq_api_key_here"
   ```
7. Click Deploy

Your app will be live at: https://your-app-name.streamlit.app

This is the URL you put on your CV and LinkedIn.

---

## Common Errors and Fixes

| Error | Fix |
|-------|-----|
| ModuleNotFoundError: groq | Run pip install groq with venv active |
| GROQ_API_KEY not found | Check .env is in root, not inside src/ |
| AuthenticationError | Re-copy API key from console.groq.com |
| No spending transactions found | Check CSV has negative amounts for spending |
| Could not find a date column | Check CSV column names match expected format |
| python not recognised | Use py instead of python |
| Streamlit not recognised | Run pip install streamlit |

---

## How to Add a New Country (Future)

1. Open src/config.py
2. Copy the UK block
3. Replace all merchant names, benchmarks, and bank formats for the new country
4. Add the new country key to COUNTRY_CONFIG
5. That is it — no other file needs to change

---

## File Descriptions

| File | What it does |
|------|-------------|
| app.py | Streamlit UI — the entire frontend |
| src/config.py | Country configs: merchants, benchmarks, bank formats |
| src/parser.py | Reads CSV, auto-detects bank format, normalises data |
| src/categoriser.py | Matches transactions to categories using merchant lists |
| src/analyser.py | Deep analysis: food delivery, coffee, groceries |
| src/adviser.py | Generic advice: subscriptions, gym, transport |
| src/report.py | LLM report generation using Groq API |
| tests/test_pipeline.py | End-to-end test of all 6 pipeline stages |

---

## Running the FastAPI Backend

### Install FastAPI packages

```powershell
pip install fastapi uvicorn python-multipart
```

### Start the API server

Open a **second** VS Code terminal (click the + icon in the terminal panel).
Keep Streamlit running in the first terminal.

In the second terminal:

```powershell
uvicorn api.main:app --reload --port 8000
```

You now have both running:
- Streamlit UI:  http://localhost:8501
- FastAPI:       http://localhost:8000
- API Docs:      http://localhost:8000/docs  ← interactive documentation

### Test the API

In a third terminal:

```powershell
pip install requests
python tests/test_api.py
```

Expected: ALL API TESTS PASSED

### Using the API Docs

Go to http://localhost:8000/docs in your browser.

FastAPI auto-generates beautiful interactive documentation.
You can test every endpoint directly from the browser — no Postman needed.

Click "POST /analyse" → "Try it out" → upload a sample CSV → Execute.
You will see the full JSON response.

### Example API call (curl)

```bash
curl -X POST http://localhost:8000/analyse \
  -F "file=@data/sample_statements/sample_uk.csv" \
  -F "country=UK"
```

### Example API call (Python)

```python
import requests

with open("data/sample_statements/sample_uk.csv", "rb") as f:
    response = requests.post(
        "http://localhost:8000/analyse",
        files={"file": ("statement.csv", f, "text/csv")},
        data={"country": "UK"},
    )

data = response.json()
print(f"Total spent: {data['currency_symbol']}{data['total_spent']}")
print(f"Monthly saving: {data['currency_symbol']}{data['total_monthly_saving']}")
print(data['report_markdown'])
```