"""
FinSakhi Virtual Trading / Portfolio API
Allows users to simulate buying/selling commodities and mutual funds
with a virtual balance of ₹1,00,000.
Uses existing Portfolio and Investment DB tables.
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.models.database import get_db, Portfolio, Investment, User
from typing import Optional, List
from datetime import datetime
import requests
import yfinance as yf
import time

router = APIRouter(prefix="/api/portfolio", tags=["Portfolio"])

VIRTUAL_STARTING_BALANCE = 100000.0  # ₹1,00,000

# ── Price cache ──────────────────────────────────────────
_cache = {}
_TTL = 300

def _cached(key):
    if key in _cache:
        val, ts = _cache[key]
        if time.time() - ts < _TTL:
            return val
    return None

def _set_cache(key, val):
    _cache[key] = (val, time.time())


# ── Schemas ──────────────────────────────────────────────

class BuyRequest(BaseModel):
    user_id: int
    asset_type: str          # "commodity" or "mutual_fund"
    asset_symbol: str        # e.g. "gold", "silver", scheme code "119598"
    asset_name: str
    quantity: float
    language: Optional[str] = "en"

class SellRequest(BaseModel):
    user_id: int
    investment_id: int
    quantity: float
    language: Optional[str] = "en"


# ── Helpers ──────────────────────────────────────────────

COMMODITY_TICKERS = {
    "gold": "GC=F",
    "silver": "SI=F",
    "crude_oil": "CL=F",
}

def _get_usd_inr() -> float:
    cached = _cached("usd_inr")
    if cached:
        return cached
    try:
        t = yf.Ticker("INR=X")
        h = t.history(period="1d")
        rate = float(h["Close"].iloc[-1]) if not h.empty else 83.0
        _set_cache("usd_inr", rate)
        return rate
    except Exception:
        return 83.0

def _get_commodity_price_inr(symbol: str) -> Optional[float]:
    cached = _cached(f"price_{symbol}")
    if cached:
        return cached
    ticker_str = COMMODITY_TICKERS.get(symbol)
    if not ticker_str:
        return None
    try:
        t = yf.Ticker(ticker_str)
        h = t.history(period="2d")
        if h.empty:
            return None
        usd_inr = _get_usd_inr()
        price = float(h["Close"].iloc[-1]) * usd_inr
        _set_cache(f"price_{symbol}", price)
        return round(price, 2)
    except Exception:
        return None

def _get_mf_nav(scheme_code: str) -> Optional[float]:
    cached = _cached(f"nav_{scheme_code}")
    if cached:
        return cached
    try:
        resp = requests.get(f"https://api.mfapi.in/mf/{scheme_code}", timeout=10)
        if resp.status_code != 200:
            return None
        data = resp.json().get("data", [])
        if not data:
            return None
        nav = float(data[0]["nav"])
        _set_cache(f"nav_{scheme_code}", nav)
        return nav
    except Exception:
        return None

def _get_current_price(asset_type: str, asset_symbol: str) -> Optional[float]:
    if asset_type == "commodity":
        return _get_commodity_price_inr(asset_symbol)
    elif asset_type == "mutual_fund":
        return _get_mf_nav(asset_symbol)
    return None

def _ensure_portfolio(db: Session, user_id: int) -> Portfolio:
    portfolio = db.query(Portfolio).filter(Portfolio.user_id == user_id).first()
    if not portfolio:
        portfolio = Portfolio(
            user_id=user_id,
            total_invested=0.0,
            current_value=0.0,
            total_returns=0.0,
        )
        db.add(portfolio)
        db.commit()
        db.refresh(portfolio)
    return portfolio


# ── Endpoints ────────────────────────────────────────────

@router.get("/{user_id}")
def get_portfolio(user_id: int, db: Session = Depends(get_db)):
    """Get user's portfolio with holdings, P&L, and virtual balance."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")

    portfolio = _ensure_portfolio(db, user_id)
    investments = db.query(Investment).filter(Investment.user_id == user_id).all()

    holdings = []
    total_current_value = 0.0
    total_invested = 0.0

    for inv in investments:
        if inv.quantity <= 0:
            continue
        # Determine asset type from symbol
        asset_type = "commodity" if inv.asset_symbol in COMMODITY_TICKERS else "mutual_fund"
        current_price = _get_current_price(asset_type, inv.asset_symbol)

        if current_price is None:
            current_price = inv.buy_price  # fallback

        current_value = inv.quantity * current_price
        invested = inv.invested_amount
        pnl = current_value - invested
        pnl_pct = (pnl / invested * 100) if invested > 0 else 0

        total_current_value += current_value
        total_invested += invested

        holdings.append({
            "id": inv.id,
            "asset_symbol": inv.asset_symbol,
            "asset_name": inv.asset_name,
            "asset_type": asset_type,
            "quantity": inv.quantity,
            "buy_price": round(inv.buy_price, 2),
            "current_price": round(current_price, 2),
            "invested_amount": round(invested, 2),
            "current_value": round(current_value, 2),
            "pnl": round(pnl, 2),
            "pnl_pct": round(pnl_pct, 2),
            "bought_at": inv.created_at.isoformat() if inv.created_at else None,
        })

    virtual_balance = VIRTUAL_STARTING_BALANCE - total_invested
    overall_pnl = total_current_value - total_invested

    return {
        "user_id": user_id,
        "virtual_balance": round(virtual_balance, 2),
        "total_invested": round(total_invested, 2),
        "total_current_value": round(total_current_value, 2),
        "overall_pnl": round(overall_pnl, 2),
        "overall_pnl_pct": round((overall_pnl / total_invested * 100) if total_invested > 0 else 0, 2),
        "holdings": holdings,
    }


@router.post("/buy")
def buy_asset(req: BuyRequest, db: Session = Depends(get_db)):
    """Buy an asset (virtual trading)."""
    user = db.query(User).filter(User.id == req.user_id).first()
    if not user:
        raise HTTPException(404, "User not found")

    # Get current price
    current_price = _get_current_price(req.asset_type, req.asset_symbol)
    if current_price is None:
        raise HTTPException(400, "Could not fetch price for this asset. Try again later.")

    cost = req.quantity * current_price
    portfolio = _ensure_portfolio(db, req.user_id)

    # Check virtual balance
    existing_invested = sum(
        inv.invested_amount for inv in
        db.query(Investment).filter(Investment.user_id == req.user_id).all()
        if inv.quantity > 0
    )
    available = VIRTUAL_STARTING_BALANCE - existing_invested
    if cost > available:
        raise HTTPException(400, f"Insufficient virtual balance. Available: ₹{available:.2f}, Required: ₹{cost:.2f}")

    # Check if user already holds this asset → average up
    existing = db.query(Investment).filter(
        Investment.user_id == req.user_id,
        Investment.asset_symbol == req.asset_symbol,
    ).first()

    if existing and existing.quantity > 0:
        # Average the buy price
        total_qty = existing.quantity + req.quantity
        total_cost = existing.invested_amount + cost
        existing.quantity = total_qty
        existing.invested_amount = total_cost
        existing.buy_price = total_cost / total_qty
        db.commit()
        db.refresh(existing)
        inv_id = existing.id
    else:
        new_inv = Investment(
            user_id=req.user_id,
            asset_symbol=req.asset_symbol,
            asset_name=req.asset_name,
            quantity=req.quantity,
            buy_price=current_price,
            invested_amount=cost,
        )
        db.add(new_inv)
        db.commit()
        db.refresh(new_inv)
        inv_id = new_inv.id

    # Update portfolio summary
    portfolio.total_invested = existing_invested + cost
    portfolio.current_value = portfolio.total_invested  # will be recalculated on GET
    db.commit()

    msg_en = f"Successfully bought {req.quantity} units of {req.asset_name} at ₹{current_price:.2f}"
    msg_hi = f"सफलतापूर्वक {req.quantity} यूनिट {req.asset_name} ₹{current_price:.2f} पर खरीदी"

    return {
        "success": True,
        "message": msg_hi if req.language == "hi" else msg_en,
        "investment_id": inv_id,
        "price": round(current_price, 2),
        "cost": round(cost, 2),
        "remaining_balance": round(VIRTUAL_STARTING_BALANCE - existing_invested - cost, 2),
    }


@router.post("/sell")
def sell_asset(req: SellRequest, db: Session = Depends(get_db)):
    """Sell (partially or fully) a held asset."""
    inv = db.query(Investment).filter(
        Investment.id == req.investment_id,
        Investment.user_id == req.user_id,
    ).first()
    if not inv:
        raise HTTPException(404, "Investment not found")
    if inv.quantity <= 0:
        raise HTTPException(400, "No holdings to sell")
    if req.quantity > inv.quantity:
        raise HTTPException(400, f"Cannot sell {req.quantity} — you only hold {inv.quantity}")

    asset_type = "commodity" if inv.asset_symbol in COMMODITY_TICKERS else "mutual_fund"
    current_price = _get_current_price(asset_type, inv.asset_symbol)
    if current_price is None:
        current_price = inv.buy_price

    sale_value = req.quantity * current_price
    cost_basis = req.quantity * inv.buy_price
    pnl = sale_value - cost_basis

    # Reduce holding
    sold_fraction = req.quantity / inv.quantity
    inv.invested_amount -= inv.invested_amount * sold_fraction
    inv.quantity -= req.quantity
    if inv.quantity < 0.0001:
        inv.quantity = 0
        inv.invested_amount = 0

    db.commit()

    msg_en = f"Sold {req.quantity} units of {inv.asset_name} at ₹{current_price:.2f}. P&L: ₹{pnl:+.2f}"
    msg_hi = f"{req.quantity} यूनिट {inv.asset_name} ₹{current_price:.2f} पर बेची। लाभ/हानि: ₹{pnl:+.2f}"

    return {
        "success": True,
        "message": msg_hi if req.language == "hi" else msg_en,
        "sale_value": round(sale_value, 2),
        "pnl": round(pnl, 2),
        "remaining_quantity": round(inv.quantity, 4),
    }
