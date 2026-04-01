"""
FinSakhi Investment API — Live Commodity Prices, Indian Mutual Funds & AI Recommendations
Free data sources: yfinance (gold/silver/oil), mfapi.in (mutual funds), Groq LLM (recommendations)
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.models.database import (
    get_db, User, FinancialProfile, AssessmentSession,
    LiteracyAssessment, UserFinancialHealth, LearningProgress
)
from typing import Optional, List
import yfinance as yf
import requests
from datetime import datetime, timedelta
from functools import lru_cache
import time, json, os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

# ============================================
# Groq LLM client (for recommendations)
# ============================================
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if GROQ_API_KEY:
    groq_client = Groq(api_key=GROQ_API_KEY)
    print(" Groq API configured for investment recommendations")
else:
    groq_client = None
    print(" GROQ_API_KEY not set — investment recommendations will use fallback")

router = APIRouter(prefix="/api/investments", tags=["Investments"])

# ============================================
# Pydantic Schemas (for recommendation endpoints)
# ============================================

class RecommendationRequest(BaseModel):
    user_id: int
    language: Optional[str] = "en"
    question: Optional[str] = None  # Optional follow-up question

class AskInvestmentRequest(BaseModel):
    user_id: int
    question: str
    language: Optional[str] = "en"

# ============================================
# CONSTANTS
# ============================================

# yfinance tickers for commodities (prices in USD)
COMMODITY_TICKERS = {
    "gold": {"ticker": "GC=F", "name": "Gold", "name_hi": "सोना", "unit": "per gram"},
    "silver": {"ticker": "SI=F", "name": "Silver", "name_hi": "चाँदी", "unit": "per gram"},
    "crude_oil": {"ticker": "CL=F", "name": "Crude Oil", "name_hi": "कच्चा तेल", "unit": "per barrel"},
}

USD_INR_TICKER = "INR=X"  # USD to INR exchange rate

# Popular Indian mutual funds (curated for rural/beginner investors)
# Scheme codes verified against mfapi.in
POPULAR_MF_SCHEMES = [
    {"code": 119598, "name": "SBI Large Cap Fund - Direct Plan - Growth", "category": "Large Cap"},
    {"code": 125497, "name": "SBI Small Cap Fund - Direct Plan - Growth", "category": "Small Cap"},
    {"code": 118968, "name": "HDFC Balanced Advantage Fund - Direct Plan - Growth", "category": "Hybrid"},
    {"code": 119721, "name": "SBI Large & Midcap Fund - Direct Plan - Growth", "category": "Large & Mid Cap"},
    {"code": 122639, "name": "Parag Parikh Flexi Cap Fund - Direct Plan - Growth", "category": "Flexi Cap"},
    {"code": 118778, "name": "Nippon India Small Cap Fund - Direct Plan - Growth", "category": "Small Cap"},
    {"code": 118825, "name": "Mirae Asset Large Cap Fund - Direct Plan - Growth", "category": "Large Cap"},
    {"code": 120505, "name": "Axis Midcap Fund - Direct Plan - Growth", "category": "Mid Cap"},
]

# MFAPI base URL (completely free, no auth)
MFAPI_BASE = "https://api.mfapi.in/mf"

# TradingView widget symbols for embeddable charts
TRADINGVIEW_SYMBOLS = {
    "gold": "COMEX:GC1!",
    "silver": "COMEX:SI1!",
    "crude_oil": "NYMEX:CL1!",
    "nifty50": "NSE:NIFTY",
    "sensex": "BSE:SENSEX",
}

# ============================================
# CACHE (simple TTL cache to avoid hammering APIs)
# ============================================

_price_cache = {}
_CACHE_TTL = 0  # Always fetch fresh — no caching


def _get_cached(key: str):
    if key in _price_cache:
        data, ts = _price_cache[key]
        if time.time() - ts < _CACHE_TTL:
            return data
    return None


def _set_cached(key: str, data):
    _price_cache[key] = (data, time.time())


# ============================================
# HELPERS
# ============================================

def _get_usd_inr_rate(force_refresh: bool = False) -> float:
    """Get current USD to INR exchange rate."""
    if not force_refresh:
        cached = _get_cached("usd_inr")
        if cached:
            return cached
    try:
        ticker = yf.Ticker(USD_INR_TICKER)
        hist = ticker.history(period="1d", interval="1m")
        if hist.empty:
            hist = ticker.history(period="1d")
        if hist.empty:
            return 83.0  # fallback
        rate = float(hist["Close"].iloc[-1])
        _set_cached("usd_inr", rate)
        return rate
    except Exception:
        return 83.0  # fallback


def _fetch_commodity_price(commodity_key: str, force_refresh: bool = False) -> dict:
    """Fetch latest available commodity price from yfinance."""
    if not force_refresh:
        cached = _get_cached(f"commodity_{commodity_key}")
        if cached:
            return cached

    info = COMMODITY_TICKERS.get(commodity_key)
    if not info:
        return None

    try:
        ticker = yf.Ticker(info["ticker"])
        intraday_hist = ticker.history(period="1d", interval="1m")
        if intraday_hist.empty:
            intraday_hist = ticker.history(period="5d")
        if intraday_hist.empty:
            return None

        daily_hist = ticker.history(period="2d", interval="1d")

        usd_inr = _get_usd_inr_rate(force_refresh=force_refresh)
        price_usd = float(intraday_hist["Close"].iloc[-1])
        if len(daily_hist) >= 2:
            prev_close_usd = float(daily_hist["Close"].iloc[-2])
        elif len(intraday_hist) >= 2:
            prev_close_usd = float(intraday_hist["Close"].iloc[-2])
        else:
            prev_close_usd = price_usd

        if info["unit"] == "per gram":
            # Convert Troy Oz to Grams
            price_usd /= 31.1034768
            prev_close_usd /= 31.1034768

        change_usd = price_usd - prev_close_usd
        change_pct = (change_usd / prev_close_usd * 100) if prev_close_usd else 0

        market_ts = intraday_hist.index[-1]
        market_timestamp = market_ts.isoformat() if hasattr(market_ts, "isoformat") else str(market_ts)

        result = {
            "commodity": commodity_key,
            "name": info["name"],
            "name_hi": info["name_hi"],
            "unit": info["unit"],
            "price_usd": round(price_usd, 2),
            "price_inr": round(price_usd * usd_inr, 2),
            "change_usd": round(change_usd, 2),
            "change_pct": round(change_pct, 2),
            "direction": "up" if change_usd >= 0 else "down",
            "usd_inr_rate": round(usd_inr, 2),
            "last_updated": market_timestamp,
            "fetched_at": datetime.utcnow().isoformat() + "Z",
        }
        _set_cached(f"commodity_{commodity_key}", result)
        return result
    except Exception as e:
        print(f" Failed to fetch {commodity_key}: {e}")
        return None


def _fetch_mf_nav(scheme_code: int) -> dict:
    """Fetch latest NAV for a mutual fund from mfapi.in."""
    cached = _get_cached(f"mf_{scheme_code}")
    if cached:
        return cached

    try:
        resp = requests.get(f"{MFAPI_BASE}/{scheme_code}", timeout=10)
        if resp.status_code != 200:
            return None
        data = resp.json()

        meta = data.get("meta", {})
        nav_data = data.get("data", [])
        if not nav_data:
            return None

        latest = nav_data[0]
        previous = nav_data[1] if len(nav_data) > 1 else latest

        current_nav = float(latest["nav"])
        prev_nav = float(previous["nav"])
        change = current_nav - prev_nav
        change_pct = (change / prev_nav * 100) if prev_nav else 0

        result = {
            "scheme_code": scheme_code,
            "scheme_name": meta.get("scheme_name", ""),
            "fund_house": meta.get("fund_house", ""),
            "scheme_type": meta.get("scheme_type", ""),
            "scheme_category": meta.get("scheme_category", ""),
            "nav": current_nav,
            "prev_nav": prev_nav,
            "change": round(change, 4),
            "change_pct": round(change_pct, 2),
            "direction": "up" if change >= 0 else "down",
            "date": latest.get("date", ""),
        }
        _set_cached(f"mf_{scheme_code}", result)
        return result
    except Exception as e:
        print(f" Failed to fetch MF {scheme_code}: {e}")
        return None


# ============================================
# ENDPOINTS — COMMODITIES
# ============================================

@router.get("/commodities")
def get_all_commodity_prices(
    live: bool = Query(False, description="If true, bypass cache and fetch latest available data")
):
    """
    Get latest available prices for gold, silver, and crude oil.
    Prices in both USD and INR.
    """
    results = []
    for key in COMMODITY_TICKERS:
        data = _fetch_commodity_price(key, force_refresh=live)
        if data:
            results.append(data)

    return {
        "commodities": results,
        "source": "Yahoo Finance (yfinance)",
        "cache_ttl_seconds": _CACHE_TTL,
        "cache_bypassed": live,
        "note": (
            "Live refresh requested. Source may still have exchange delay."
            if live else
            "Set live=true to bypass server cache. Source may have exchange delay."
        ),
    }


@router.get("/commodities/{commodity}")
def get_commodity_price(
    commodity: str,
    live: bool = Query(False, description="If true, bypass cache and fetch latest available data")
):
    """
    Get live price for a specific commodity.
    Valid values: gold, silver, crude_oil
    """
    if commodity not in COMMODITY_TICKERS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid commodity. Choose from: {', '.join(COMMODITY_TICKERS.keys())}"
        )

    data = _fetch_commodity_price(commodity, force_refresh=live)
    if not data:
        raise HTTPException(status_code=503, detail=f"Unable to fetch {commodity} price right now")

    return data


@router.get("/commodities/{commodity}/history")
def get_commodity_history(
    commodity: str,
    period: str = Query("1mo", description="1d, 5d, 1mo, 3mo, 6mo, 1y, 5y, max")
):
    """
    Get historical price data for a commodity.
    Use this to render price charts on the frontend.
    """
    if commodity not in COMMODITY_TICKERS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid commodity. Choose from: {', '.join(COMMODITY_TICKERS.keys())}"
        )

    valid_periods = ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "max"]
    if period not in valid_periods:
        raise HTTPException(status_code=400, detail=f"Invalid period. Choose from: {', '.join(valid_periods)}")

    try:
        ticker = yf.Ticker(COMMODITY_TICKERS[commodity]["ticker"])
        hist = ticker.history(period=period)
        if hist.empty:
            raise HTTPException(status_code=503, detail="No historical data available")

        usd_inr = _get_usd_inr_rate()

        prices = []
        for idx, row in hist.iterrows():
            close_price = float(row["Close"])
            if COMMODITY_TICKERS[commodity]["unit"] == "per gram":
                close_price /= 31.1034768

            prices.append({
                "date": idx.strftime("%Y-%m-%d"),
                "price_usd": round(close_price, 2),
                "price_inr": round(close_price * usd_inr, 2),
                "volume": int(row["Volume"]) if row["Volume"] else 0,
            })

        return {
            "commodity": commodity,
            "period": period,
            "data_points": len(prices),
            "prices": prices,
            "usd_inr_rate": round(usd_inr, 2),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Failed to fetch history: {str(e)}")


# ============================================
# ENDPOINTS — MUTUAL FUNDS
# ============================================

@router.get("/mutual-funds/popular")
def get_popular_mutual_funds():
    """
    Get NAV and daily change for curated popular Indian mutual funds.
    Great for beginners — hand-picked safe and well-known funds.
    """
    results = []
    for scheme in POPULAR_MF_SCHEMES:
        data = _fetch_mf_nav(scheme["code"])
        if data:
            data["category_tag"] = scheme["category"]
            results.append(data)

    return {
        "funds": results,
        "total": len(results),
        "source": "mfapi.in (AMFI India)",
        "note": "NAV updated daily by AMFI"
    }


@router.get("/mutual-funds/search")
def search_mutual_funds(q: str = Query(..., min_length=2, description="Search query")):
    """
    Search for any Indian mutual fund by name.
    Uses mfapi.in free search API — no key required.
    """
    try:
        resp = requests.get(f"{MFAPI_BASE}/search?q={q}", timeout=10)
        if resp.status_code != 200:
            raise HTTPException(status_code=503, detail="MF search API unavailable")

        results = resp.json()
        return {
            "query": q,
            "results": results[:20],  # Limit to 20 results
            "total": len(results),
            "tip": "Use scheme_code to fetch NAV via /mutual-funds/{scheme_code}"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Search failed: {str(e)}")


@router.get("/mutual-funds/{scheme_code}")
def get_mutual_fund_nav(scheme_code: int):
    """
    Get latest NAV and details for a specific mutual fund.
    Pass the scheme_code from search results or popular list.
    """
    data = _fetch_mf_nav(scheme_code)
    if not data:
        raise HTTPException(status_code=404, detail="Mutual fund not found or API unavailable")

    return data


@router.get("/mutual-funds/{scheme_code}/history")
def get_mutual_fund_history(
    scheme_code: int,
    days: int = Query(30, ge=1, le=3650, description="Number of days of history")
):
    """
    Get historical NAV data for a mutual fund.
    Use this to render NAV charts on the frontend.
    """
    try:
        resp = requests.get(f"{MFAPI_BASE}/{scheme_code}", timeout=15)
        if resp.status_code != 200:
            raise HTTPException(status_code=503, detail="MF API unavailable")

        data = resp.json()
        nav_data = data.get("data", [])
        meta = data.get("meta", {})

        if not nav_data:
            raise HTTPException(status_code=404, detail="No NAV data found")

        # mfapi returns newest first, limit to requested days
        limited = nav_data[:days]

        # Reverse to chronological order (oldest → newest)
        limited.reverse()

        prices = []
        for entry in limited:
            try:
                prices.append({
                    "date": entry["date"],
                    "nav": float(entry["nav"]),
                })
            except (ValueError, KeyError):
                continue

        # Calculate returns
        if len(prices) >= 2:
            start_nav = prices[0]["nav"]
            end_nav = prices[-1]["nav"]
            total_return = round(((end_nav - start_nav) / start_nav) * 100, 2)
        else:
            total_return = 0

        return {
            "scheme_code": scheme_code,
            "scheme_name": meta.get("scheme_name", ""),
            "fund_house": meta.get("fund_house", ""),
            "period_days": days,
            "data_points": len(prices),
            "total_return_pct": total_return,
            "prices": prices,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Failed to fetch history: {str(e)}")


# ============================================
# ENDPOINTS — CHARTS & EMBEDS
# ============================================

@router.get("/charts/embed-config")
def get_chart_embed_config():
    """
    Returns TradingView widget configuration for embedding FREE price charts.
    Frontend can use these to render live interactive charts.

    TradingView Mini Widget (free, no API key):
    - Just drop an iframe or use their JS widget library
    - Supports gold, silver, oil, Nifty, Sensex, and more
    """
    widgets = []
    for key, symbol in TRADINGVIEW_SYMBOLS.items():
        widgets.append({
            "asset": key,
            "tradingview_symbol": symbol,
            "mini_chart_url": f"https://www.tradingview.com/widgetembed/?symbol={symbol}&interval=D&theme=light&style=2&locale=en&hide_top_toolbar=1&save_image=0&hide_volume=1",
            "iframe_html": f'<iframe src="https://s.tradingview.com/widgetembed/?symbol={symbol}&interval=D&theme=light&style=2&locale=en&hide_top_toolbar=1&save_image=0&hide_volume=1" style="width:100%;height:300px;" frameborder="0"></iframe>',
        })

    return {
        "provider": "TradingView",
        "cost": "FREE (with TradingView branding)",
        "widgets": widgets,
        "advanced_chart_html": """
<!-- TradingView Advanced Chart Widget (free) — paste in your HTML -->
<div class="tradingview-widget-container">
  <div id="tradingview_chart"></div>
  <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
  <script type="text/javascript">
    new TradingView.widget({
      "container_id": "tradingview_chart",
      "width": "100%",
      "height": 400,
      "symbol": "COMEX:GC1!",
      "interval": "D",
      "theme": "light",
      "style": "2",
      "locale": "en",
      "toolbar_bg": "#f1f3f6",
      "enable_publishing": false,
      "hide_top_toolbar": false,
      "save_image": false
    });
  </script>
</div>""",
        "note": "TradingView widgets are free to embed. They show a small TradingView logo — no cost or API key."
    }


# ============================================
# ENDPOINTS — DASHBOARD / SUMMARY
# ============================================

@router.get("/dashboard")
def get_investment_dashboard(
    language: str = "en",
    live: bool = Query(False, description="If true, bypass commodity cache for latest available quotes")
):
    """
    One-call dashboard: all commodities + popular MFs + chart config.
    Ideal for the frontend home/investment screen.
    """
    # Fetch all commodities
    commodities = []
    for key in COMMODITY_TICKERS:
        data = _fetch_commodity_price(key, force_refresh=live)
        if data:
            commodities.append(data)

    # Fetch popular MFs
    mutual_funds = []
    for scheme in POPULAR_MF_SCHEMES[:4]:  # Top 4 for dashboard
        data = _fetch_mf_nav(scheme["code"])
        if data:
            data["category_tag"] = scheme["category"]
            mutual_funds.append(data)

    # Chart symbols
    charts = {key: symbol for key, symbol in TRADINGVIEW_SYMBOLS.items()}

    return {
        "commodities": commodities,
        "mutual_funds": mutual_funds,
        "chart_symbols": charts,
        "tips": [
            "Gold is a safe investment during uncertain times" if language == "en" else "अनिश्चित समय में सोना सुरक्षित निवेश है",
            "Start SIP with as little as ₹500/month" if language == "en" else "₹500/महीने से SIP शुरू करें",
            "Never invest money you might need in 6 months" if language == "en" else "6 महीने में चाहिए वो पैसा कभी निवेश न करें",
        ],
        "data_sources": {
            "commodities": "Yahoo Finance (free, usually delayed feed)",
            "mutual_funds": "mfapi.in / AMFI India (free, daily NAV)",
            "charts": "TradingView (free embeddable widgets)",
        },
        "cache_bypassed": live,
    }


# ============================================
# HELPERS — USER CONTEXT BUILDER
# ============================================

def _build_user_context(user_id: int, db: Session) -> dict:
    """
    Gather everything we know about a user:
    profile, assessment results, learning progress, financial health.
    Returns a dict the LLM can consume.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None

    # Financial profile
    profile = db.query(FinancialProfile).filter(FinancialProfile.user_id == user_id).first()

    # Latest completed assessment
    assessment = (
        db.query(AssessmentSession)
        .filter(AssessmentSession.user_id == user_id, AssessmentSession.status == "completed")
        .order_by(AssessmentSession.completed_at.desc())
        .first()
    )

    # Latest literacy assessment (category scores)
    literacy = (
        db.query(LiteracyAssessment)
        .filter(LiteracyAssessment.user_id == user_id)
        .order_by(LiteracyAssessment.completed_at.desc())
        .first()
    )

    # Financial health / learning progress
    health = db.query(UserFinancialHealth).filter(UserFinancialHealth.user_id == user_id).first()

    # Build context dict
    context = {
        "name": user.name or "User",
        "language": user.language or "en",
    }

    if profile:
        context.update({
            "monthly_income": profile.monthly_income,
            "income_source": profile.income_source,
            "risk_appetite": profile.risk_appetite,
            "occupation": profile.occupation,
            "marital_status": profile.marital_status,
            "children_count": profile.children_count,
        })
    else:
        context.update({
            "monthly_income": None,
            "income_source": None,
            "risk_appetite": "medium",
            "occupation": None,
            "marital_status": None,
            "children_count": 0,
        })

    if assessment:
        questions_asked = json.loads(assessment.questions_asked or "[]")
        profile_data = json.loads(assessment.profile_data or "{}")
        context.update({
            "literacy_level": assessment.literacy_level,
            "assessment_score": assessment.total_score,
            "assessment_total": 8,
            "assessment_percentage": round((assessment.total_score / 8) * 100, 1),
            "assessment_profile": profile_data,
            "assessment_qa_summary": [
                {
                    "category": qa.get("category"),
                    "correct": qa.get("is_correct"),
                }
                for qa in questions_asked
            ],
        })
    else:
        context.update({
            "literacy_level": "beginner",
            "assessment_score": None,
            "assessment_total": None,
            "assessment_percentage": None,
            "assessment_profile": {},
            "assessment_qa_summary": [],
        })

    if literacy:
        context.update({
            "budgeting_score": literacy.budgeting_score,
            "investing_score": literacy.investing_score,
        })

    if health:
        context.update({
            "health_score": health.health_score,
            "lessons_completed": health.lessons_completed,
            "current_learning_level": health.current_level,
        })

    return context


def _get_live_market_summary() -> dict:
    """
    Fetch current commodity prices and popular MF NAVs
    to give the LLM real market context.
    """
    commodities = []
    for key in COMMODITY_TICKERS:
        data = _fetch_commodity_price(key, force_refresh=True)
        if data:
            commodities.append({
                "name": data["name"],
                "price_inr": data["price_inr"],
                "change_pct": data["change_pct"],
                "direction": data["direction"],
            })

    mutual_funds = []
    for scheme in POPULAR_MF_SCHEMES:
        data = _fetch_mf_nav(scheme["code"])
        if data:
            mutual_funds.append({
                "scheme_name": data["scheme_name"],
                "scheme_code": data["scheme_code"],
                "nav": data["nav"],
                "change_pct": data["change_pct"],
                "category": scheme["category"],
            })

    return {"commodities": commodities, "mutual_funds": mutual_funds}


def _generate_fallback_recommendations(user_context: dict) -> dict:
    """Fallback recommendations when Groq is unavailable."""
    income = user_context.get("monthly_income") or 15000
    risk = user_context.get("risk_appetite", "medium")
    level = user_context.get("literacy_level", "beginner")

    # SIP amount: ~10-15% of income, minimum ₹500
    sip_amount = max(500, round(income * 0.10 / 100) * 100)

    recs = {
        "summary": "Based on your profile, here are safe starting points for investing.",
        "summary_hi": "आपकी प्रोफ़ाइल के अनुसार, निवेश शुरू करने के लिए यहाँ सुरक्षित विकल्प हैं।",
        "recommended_sip_amount": sip_amount,
        "mutual_funds": [
            {
                "scheme_name": "SBI Large Cap Fund - Direct Plan - Growth",
                "scheme_code": 119598,
                "reason": "Large cap funds are stable and good for beginners",
                "reason_hi": "लार्ज कैप फंड स्थिर हैं और शुरुआत के लिए अच्छे हैं",
                "risk": "low",
                "suggested_sip": sip_amount,
            }
        ],
        "commodities": [
            {
                "commodity": "gold",
                "reason": "Gold is a traditional safe investment, good for preservation of wealth",
                "reason_hi": "सोना एक पारंपरिक सुरक्षित निवेश है, धन संरक्षण के लिए अच्छा है",
                "risk": "low",
            }
        ],
        "risk_warnings": [
            "Start small and increase gradually as you learn more",
            "Never invest money you may need within 6 months",
            "SIP is safer than lump-sum investing for beginners",
        ],
        "risk_warnings_hi": [
            "छोटी शुरुआत करें और जैसे-जैसे सीखें बढ़ाएं",
            "वो पैसा कभी निवेश न करें जो 6 महीने में चाहिए",
            "शुरुआत के लिए SIP, एकमुश्त निवेश से सुरक्षित है",
        ],
    }

    # Add more aggressive options for higher risk / income
    if risk in ("high",) or (income and income > 50000):
        recs["mutual_funds"].append({
            "scheme_name": "SBI Small Cap Fund - Direct Plan - Growth",
            "scheme_code": 125497,
            "reason": "Small cap funds can give higher returns over 5+ years",
            "reason_hi": "स्मॉल कैप फंड 5+ साल में अधिक रिटर्न दे सकते हैं",
            "risk": "high",
            "suggested_sip": sip_amount,
        })
        recs["commodities"].append({
            "commodity": "silver",
            "reason": "Silver is more volatile but has industrial demand upside",
            "reason_hi": "चाँदी अधिक अस्थिर है लेकिन औद्योगिक मांग से बढ़ सकती है",
            "risk": "medium",
        })

    return recs


async def _ask_groq_for_recommendations(user_context: dict, market_data: dict, language: str = "en", follow_up: str = None) -> dict:
    """
    Send user context + live market data to Groq LLM and get
    structured investment recommendations.
    """
    if not groq_client:
        return _generate_fallback_recommendations(user_context)

    name = user_context.get("name", "User")
    income = user_context.get("monthly_income", "unknown")
    source = user_context.get("income_source", "unknown")
    risk = user_context.get("risk_appetite", "medium")
    occupation = user_context.get("occupation", "unknown")
    marital = user_context.get("marital_status", "unknown")
    children = user_context.get("children_count", 0)
    level = user_context.get("literacy_level", "beginner")
    score = user_context.get("assessment_percentage", "not assessed")
    health = user_context.get("health_score", "unknown")
    budgeting_score = user_context.get("budgeting_score", "N/A")
    investing_score = user_context.get("investing_score", "N/A")

    # Format market data
    commodity_text = ""
    for c in market_data.get("commodities", []):
        commodity_text += f"  - {c['name']}: ₹{c['price_inr']:,.0f} ({c['direction']} {c['change_pct']}%)\n"

    mf_text = ""
    for mf in market_data.get("mutual_funds", []):
        mf_text += f"  - {mf['scheme_name']} (Code: {mf['scheme_code']}, NAV: ₹{mf['nav']:.2f}, {mf['category']})\n"

    follow_up_section = ""
    if follow_up:
        follow_up_section = f"""
USER'S SPECIFIC QUESTION:
"{follow_up}"
Answer this question FIRST, then provide your structured recommendations.
"""

    prompt = f"""You are FinSakhi, a trusted financial advisor for rural India (Bharat). You give simple, practical, and safe investment advice.

USER PROFILE:
- Name: {name}
- Monthly Income: ₹{income}
- Income Source: {source}
- Occupation: {occupation}
- Marital Status: {marital}
- Children: {children}
- Risk Appetite: {risk}
- Financial Literacy Level: {level}
- Assessment Score: {score}%
- Budgeting Knowledge: {budgeting_score}%
- Investing Knowledge: {investing_score}%
- Financial Health Score: {health}/100

LIVE MARKET DATA (today):
Commodities:
{commodity_text or "  (unavailable)"}
Mutual Funds (Popular Indian MFs):
{mf_text or "  (unavailable)"}
{follow_up_section}
TASK:
Based on this user's income, risk profile, literacy level, and current market conditions, recommend:
1. Which mutual funds to start SIP in (from the list above — use exact scheme_code)
2. Whether to invest in gold/silver/crude oil and why
3. Suggested monthly SIP amount (must be realistic for their income)
4. Risk warnings personalized to their level

RULES:
- Recommend SIP amount as 10-20% of monthly income, minimum ₹500
- For beginners/low income: suggest only Large Cap or Flexi Cap funds
- For intermediate users: can suggest Mid Cap, Balanced funds
- For advanced/high income: can suggest Small Cap, sectoral
- Always warn about risks in simple language
- If literacy level is beginner, explain everything simply like talking to a friend
- Include Hindi translations for all advice
- Never recommend more than 3 mutual funds
- Never suggest investing more than 20% of income

RESPOND IN THIS EXACT JSON FORMAT (no markdown, no extra text):
{{
  "summary": "2-3 sentence personalized summary in English",
  "summary_hi": "Same summary in Hindi",
  "answer": "Direct answer to user's question if they asked one, otherwise null",
  "answer_hi": "Same answer in Hindi, or null",
  "recommended_sip_amount": 1000,
  "mutual_funds": [
    {{
      "scheme_name": "Fund Name",
      "scheme_code": 119598,
      "reason": "Why this fund suits this user (English)",
      "reason_hi": "Hindi reason",
      "risk": "low/medium/high",
      "suggested_sip": 500
    }}
  ],
  "commodities": [
    {{
      "commodity": "gold/silver/crude_oil",
      "action": "buy/hold/avoid",
      "reason": "Why (English)",
      "reason_hi": "Hindi reason",
      "risk": "low/medium/high"
    }}
  ],
  "risk_warnings": ["Warning 1 in English", "Warning 2"],
  "risk_warnings_hi": ["Hindi warning 1", "Hindi warning 2"],
  "next_steps": ["Actionable step 1", "Step 2"],
  "next_steps_hi": ["Hindi step 1", "Hindi step 2"]
}}"""

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are FinSakhi, a trusted financial advisor for rural India. Respond ONLY with valid JSON. No markdown, no extra text."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.6,
            max_tokens=1500,
        )
        text = response.choices[0].message.content.strip()

        # Clean markdown fences if present
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
            text = text.rsplit("```", 1)[0].strip()

        result = json.loads(text)

        # Validate required keys exist
        required = ["summary", "mutual_funds", "commodities", "risk_warnings"]
        for key in required:
            if key not in result:
                raise ValueError(f"Missing key: {key}")

        return result

    except Exception as e:
        print(f" Groq recommendation error: {e}, using fallback")
        return _generate_fallback_recommendations(user_context)


# ============================================
# ENDPOINTS — AI RECOMMENDATIONS
# ============================================

@router.get("/recommendations/{user_id}")
async def get_personalized_recommendations(
    user_id: int,
    language: str = Query("en", description="en or hi"),
    db: Session = Depends(get_db),
):
    """
     AI-powered personalized investment recommendations.

    Pulls the user's financial profile, assessment results, and learning progress,
    combines with live market data, and asks Groq LLM to recommend
    mutual funds, commodities, and SIP amounts tailored to this user.
    """
    # 1. Build user context from DB
    user_context = _build_user_context(user_id, db)
    if not user_context:
        raise HTTPException(status_code=404, detail="User not found")

    # 2. Get live market data
    market_data = _get_live_market_summary()

    # 3. Ask Groq LLM for recommendations
    recommendations = await _ask_groq_for_recommendations(
        user_context=user_context,
        market_data=market_data,
        language=language,
    )

    return {
        "user_id": user_id,
        "user_profile_snapshot": {
            "name": user_context.get("name"),
            "monthly_income": user_context.get("monthly_income"),
            "risk_appetite": user_context.get("risk_appetite"),
            "literacy_level": user_context.get("literacy_level"),
            "assessment_score": user_context.get("assessment_percentage"),
        },
        "recommendations": recommendations,
        "market_data_used": market_data,
        "generated_at": datetime.utcnow().isoformat(),
        "powered_by": "Groq (Llama 3.3 70B)",
        "disclaimer": "These are AI-generated suggestions for learning purposes. Consult a certified financial advisor before investing real money."
            if language == "en"
            else "ये AI-जनित सुझाव सीखने के उद्देश्य से हैं। असली पैसा निवेश करने से पहले प्रमाणित वित्तीय सलाहकार से परामर्श लें।",
    }


@router.post("/recommendations/ask")
async def ask_investment_question(
    data: AskInvestmentRequest,
    db: Session = Depends(get_db),
):
    """
     Ask a follow-up investment question.

    The LLM answers the user's specific question in the context of their
    financial profile AND current market conditions.

    Example questions:
    - "Should I invest in gold right now?"
    - "Is SBI Small Cap Fund safe for me?"
    - "How much SIP should I start with?"
    - "What is the difference between large cap and small cap?"
    - "मुझे SIP कहाँ शुरू करनी चाहिए?"
    """
    if not data.question or len(data.question.strip()) < 3:
        raise HTTPException(status_code=400, detail="Please provide a valid question (at least 3 characters)")

    # 1. Build user context
    user_context = _build_user_context(data.user_id, db)
    if not user_context:
        raise HTTPException(status_code=404, detail="User not found")

    # 2. Get live market data
    market_data = _get_live_market_summary()

    # 3. Ask Groq with the follow-up question
    recommendations = await _ask_groq_for_recommendations(
        user_context=user_context,
        market_data=market_data,
        language=data.language or "en",
        follow_up=data.question.strip(),
    )

    return {
        "user_id": data.user_id,
        "question": data.question,
        "answer": recommendations.get("answer") or recommendations.get("summary"),
        "answer_hi": recommendations.get("answer_hi") or recommendations.get("summary_hi"),
        "recommendations": recommendations,
        "market_data_used": market_data,
        "generated_at": datetime.utcnow().isoformat(),
        "powered_by": "Groq (Llama 3.3 70B)",
        "disclaimer": "AI-generated suggestions for learning. Consult a financial advisor before investing."
            if (data.language or "en") == "en"
            else "AI-जनित सुझाव। निवेश से पहले वित्तीय सलाहकार से परामर्श लें।",
    }


@router.get("/recommendations/{user_id}/quick")
async def get_quick_recommendations(
    user_id: int,
    db: Session = Depends(get_db),
):
    """
     Quick recommendations without calling the LLM.
    Uses rule-based logic based on user's profile.
    Fast, no API dependency — good fallback for offline/low-latency needs.
    """
    user_context = _build_user_context(user_id, db)
    if not user_context:
        raise HTTPException(status_code=404, detail="User not found")

    recommendations = _generate_fallback_recommendations(user_context)

    return {
        "user_id": user_id,
        "mode": "quick (rule-based, no LLM)",
        "user_profile_snapshot": {
            "name": user_context.get("name"),
            "monthly_income": user_context.get("monthly_income"),
            "risk_appetite": user_context.get("risk_appetite"),
            "literacy_level": user_context.get("literacy_level"),
        },
        "recommendations": recommendations,
        "generated_at": datetime.utcnow().isoformat(),
    }
