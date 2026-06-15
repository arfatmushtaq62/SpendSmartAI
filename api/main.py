"""
api/main.py
-----------
SpendSmart AI — FastAPI Backend + Frontend Server

Serves the HTML frontend AND the REST API from the same server.

Run: uvicorn api.main:app --reload --port 8000
Open: http://localhost:8000
API docs: http://localhost:8000/docs
"""

import os
import uuid
import tempfile
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from src.config import get_all_countries, get_currency_symbol
from src.parser import parse_statement, get_statement_summary
from src.categoriser import (
    categorise_all, get_category_totals,
    get_frequent_merchants, get_spending_by_day_of_week
)
from src.analyser import (
    analyse_food_delivery, build_food_delivery_message,
    analyse_coffee, build_coffee_message,
    analyse_groceries, build_groceries_message,
    analyse_other_spending, build_other_spending_message,
)
from src.adviser import get_all_generic_advice
from src.report import generate_report, generate_quick_summary


# ── App setup ─────────────────────────────────────────────────────────────────

app = FastAPI(
    title="SpendSmart AI",
    description=(
        "AI-powered personal finance API. Upload a bank statement (CSV, PDF, or image) "
        "and receive a plain English analysis of your spending with smarter alternatives."
    ),
    version="1.0.0",
    contact={
        "name": "Arfat Mushtaq",
        "email": "arfatmushtaq62@gmail.com",
    },
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (CSS, JS, images if any)
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# In-memory session store
_sessions: dict[str, dict] = {}


# ── Response models ───────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    version: str
    supported_countries: list[str]
    supported_formats: list[str]
    timestamp: str


class MerchantSummary(BaseModel):
    merchant: str
    total: float
    count: int
    avg: float
    category: str


class CategorySummary(BaseModel):
    label: str
    total: float
    count: int
    avg: float


class SavingOpportunity(BaseModel):
    category: str
    monthly_saving: float
    annual_saving: float
    description: str


class AnalysisResponse(BaseModel):
    session_id: str
    country: str
    currency_symbol: str
    file_type: str
    date_from: str
    date_to: str
    total_transactions: int
    total_spent: float
    categories: dict[str, CategorySummary]
    food_delivery: Optional[dict] = None
    coffee: Optional[dict] = None
    groceries: Optional[dict] = None
    frequent_merchants: list[MerchantSummary]
    subscriptions: Optional[dict] = None
    gym: Optional[dict] = None
    transport: Optional[dict] = None
    saving_opportunities: list[SavingOpportunity]
    total_monthly_saving: float
    total_annual_saving: float
    report_markdown: str
    quick_summary: str
    analysed_at: str
    processing_notes: list[str]


# ── Frontend routes ───────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def serve_frontend():
    """Serve the main HTML frontend."""
    template_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "templates", "index.html"
    )
    if not os.path.exists(template_path):
        return HTMLResponse(
            "<h1>Frontend not found</h1>"
            "<p>Make sure templates/index.html exists.</p>"
            "<p><a href='/docs'>Go to API docs</a></p>",
            status_code=404
        )
    with open(template_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


# ── API Endpoints ─────────────────────────────────────────────────────────────

@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    tags=["System"],
)
async def health():
    return HealthResponse(
        status="ok",
        version="1.0.0",
        supported_countries=get_all_countries(),
        supported_formats=["csv", "pdf", "jpg", "jpeg", "png", "webp"],
        timestamp=datetime.utcnow().isoformat(),
    )


@app.get(
    "/countries",
    summary="List supported countries",
    tags=["System"],
)
async def list_countries():
    from src.config import get_config
    result = {}
    for country in get_all_countries():
        cfg = get_config(country)
        result[country] = {
            "currency_symbol": cfg["currency_symbol"],
            "currency_code":   cfg["currency_code"],
            "supported_banks": list(cfg["bank_formats"].keys()),
        }
    return result


@app.post(
    "/analyse",
    response_model=AnalysisResponse,
    summary="Analyse a bank statement",
    tags=["Analysis"],
)
async def analyse(
    file: UploadFile = File(...),
    country: str = Form(...),
):
    notes = []

    # Validate country
    valid_countries = get_all_countries()
    if country not in valid_countries:
        raise HTTPException(
            status_code=400,
            detail=f"Country '{country}' not supported. Choose from: {', '.join(valid_countries)}"
        )

    # Detect file type
    filename = file.filename or "upload"
    ext = filename.split(".")[-1].lower()
    type_map = {
        "csv": "csv", "pdf": "pdf",
        "jpg": "image", "jpeg": "image",
        "png": "image", "webp": "image", "bmp": "image",
    }
    file_type = type_map.get(ext)
    if not file_type:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: .{ext}. Accepted: csv, pdf, jpg, jpeg, png, webp"
        )

    accuracy_map = {"csv": "~99%", "pdf": "85-95%", "image": "75-85%"}
    notes.append(f"File format: {ext.upper()} — typical accuracy {accuracy_map[file_type]}")

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(mode="wb", suffix=f".{ext}", delete=False) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        # Parse
        try:
            df = parse_statement(tmp_path, country, file_type=file_type)
        except Exception as e:
            raise HTTPException(status_code=422, detail=f"Could not parse statement: {str(e)}")

        if df.empty:
            raise HTTPException(
                status_code=422,
                detail="No spending transactions found in this file."
            )

        summary = get_statement_summary(df, country)
        symbol  = get_currency_symbol(country)
        notes.append(f"Extracted {len(df)} spending transactions")

        # Categorise
        df         = categorise_all(df, country, use_llm=True)
        cat_totals = get_category_totals(df)
        frequent   = get_frequent_merchants(df, min_transactions=3)
        notes.append(f"LLM smart categorisation applied — {len(cat_totals)} categories identified")

        # Deep analysis
        food    = analyse_food_delivery(df, country)
        coffee  = analyse_coffee(df, country)
        grocery = analyse_groceries(df, country)
        fm = build_food_delivery_message(food)
        cm = build_coffee_message(coffee)
        gm = build_groceries_message(grocery)

        # Other spending
        missing = []
        if not food:    missing.append("food_delivery")
        if not coffee:  missing.append("coffee")
        if not grocery: missing.append("groceries")

        other_analysis = None
        other_message  = ""
        if missing:
            other_analysis = analyse_other_spending(df, country, missing)
            other_message  = build_other_spending_message(other_analysis)

        # Generic advice
        advice = get_all_generic_advice(df, country)

        # Saving opportunities
        saving_opps  = []
        total_saving = 0.0

        if food and food.get("realistic_saving", 0) > 0:
            s = food["realistic_saving"]
            saving_opps.append(SavingOpportunity(
                category="Food Delivery", monthly_saving=round(s,2),
                annual_saving=round(s*12,2),
                description="Cook at home for half your delivery meals",
            ))
            total_saving += s

        if coffee and coffee.get("realistic_saving", 0) > 0:
            s = coffee["realistic_saving"]
            saving_opps.append(SavingOpportunity(
                category="Coffee", monthly_saving=round(s,2),
                annual_saving=round(s*12,2),
                description="Switch 60% of cafe visits to home coffee",
            ))
            total_saving += s

        if grocery and grocery.get("realistic_saving", 0) > 0:
            s = grocery["realistic_saving"]
            saving_opps.append(SavingOpportunity(
                category="Groceries", monthly_saving=round(s,2),
                annual_saving=round(s*12,2),
                description="Split shop between budget and premium stores",
            ))
            total_saving += s

        subs = (advice.get("subscriptions") or {})
        if subs.get("potential_saving", 0) > 0:
            s = subs["potential_saving"]
            saving_opps.append(SavingOpportunity(
                category="Subscriptions", monthly_saving=round(s,2),
                annual_saving=round(s*12,2),
                description="Cancel unused streaming/app subscriptions",
            ))
            total_saving += s

        # Generate report
        report_md = generate_report(
            country=country, summary=summary,
            food_analysis=food, coffee_analysis=coffee, grocery_analysis=grocery,
            generic_advice=advice,
            food_message=fm, coffee_message=cm, grocery_message=gm,
            other_analysis=other_analysis, other_message=other_message,
            frequent_merchants=frequent,
        )

        quick_sum = generate_quick_summary(
            total_spent=summary.get("total_spent", 0),
            total_saving=total_saving,
            country=country,
        )

        session_id = str(uuid.uuid4())

        response_data = AnalysisResponse(
            session_id=session_id,
            country=country,
            currency_symbol=symbol,
            file_type=file_type,
            date_from=summary.get("date_from", "Unknown"),
            date_to=summary.get("date_to", "Unknown"),
            total_transactions=summary.get("total_transactions", 0),
            total_spent=round(summary.get("total_spent", 0), 2),
            categories={
                k: CategorySummary(
                    label=v["label"], total=round(v["total"],2),
                    count=v["count"], avg=round(v["avg"],2),
                )
                for k, v in cat_totals.items()
            },
            food_delivery={
                "total": round(food["total_spent"],2),
                "order_count": food["order_count"],
                "avg_order": round(food["avg_order"],2),
                "home_cost_avg": food["home_cost_per_meal"],
                "realistic_saving": round(food.get("realistic_saving",0),2),
                "annual_saving": round(food.get("annual_saving",0),2),
                "analysis": fm,
            } if food else None,
            coffee={
                "total": round(coffee["total_spent"],2),
                "visit_count": coffee["visit_count"],
                "avg_spend": round(coffee["avg_spend"],2),
                "home_cost_avg": coffee["home_cost_per_cup"],
                "realistic_saving": round(coffee.get("realistic_saving",0),2),
                "annual_saving": round(coffee.get("annual_saving",0),2),
                "analysis": cm,
            } if coffee else None,
            groceries={
                "total": round(grocery["total_spent"],2),
                "shop_count": grocery["shop_count"],
                "primary_tier": grocery["primary_tier"],
                "realistic_saving": round(grocery.get("realistic_saving",0),2),
                "annual_saving": round(grocery.get("annual_saving",0),2),
                "analysis": gm,
            } if grocery else None,
            frequent_merchants=[
                MerchantSummary(
                    merchant=m["merchant"], total=round(m["total"],2),
                    count=int(m["count"]), avg=round(m["avg"],2),
                    category=m["category_label"],
                ) for m in frequent[:10]
            ],
            subscriptions={
                "total": round(subs.get("total",0),2),
                "count": subs.get("count",0),
                "annual": round(subs.get("annual",0),2),
                "saving": round(subs.get("potential_saving",0),2),
                "advice": subs.get("advice_text",""),
            } if subs else None,
            gym={
                "total": round((advice.get("gym") or {}).get("total",0),2),
                "advice": (advice.get("gym") or {}).get("advice_text",""),
            } if advice.get("gym") else None,
            transport={
                "total": round((advice.get("transport") or {}).get("total",0),2),
                "trip_count": (advice.get("transport") or {}).get("count",0),
                "avg_trip": round((advice.get("transport") or {}).get("avg",0),2),
                "advice": (advice.get("transport") or {}).get("advice_text",""),
            } if advice.get("transport") else None,
            saving_opportunities=saving_opps,
            total_monthly_saving=round(total_saving,2),
            total_annual_saving=round(total_saving*12,2),
            report_markdown=report_md,
            quick_summary=quick_sum,
            analysed_at=datetime.utcnow().isoformat(),
            processing_notes=notes,
        )

        _sessions[session_id] = response_data.model_dump()
        return response_data

    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


@app.get(
    "/report/{session_id}",
    summary="Get report by session ID",
    tags=["Analysis"],
)
async def get_report(session_id: str):
    if session_id not in _sessions:
        raise HTTPException(
            status_code=404,
            detail=f"Session '{session_id}' not found. Please re-upload your statement."
        )
    return JSONResponse(content=_sessions[session_id])