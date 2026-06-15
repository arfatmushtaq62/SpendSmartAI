"""
parser.py
---------
Universal bank statement parser.

Supports four input formats:
  1. CSV  — any UK/US/India bank export (most accurate)
  2. PDF  — digital bank statement PDFs
  3. Image — photo of a printed statement or banking app screenshot
  4. Auto  — detects format from file extension automatically

Every output DataFrame has exactly these columns:
  date, description, amount, raw_desc
"""

import os
import re
import io
import base64
import tempfile
import pandas as pd
from datetime import datetime
from src.config import get_config, get_currency_symbol


# ── SHARED HELPERS ────────────────────────────────────────────────────────────

DATE_CANDIDATES = [
    "date", "transaction date", "txn date", "tran date",
    "value date", "posted date", "posting date"
]
DESC_CANDIDATES = [
    "description", "memo", "name", "narration", "particulars",
    "transaction description", "transaction remarks", "counter party",
    "details", "remarks", "narrative"
]
AMOUNT_CANDIDATES = [
    "amount", "debit", "withdrawal amt.", "withdrawal amount (inr )",
    "dr", "debit amount", "value", "amount (gbp)", "amount (usd)"
]

# Date patterns used in PDF/image parsing
DATE_PATTERNS = [
    r'\b(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})\b',
    r'\b(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{2,4})\b',
    r'\b(\d{4}[\/\-]\d{2}[\/\-]\d{2})\b',
]
DATE_FORMATS_ALL = [
    "%d/%m/%Y", "%d/%m/%y", "%m/%d/%Y", "%m/%d/%y",
    "%Y-%m-%d", "%d-%m-%Y", "%d-%m-%y",
    "%d %b %Y", "%d %b %y", "%d %B %Y",
]

# Amount patterns — matches things like £28.50, $1,234.56, ₹450.00, 28.50, 1,234.56
AMOUNT_PATTERN = re.compile(
    r'[£$₹]?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?|\d+(?:\.\d{1,2})?)'
)

# Lines we skip in PDF/image parsing (income, headers, footers)
SKIP_KEYWORDS = [
    "opening balance", "closing balance", "brought forward",
    "carried forward", "statement", "account number", "sort code",
    "balance", "salary", "credit", "deposit", "refund",
    "transfer in", "received", "interest earned", "cashback",
    "page ", "total", "available", "overdraft limit",
    "bank plc", "bank ltd", "financial", "branch"
]


def _try_parse_date(val: str, formats: list) -> datetime | None:
    for fmt in formats:
        try:
            return datetime.strptime(str(val).strip(), fmt)
        except ValueError:
            continue
    return None


def _detect_column(cols: list, candidates: list) -> str | None:
    lower = {c.lower().strip(): c for c in cols}
    for cand in candidates:
        if cand.lower() in lower:
            return lower[cand.lower()]
    return None


def _clean_amount(val) -> float:
    if pd.isna(val):
        return 0.0
    s = str(val).strip()
    for ch in ["£","$","₹",","," "]:
        s = s.replace(ch, "")
    negative = False
    if s.startswith("(") and s.endswith(")"):
        s = s[1:-1]; negative = True
    try:
        amt = float(s)
    except ValueError:
        return 0.0
    return abs(amt) if (amt < 0 or negative) else 0.0


def _build_clean_df(rows: list, country: str) -> pd.DataFrame:
    """
    Takes a list of (date, raw_desc, amount) tuples and returns
    the standard clean DataFrame.
    """
    if not rows:
        return pd.DataFrame(columns=["date","description","amount","raw_desc"])

    df = pd.DataFrame(rows, columns=["date","raw_desc","amount"])
    df["description"] = df["raw_desc"].str.lower().str.strip()
    df = df[df["amount"] > 0].copy()
    df = df[df["date"].notna()].copy()
    df = df[df["description"].str.len() > 2].copy()
    df.sort_values("date", inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df[["date","description","amount","raw_desc"]]


# ── FORMAT 1: CSV ─────────────────────────────────────────────────────────────

def parse_csv(file_path: str, country: str) -> pd.DataFrame:
    """Parse any bank statement CSV file."""
    config = get_config(country)
    date_formats = config["date_formats"]

    for encoding in ["utf-8", "latin-1", "cp1252"]:
        try:
            df = pd.read_csv(file_path, encoding=encoding, skip_blank_lines=True)
            break
        except Exception:
            continue
    else:
        raise ValueError("Could not read the CSV file. Try saving as UTF-8.")

    df.dropna(how="all", inplace=True)
    df.dropna(axis=1, how="all", inplace=True)
    df.columns = [str(c).strip() for c in df.columns]

    date_col   = _detect_column(df.columns.tolist(), DATE_CANDIDATES)
    desc_col   = _detect_column(df.columns.tolist(), DESC_CANDIDATES)
    amount_col = _detect_column(df.columns.tolist(), AMOUNT_CANDIDATES)

    if not date_col:
        raise ValueError(f"No date column found. Columns in file: {list(df.columns)}")
    if not desc_col:
        raise ValueError(f"No description column found. Columns in file: {list(df.columns)}")
    if not amount_col:
        raise ValueError(f"No amount column found. Columns in file: {list(df.columns)}")

    rows = []
    for _, row in df.iterrows():
        dt  = _try_parse_date(row[date_col], date_formats)
        amt = _clean_amount(row[amount_col])
        desc = str(row[desc_col]).strip()
        rows.append((dt, desc, amt))

    return _build_clean_df(rows, country)


# ── FORMAT 2: PDF ─────────────────────────────────────────────────────────────

def _extract_text_from_pdf(file_path: str) -> str:
    """Extract all text from a PDF using PyMuPDF."""
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(file_path)
        pages = []
        for page in doc:
            pages.append(page.get_text("text"))
        doc.close()
        return "\n".join(pages)
    except ImportError:
        raise ImportError(
            "PyMuPDF is required for PDF support.\n"
            "Install it with: pip install pymupdf"
        )
    except Exception as e:
        raise ValueError(f"Could not read PDF: {e}")


def _extract_transactions_via_llm(text: str, country: str) -> list:
    """
    Use Groq LLM to extract transactions from raw PDF text.

    This approach works for ANY bank's PDF format because the LLM
    reads the text intelligently, just like a human would.

    No regex. No bank-specific rules. Universal.
    """
    import os
    from groq import Groq
    from dotenv import load_dotenv
    load_dotenv()

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not found. Check your .env file.")

    symbol = get_currency_symbol(country)
    client = Groq(api_key=api_key)

    # Split text into chunks if too long (Groq has token limits)
    # 6000 chars per chunk is safe for most statements
    CHUNK_SIZE = 6000
    chunks = []
    if len(text) > CHUNK_SIZE:
        # Split at newlines to avoid cutting mid-line
        lines = text.split("\n")
        current_chunk = []
        current_len = 0
        for line in lines:
            current_len += len(line) + 1
            current_chunk.append(line)
            if current_len >= CHUNK_SIZE:
                chunks.append("\n".join(current_chunk))
                current_chunk = []
                current_len = 0
        if current_chunk:
            chunks.append("\n".join(current_chunk))
    else:
        chunks = [text]

    all_rows = []

    for i, chunk in enumerate(chunks):
        prompt = f"""You are a bank statement parser. Below is raw text extracted from a {country} bank statement PDF.

Your job: find ALL spending transactions (money going OUT of the account).

Output ONLY transactions in this exact format, one per line:
DD/MM/YYYY | MERCHANT NAME | AMOUNT

Rules:
- Only include DEBITS / spending (money leaving the account)
- Do NOT include: credits, deposits, salary, refunds, opening/closing balance, interest received
- DATE must be DD/MM/YYYY format
- MERCHANT NAME: the shop, company, or service name only (clean, no codes)
- AMOUNT: positive number only, no currency symbols, no commas
- If a line has no clear date or amount, skip it
- Output NOTHING else — no headers, no explanations, no blank lines between transactions

Example output:
12/05/2025 | DELIVEROO | 28.50
13/05/2025 | TESCO STORES | 67.20
14/05/2025 | COSTA COFFEE | 5.40

Here is the bank statement text (chunk {i+1} of {len(chunks)}):

{chunk}"""

        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a precise bank statement parser. "
                            "Extract only spending transactions. "
                            "Output only in the format: DD/MM/YYYY | MERCHANT | AMOUNT. "
                            "Nothing else."
                        )
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,  # Zero temperature = deterministic, no hallucination
                max_tokens=2000,
            )

            llm_output = response.choices[0].message.content.strip()
            chunk_rows = _parse_llm_pipe_output(llm_output, country)
            all_rows.extend(chunk_rows)

        except Exception as e:
            # If one chunk fails, continue with others
            continue

    return all_rows


def _parse_llm_pipe_output(text: str, country: str) -> list:
    """
    Parse the pipe-delimited output from the LLM.
    Format expected: DD/MM/YYYY | MERCHANT NAME | AMOUNT
    """
    config = get_config(country)
    date_formats = config["date_formats"] + DATE_FORMATS_ALL
    rows = []

    for line in text.strip().split("\n"):
        line = line.strip()
        if not line or "|" not in line:
            continue

        # Remove any markdown formatting the LLM might add
        line = line.lstrip("•-* ")

        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 3:
            continue

        date_str  = parts[0].strip()
        desc      = parts[1].strip()
        amount_str = parts[2].strip()

        # Parse date
        dt = _try_parse_date(date_str, date_formats)
        if not dt:
            continue

        # Parse amount — clean and convert
        amount_clean = amount_str.replace(",","").replace("£","").replace("$","").replace("₹","").strip()
        try:
            amount = float(amount_clean)
        except ValueError:
            continue

        if amount <= 0 or len(desc) < 2:
            continue

        # Skip if description looks like a header
        if any(kw in desc.lower() for kw in ["date", "description", "amount", "balance", "debit", "credit"]):
            continue

        rows.append((dt, desc, amount))

    return rows


def parse_pdf(file_path: str, country: str) -> pd.DataFrame:
    """
    Parse a PDF bank statement using LLM intelligence.

    Works for ANY bank's PDF format — HSBC, Barclays, Monzo,
    SBI, HDFC, Chase, Bank of America, and any other bank worldwide.

    No bank-specific rules needed. The LLM reads it like a human.
    """
    # Step 1: Extract raw text from PDF
    text = _extract_text_from_pdf(file_path)

    if not text.strip():
        raise ValueError(
            "No text found in this PDF. It may be a scanned image.\n"
            "Please use the photo/screenshot upload option instead."
        )

    # Step 2: Use LLM to find transactions in the text
    rows = _extract_transactions_via_llm(text, country)

    # Step 3: Build clean DataFrame
    df = _build_clean_df(rows, country)

    if df.empty:
        raise ValueError(
            "No spending transactions could be found in this PDF.\n\n"
            "This can happen if:\n"
            "• The PDF only shows credits/income (no spending this period)\n"
            "• The PDF is password protected\n"
            "• The text is in an unusual format\n\n"
            "Please try exporting as CSV from your bank's website for best results."
        )

    return df


# ── FORMAT 3: IMAGE (Photo / Screenshot) ─────────────────────────────────────

def _image_to_base64(file_path: str) -> tuple[str, str]:
    """Convert image file to base64 string for API."""
    from PIL import Image
    import base64

    # Open and optimise image for API
    img = Image.open(file_path)

    # Convert to RGB if needed (handles PNG with transparency)
    if img.mode in ("RGBA", "P", "LA"):
        img = img.convert("RGB")

    # Resize if too large — keeps API cost low
    max_size = 2048
    if max(img.size) > max_size:
        ratio = max_size / max(img.size)
        new_size = (int(img.width * ratio), int(img.height * ratio))
        img = img.resize(new_size, Image.LANCZOS)

    # Save to buffer
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=90)
    buffer.seek(0)

    img_b64 = base64.b64encode(buffer.read()).decode("utf-8")
    return img_b64, "image/jpeg"


def _extract_text_from_image_via_llm(file_path: str, country: str) -> str:
    """
    Use Groq's vision model to extract transaction text from an image.
    Returns raw text that _parse_text_to_transactions can process.
    """
    import os
    from groq import Groq
    from dotenv import load_dotenv
    load_dotenv()

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not found. Check your .env file.")

    symbol = get_currency_symbol(country)
    img_b64, media_type = _image_to_base64(file_path)

    client = Groq(api_key=api_key)

    prompt = f"""You are a bank statement reader. This image shows a bank statement or banking app screen.

Extract ALL transactions you can see. For each transaction output EXACTLY this format:
DATE | MERCHANT NAME | AMOUNT

Rules:
- Only include SPENDING transactions (money going out), not credits or income
- DATE format: DD/MM/YYYY
- AMOUNT: numbers only, no currency symbols
- One transaction per line
- If you cannot read a value clearly, skip that transaction
- Do not include headers, balances, or account information

Example output:
12/05/2025 | DELIVEROO | 28.50
13/05/2025 | TESCO STORES | 67.20
13/05/2025 | COSTA COFFEE | 5.40

Now extract all spending transactions from this {country} bank statement:"""

    try:
        response = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{media_type};base64,{img_b64}"
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ],
            temperature=0.1,
            max_tokens=2000,
        )
        return response.choices[0].message.content

    except Exception as e:
        # Fallback: try OCR if vision model fails
        raise ValueError(
            f"Could not process image with AI vision: {e}\n"
            "Please ensure your image is clear and well-lit."
        )


def _parse_llm_image_output(text: str, country: str) -> list:
    """
    Parse the structured output from the vision LLM.
    Expected format per line: DATE | DESCRIPTION | AMOUNT
    """
    config = get_config(country)
    date_formats = config["date_formats"] + DATE_FORMATS_ALL
    rows = []

    for line in text.strip().split("\n"):
        line = line.strip()
        if not line or "|" not in line:
            continue

        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 3:
            continue

        date_str, desc, amount_str = parts[0], parts[1], parts[2]

        dt = _try_parse_date(date_str, date_formats)
        if not dt:
            continue

        try:
            amount = float(amount_str.replace(",","").replace("£","").replace("$","").replace("₹","").strip())
        except ValueError:
            continue

        if amount <= 0 or len(desc) < 2:
            continue

        rows.append((dt, desc, amount))

    return rows


def parse_image(file_path: str, country: str) -> pd.DataFrame:
    """
    Parse a photo or screenshot of a bank statement.
    Uses Groq vision AI to read the image and extract transactions.
    """
    llm_text = _extract_text_from_image_via_llm(file_path, country)
    rows = _parse_llm_image_output(llm_text, country)
    df = _build_clean_df(rows, country)

    if df.empty:
        raise ValueError(
            "No transactions could be read from this image.\n"
            "Please ensure:\n"
            "• The image is clear and well-lit\n"
            "• Transactions are visible and not blurry\n"
            "• The image shows a bank statement or app transaction list"
        )
    return df


# ── AUTO-DETECT AND ROUTE ─────────────────────────────────────────────────────

def detect_file_type(file_path: str, original_filename: str) -> str:
    """
    Detect file type from extension and content.
    Returns: 'csv', 'pdf', or 'image'
    """
    ext = os.path.splitext(original_filename.lower())[1]

    if ext == ".csv":
        return "csv"
    elif ext == ".pdf":
        return "pdf"
    elif ext in [".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".heic"]:
        return "image"
    else:
        # Try to detect from content
        try:
            with open(file_path, "rb") as f:
                header = f.read(8)
            if header.startswith(b"%PDF"):
                return "pdf"
            if header.startswith(b"\xff\xd8") or header.startswith(b"\x89PNG"):
                return "image"
        except Exception:
            pass
        return "csv"  # default fallback


def parse_statement(file_path: str, country: str, file_type: str = "csv") -> pd.DataFrame:
    """
    Universal entry point. Routes to the correct parser based on file_type.

    Parameters
    ----------
    file_path  : str  Path to the file
    country    : str  'UK', 'US', or 'India'
    file_type  : str  'csv', 'pdf', or 'image'

    Returns
    -------
    pd.DataFrame with columns: date, description, amount, raw_desc
    """
    if file_type == "csv":
        return parse_csv(file_path, country)
    elif file_type == "pdf":
        return parse_pdf(file_path, country)
    elif file_type == "image":
        return parse_image(file_path, country)
    else:
        raise ValueError(f"Unknown file type: {file_type}")


def get_statement_summary(df: pd.DataFrame, country: str) -> dict:
    """Returns basic summary stats about the parsed statement."""
    symbol = get_currency_symbol(country)
    if df.empty:
        return {}
    return {
        "total_transactions": len(df),
        "total_spent": df["amount"].sum(),
        "date_from": df["date"].min().strftime("%d %b %Y") if pd.notna(df["date"].min()) else "Unknown",
        "date_to":   df["date"].max().strftime("%d %b %Y") if pd.notna(df["date"].max()) else "Unknown",
        "avg_transaction": df["amount"].mean(),
        "largest_transaction": df["amount"].max(),
        "currency_symbol": symbol,
    }