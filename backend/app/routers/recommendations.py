"""
FinSakhi Recommendations API — Credit Card & Government Scheme Recommendations
Uses user financial profile + Groq LLM for personalised suggestions.
Includes direct apply links for government schemes.
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.models.database import (
    get_db, User, FinancialProfile, LiteracyAssessment
)
from typing import Optional, List
import json, os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

# ============================================
# Groq LLM client
# ============================================
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if GROQ_API_KEY:
    groq_client = Groq(api_key=GROQ_API_KEY)
    print("✅ Groq API configured for recommendations")
else:
    groq_client = None
    print("⚠️ GROQ_API_KEY not set — recommendations will use fallback data")

router = APIRouter(prefix="/api/recommendations", tags=["Recommendations"])

# ============================================
# Pydantic Schemas
# ============================================

class RecommendationRequest(BaseModel):
    user_id: int
    language: Optional[str] = "en"


class CreditCard(BaseModel):
    name: str
    bank: str
    card_type: str           # e.g. "Basic", "Rewards", "Cashback", "Secured"
    annual_fee: str
    benefits: List[str]
    best_for: str
    apply_url: str
    eligibility: str


class GovernmentScheme(BaseModel):
    name: str
    name_hi: Optional[str] = None
    ministry: str
    description: str
    benefits: List[str]
    eligibility: str
    how_to_apply: str
    apply_url: str
    category: str            # savings, insurance, pension, women, farmer, business, education


class CreditCardResponse(BaseModel):
    success: bool
    cards: List[CreditCard]
    ai_summary: Optional[str] = None
    language: str


class GovtSchemeResponse(BaseModel):
    success: bool
    schemes: List[GovernmentScheme]
    ai_summary: Optional[str] = None
    language: str


# ============================================
# STATIC CREDIT CARD DATABASE (Indian market)
# ============================================
CREDIT_CARDS_DB: List[dict] = [
    {
        "name": "SBI SimplyCLICK Credit Card",
        "bank": "SBI",
        "card_type": "Rewards",
        "annual_fee": "₹499 (waived on ₹1L annual spend)",
        "benefits": [
            "10× reward points on partner brands (Amazon, Cleartrip, Apollo 24|7)",
            "5× reward points on all online spends",
            "₹500 Amazon voucher as welcome gift",
            "Fuel surcharge waiver"
        ],
        "best_for": "Online shoppers with moderate income",
        "apply_url": "https://www.sbicard.com/en/personal/credit-cards/shopping/simplyclick-sbi-card.page",
        "eligibility": "Salaried ₹25,000+/month or self-employed with ITR",
        "min_income": 25000,
        "segment": ["salaried", "business"]
    },
    {
        "name": "HDFC MoneyBack+ Credit Card",
        "bank": "HDFC Bank",
        "card_type": "Cashback",
        "annual_fee": "₹500 (waived on ₹50K annual spend)",
        "benefits": [
            "2× reward points on all spends",
            "Cashback up to ₹1,000/month on everyday purchases",
            "1% fuel surcharge waiver",
            "EMI conversion on purchases above ₹2,500"
        ],
        "best_for": "Everyday spenders who want cashback",
        "apply_url": "https://www.hdfcbank.com/personal/pay/cards/credit-cards/moneyback-plus-credit-card",
        "eligibility": "Salaried ₹25,000+/month; age 21-60",
        "min_income": 25000,
        "segment": ["salaried"]
    },
    {
        "name": "Axis MyZone Credit Card",
        "bank": "Axis Bank",
        "card_type": "Lifestyle",
        "annual_fee": "₹500",
        "benefits": [
            "Grab Deals up to 20% off on partner brands",
            "Buy 1 Get 1 on movie tickets (BookMyShow/Paytm)",
            "4 complimentary lounge visits/year",
            "Contactless payments"
        ],
        "best_for": "Young professionals who love entertainment",
        "apply_url": "https://www.axisbank.com/retail/cards/credit-card/axis-bank-my-zone-credit-card",
        "eligibility": "Salaried ₹15,000+/month; age 18-70",
        "min_income": 15000,
        "segment": ["salaried", "business"]
    },
    {
        "name": "SBI Cashback Credit Card",
        "bank": "SBI",
        "card_type": "Cashback",
        "annual_fee": "₹999 (waived on ₹2L annual spend)",
        "benefits": [
            "5% cashback on all online purchases",
            "1% cashback on offline purchases",
            "Fuel surcharge waiver at any petrol pump",
            "No capping on online cashback (up to ₹5,000/cycle)"
        ],
        "best_for": "Heavy online spenders",
        "apply_url": "https://www.sbicard.com/en/personal/credit-cards/cashback/cashback-sbi-card.page",
        "eligibility": "Salaried ₹30,000+/month",
        "min_income": 30000,
        "segment": ["salaried"]
    },
    {
        "name": "Kotak 811 #DreamDifferent Credit Card",
        "bank": "Kotak Mahindra Bank",
        "card_type": "Basic",
        "annual_fee": "Nil (lifetime free)",
        "benefits": [
            "No annual or joining fee — lifetime free",
            "1% cashback on all spends (online & offline)",
            "Instant virtual card issued in minutes",
            "Easy EMI conversion"
        ],
        "best_for": "First-time credit card users with low income",
        "apply_url": "https://www.kotak.com/en/personal-banking/cards/credit-cards/dream-different-credit-card.html",
        "eligibility": "Salaried ₹15,000+/month; age 21-65",
        "min_income": 15000,
        "segment": ["salaried", "business", "farming"]
    },
    {
        "name": "Bank of Baroda Easy Credit Card",
        "bank": "Bank of Baroda",
        "card_type": "Basic",
        "annual_fee": "₹250",
        "benefits": [
            "Reward points on every ₹100 spent",
            "Fuel surcharge waiver",
            "Personal accident cover of ₹2 lakh",
            "Low interest rate on revolving credit"
        ],
        "best_for": "Rural & semi-urban customers with modest income",
        "apply_url": "https://www.bankofbaroda.in/personal-banking/digital-products/cards/credit-card/bob-easy-credit-card",
        "eligibility": "Salaried ₹12,000+/month or SHG/farm income proof",
        "min_income": 12000,
        "segment": ["salaried", "farming", "daily_wages"]
    },
    {
        "name": "SBI Secured Credit Card (Against FD)",
        "bank": "SBI",
        "card_type": "Secured",
        "annual_fee": "Nil",
        "benefits": [
            "No income proof required — issued against FD as collateral",
            "Credit limit up to 80% of FD value",
            "Build credit score (CIBIL) from scratch",
            "Reward points on all purchases"
        ],
        "best_for": "People with no credit history or low/irregular income",
        "apply_url": "https://www.sbicard.com/en/personal/credit-cards/secured-credit-card.page",
        "eligibility": "Anyone with an SBI Fixed Deposit of ₹25,000+",
        "min_income": 0,
        "segment": ["salaried", "business", "farming", "daily_wages"]
    },
    {
        "name": "ICICI Platinum Chip Credit Card",
        "bank": "ICICI Bank",
        "card_type": "Basic",
        "annual_fee": "₹199 (waived on ₹50K spend)",
        "benefits": [
            "2 PAYBACK reward points per ₹100 spent",
            "Fuel surcharge waiver (1%)",
            "Insurance cover up to ₹1 lakh",
            "Good entry-level card for building credit"
        ],
        "best_for": "Entry-level credit card users",
        "apply_url": "https://www.icicibank.com/credit-card/platinum-chip-credit-card",
        "eligibility": "Salaried ₹15,000+/month",
        "min_income": 15000,
        "segment": ["salaried", "business"]
    },
]


# ============================================
# GOVERNMENT SCHEMES DATABASE (with apply links)
# ============================================
GOVT_SCHEMES_DB: List[dict] = [
    # -- SAVINGS & INVESTMENT --
    {
        "name": "Pradhan Mantri Jan Dhan Yojana (PMJDY)",
        "name_hi": "प्रधानमंत्री जन धन योजना",
        "ministry": "Ministry of Finance",
        "description": "Zero-balance savings bank account with RuPay debit card, accident insurance of ₹2 lakh, and overdraft facility up to ₹10,000.",
        "benefits": ["Zero-balance bank account", "RuPay debit card", "₹2 lakh accident insurance", "₹10,000 overdraft facility", "Direct Benefit Transfer (DBT)"],
        "eligibility": "Any Indian citizen aged 10+ who does not have a bank account",
        "how_to_apply": "Visit any bank branch or Banking Correspondent (BC) with Aadhaar/ID proof",
        "apply_url": "https://pmjdy.gov.in/",
        "category": "savings",
        "target": ["all"]
    },
    {
        "name": "Sukanya Samriddhi Yojana (SSY)",
        "name_hi": "सुकन्या समृद्धि योजना",
        "ministry": "Ministry of Finance",
        "description": "Small deposit scheme for girl child offering 8.2% interest (highest among small-savings), tax-free maturity, and Section 80C deduction.",
        "benefits": ["8.2% annual interest (FY 2024-25)", "Tax-free returns under EEE", "Section 80C deduction up to ₹1.5 lakh", "Partial withdrawal at 18 for education"],
        "eligibility": "Parents/guardians of girl child below age 10; max 2 accounts (one per girl child)",
        "how_to_apply": "Open at any Post Office or authorized bank with birth certificate of girl child + ID proof of guardian",
        "apply_url": "https://www.india.gov.in/sukanya-samriddhi-yojna",
        "category": "savings",
        "target": ["married", "children"]
    },
    {
        "name": "Public Provident Fund (PPF)",
        "name_hi": "सार्वजनिक भविष्य निधि",
        "ministry": "Ministry of Finance",
        "description": "Long-term savings scheme with guaranteed returns (7.1%), tax benefits, and sovereign safety. 15-year lock-in with partial withdrawal from 7th year.",
        "benefits": ["7.1% interest (compounded yearly)", "EEE tax benefit (exempt at all stages)", "Loan against PPF from 3rd year", "Sovereign guarantee — zero risk"],
        "eligibility": "Any Indian citizen (one account per person); NRIs not eligible for new accounts",
        "how_to_apply": "Open at Post Office or any nationalized bank with KYC documents",
        "apply_url": "https://www.india.gov.in/public-provident-fund-scheme",
        "category": "savings",
        "target": ["all"]
    },
    # -- INSURANCE --
    {
        "name": "Pradhan Mantri Jeevan Jyoti Bima Yojana (PMJJBY)",
        "name_hi": "प्रधानमंत्री जीवन ज्योति बीमा योजना",
        "ministry": "Ministry of Finance",
        "description": "Life insurance scheme offering ₹2 lakh death cover at just ₹436/year, auto-debited from bank account.",
        "benefits": ["₹2 lakh life cover", "Premium only ₹436/year", "Auto-debit from savings account", "No medical examination required"],
        "eligibility": "Age 18-50 with a bank account; annual auto-renewal till age 55",
        "how_to_apply": "Apply through your bank (net banking, branch, or SMS) — form available at all banks",
        "apply_url": "https://www.jansuraksha.gov.in/Forms-PMJJBY.aspx",
        "category": "insurance",
        "target": ["all"]
    },
    {
        "name": "Pradhan Mantri Suraksha Bima Yojana (PMSBY)",
        "name_hi": "प्रधानमंत्री सुरक्षा बीमा योजना",
        "ministry": "Ministry of Finance",
        "description": "Accident insurance at ₹20/year providing ₹2 lakh for accidental death and ₹1 lakh for partial disability.",
        "benefits": ["₹2 lakh accidental death cover", "₹1 lakh partial disability cover", "Premium only ₹20/year", "Auto-debit from bank account"],
        "eligibility": "Age 18-70 with a savings bank account",
        "how_to_apply": "Enroll through your bank via net banking, branch form, or SMS-based activation",
        "apply_url": "https://www.jansuraksha.gov.in/Forms-PMSBY.aspx",
        "category": "insurance",
        "target": ["all"]
    },
    {
        "name": "Ayushman Bharat — PM Jan Arogya Yojana (AB-PMJAY)",
        "name_hi": "आयुष्मान भारत — प्रधानमंत्री जन आरोग्य योजना",
        "ministry": "Ministry of Health & Family Welfare",
        "description": "World's largest health insurance scheme providing ₹5 lakh/family/year for secondary & tertiary hospitalisation. Completely cashless & paperless.",
        "benefits": ["₹5 lakh health cover per family per year", "Cashless & paperless at empanelled hospitals", "Covers pre & post hospitalisation", "No cap on family size or age"],
        "eligibility": "Bottom 40% families as per SECC 2011 data; check eligibility on official portal with Aadhaar/ration card",
        "how_to_apply": "Check eligibility at mera.pmjay.gov.in or visit nearest Ayushman Bharat Arogya Mitra at empanelled hospital",
        "apply_url": "https://mera.pmjay.gov.in/search/login",
        "category": "insurance",
        "target": ["all"]
    },
    # -- PENSION --
    {
        "name": "Atal Pension Yojana (APY)",
        "name_hi": "अटल पेंशन योजना",
        "ministry": "Ministry of Finance / PFRDA",
        "description": "Guaranteed pension of ₹1,000 to ₹5,000/month after age 60 for unorganised-sector workers. Government co-contributes 50% for eligible beneficiaries.",
        "benefits": ["Guaranteed monthly pension ₹1,000-₹5,000", "Government co-contribution (50%) for 5 years", "Spouse continues pension after death", "Tax benefit under Section 80CCD"],
        "eligibility": "Age 18-40; must have a savings bank account; not a taxpayer (for co-contribution)",
        "how_to_apply": "Apply through your bank (net banking or branch) with Aadhaar and mobile number",
        "apply_url": "https://www.npscra.nsdl.co.in/scheme-details.php",
        "category": "pension",
        "target": ["all"]
    },
    # -- WOMEN-SPECIFIC --
    {
        "name": "Mahila Samman Savings Certificate (MSSC)",
        "name_hi": "महिला सम्मान बचत प्रमाणपत्र",
        "ministry": "Ministry of Finance",
        "description": "Special 2-year deposit scheme for women & girls offering 7.5% interest with partial withdrawal facility. One-time scheme available till March 2025.",
        "benefits": ["7.5% fixed interest rate", "2-year maturity period", "Partial withdrawal after 1 year (up to 40%)", "Max deposit ₹2 lakh"],
        "eligibility": "Any woman or girl (minor account opened by guardian); Indian resident",
        "how_to_apply": "Visit any Post Office or authorised bank with ID proof and address proof",
        "apply_url": "https://www.india.gov.in/spotlight/mahila-samman-savings-certificate",
        "category": "women",
        "target": ["women"]
    },
    {
        "name": "PM Mudra Yojana (PMMY)",
        "name_hi": "प्रधानमंत्री मुद्रा योजना",
        "ministry": "Ministry of Finance",
        "description": "Collateral-free loans up to ₹10 lakh for micro/small business. Three categories: Shishu (up to ₹50K), Kishore (₹50K-₹5L), Tarun (₹5L-₹10L).",
        "benefits": ["No collateral required", "Shishu: up to ₹50,000", "Kishore: ₹50,000 - ₹5,00,000", "Tarun: ₹5,00,000 - ₹10,00,000", "Available at all banks, NBFCs, MFIs"],
        "eligibility": "Any Indian citizen with a business plan for non-farm income-generating activity",
        "how_to_apply": "Apply at any bank branch, NBFC, or MFI with business plan and KYC documents. Also available via Udyamimitra portal.",
        "apply_url": "https://www.mudra.org.in/",
        "category": "business",
        "target": ["business", "self_employed"]
    },
    # -- FARMERS --
    {
        "name": "PM-KISAN Samman Nidhi",
        "name_hi": "पीएम-किसान सम्मान निधि",
        "ministry": "Ministry of Agriculture & Farmers Welfare",
        "description": "Direct income support of ₹6,000/year (₹2,000 every 4 months) to all landholding farmer families via DBT.",
        "benefits": ["₹6,000/year in 3 installments", "Direct bank transfer", "No middlemen — DBT to Aadhaar-linked account", "Covers all landholding farmers"],
        "eligibility": "All landholding farmer families (subject to exclusion criteria for higher-income groups)",
        "how_to_apply": "Register online via PM-KISAN portal or through Common Service Centre (CSC) / Lekhpal",
        "apply_url": "https://pmkisan.gov.in/",
        "category": "farmer",
        "target": ["farming"]
    },
    {
        "name": "PM Fasal Bima Yojana (PMFBY)",
        "name_hi": "प्रधानमंत्री फसल बीमा योजना",
        "ministry": "Ministry of Agriculture & Farmers Welfare",
        "description": "Comprehensive crop insurance at very low premiums — 2% for Kharif, 1.5% for Rabi, and 5% for commercial/horticultural crops.",
        "benefits": ["Low premium: 2% Kharif, 1.5% Rabi", "Coverage for all natural calamities", "Use of technology (satellite, drones) for fast claim settlement", "Covers pre-sowing to post-harvest losses"],
        "eligibility": "All farmers (including sharecroppers & tenant farmers) growing notified crops",
        "how_to_apply": "Apply through your bank (crop loan auto-enrolled) or CSC, insurance company portal, or PMFBY app",
        "apply_url": "https://pmfby.gov.in/",
        "category": "farmer",
        "target": ["farming"]
    },
    {
        "name": "Kisan Credit Card (KCC)",
        "name_hi": "किसान क्रेडिट कार्ड",
        "ministry": "Ministry of Agriculture / NABARD",
        "description": "Flexible credit card for farmers providing short-term crop loans at 4% effective interest (with prompt repayment). Also covers animal husbandry & fisheries.",
        "benefits": ["Crop loan at 4% effective interest", "Covers crop, animal husbandry, fisheries", "Revolving credit — withdraw as needed", "Personal accident insurance of ₹50,000", "Available at all banks"],
        "eligibility": "All farmers — individual or joint borrowers, tenant farmers, SHGs",
        "how_to_apply": "Apply at any bank branch with land records, ID proof, and passport-size photos. Also via PM-KISAN portal.",
        "apply_url": "https://pmkisan.gov.in/",
        "category": "farmer",
        "target": ["farming"]
    },
    # -- EDUCATION --
    {
        "name": "PM Vidyalaxmi — Education Loan",
        "name_hi": "प्रधानमंत्री विद्यालक्ष्मी — शिक्षा ऋण",
        "ministry": "Ministry of Education / Ministry of Finance",
        "description": "Single-window portal to apply for education loans from multiple banks. Covers tuition, hostel, books, and other expenses for higher education in India & abroad.",
        "benefits": ["Apply to multiple banks in one application", "Loans up to ₹20 lakh (domestic) / ₹30 lakh (abroad)", "Interest subsidy for economically weaker sections", "Moratorium during study + 1 year"],
        "eligibility": "Indian nationals with admission to recognised institutions; co-applicant required for loans above ₹7.5 lakh",
        "how_to_apply": "Register on Vidyalaxmi portal, fill in details, and submit to multiple banks simultaneously",
        "apply_url": "https://www.vidyalakshmi.co.in/Students/",
        "category": "education",
        "target": ["all", "children"]
    },
    # -- SENIOR CITIZENS --
    {
        "name": "Pradhan Mantri Vaya Vandana Yojana (PMVVY)",
        "name_hi": "प्रधानमंत्री वय वंदना योजना",
        "ministry": "Ministry of Finance / LIC",
        "description": "Pension scheme for senior citizens providing guaranteed 7.4% return for 10 years. Managed by LIC with sovereign backing.",
        "benefits": ["Guaranteed 7.4% annual return", "Monthly/quarterly/annual pension options", "Loan facility up to 75% of purchase price", "Exempt from GST"],
        "eligibility": "Indian citizens aged 60 and above; max investment ₹15 lakh",
        "how_to_apply": "Purchase online via LIC website or visit any LIC branch with age proof and KYC",
        "apply_url": "https://www.licindia.in/Products/Pension-Plans/Pradhan-Mantri-Vaya-Vandana-Yojana",
        "category": "pension",
        "target": ["senior"]
    },
    {
        "name": "Stand-Up India Scheme",
        "name_hi": "स्टैंड-अप इंडिया योजना",
        "ministry": "Ministry of Finance / SIDBI",
        "description": "Bank loans between ₹10 lakh and ₹1 crore to SC/ST and women entrepreneurs for greenfield enterprises in manufacturing, services, or trading.",
        "benefits": ["Loan ₹10 lakh to ₹1 crore", "For SC/ST and women entrepreneurs", "Composite loan (term + working capital)", "Repayment up to 7 years", "Margin money 25% (can include MUDRA)"],
        "eligibility": "SC/ST or women entrepreneurs aged 18+; greenfield (first-time) enterprise",
        "how_to_apply": "Apply via Stand-Up India portal or at any Scheduled Commercial Bank branch",
        "apply_url": "https://www.standupmitra.in/",
        "category": "business",
        "target": ["women", "business"]
    },
]


# ============================================
# HELPER — build user context string
# ============================================
def _build_user_context(user: User, profile: FinancialProfile, assessment: LiteracyAssessment) -> dict:
    """Aggregate user data into a context dict for LLM prompts."""
    income_val = profile.monthly_income if profile else None
    return {
        "name": user.name or "User",
        "monthly_income": income_val,
        "income_source": profile.income_source if profile else None,
        "occupation": profile.occupation if profile else None,
        "marital_status": profile.marital_status if profile else None,
        "children_count": profile.children_count if profile else 0,
        "risk_appetite": profile.risk_appetite if profile else "medium",
        "literacy_level": assessment.literacy_level if assessment else "beginner",
    }


def _income_bucket(income: float) -> str:
    if income is None:
        return "unknown"
    if income < 10000:
        return "below_10k"
    if income < 25000:
        return "10k_25k"
    if income < 50000:
        return "25k_50k"
    return "above_50k"


def _map_income_source(source: str) -> str:
    """Normalise DB income_source to our segment keys."""
    if not source:
        return "salaried"
    src = source.lower()
    if "farm" in src or "agri" in src:
        return "farming"
    if "business" in src or "shop" in src:
        return "business"
    if "daily" in src or "wage" in src or "labour" in src:
        return "daily_wages"
    return "salaried"


# ============================================
# FILTERING LOGIC
# ============================================

def _filter_credit_cards(ctx: dict) -> List[dict]:
    income = ctx.get("monthly_income") or 0
    segment = _map_income_source(ctx.get("income_source"))

    matched = []
    for card in CREDIT_CARDS_DB:
        if income >= card["min_income"] and segment in card["segment"]:
            matched.append(card)
    # Always include Secured card as fallback for thin-file users
    secured = [c for c in CREDIT_CARDS_DB if c["card_type"] == "Secured"]
    for s in secured:
        if s not in matched:
            matched.append(s)
    return matched


def _filter_govt_schemes(ctx: dict) -> List[dict]:
    segment = _map_income_source(ctx.get("income_source"))
    marital = (ctx.get("marital_status") or "").lower()
    children = ctx.get("children_count") or 0

    matched = []
    for scheme in GOVT_SCHEMES_DB:
        targets = scheme.get("target", [])
        # "all" schemes always match
        if "all" in targets:
            matched.append(scheme)
            continue
        if segment in targets:
            matched.append(scheme)
            continue
        if "children" in targets and children > 0:
            matched.append(scheme)
            continue
        if "women" in targets:
            # Include women schemes for everyone — they can share with family
            matched.append(scheme)
            continue
    # De-duplicate
    seen = set()
    unique = []
    for s in matched:
        if s["name"] not in seen:
            seen.add(s["name"])
            unique.append(s)
    return unique


# ============================================
# LLM TRANSLATION HELPER
# ============================================

def _translate_to_hindi(items: List[dict], item_type: str = "credit_card") -> List[dict]:
    """Translate card/scheme fields to Hindi using Groq LLM in batches."""
    if not groq_client or not items:
        return items

    if item_type == "credit_card":
        fields_to_translate = ["best_for", "eligibility"]
        list_fields = ["benefits"]
    else:
        fields_to_translate = ["description", "eligibility", "how_to_apply"]
        list_fields = ["benefits"]

    result = list(items)  # copy
    BATCH_SIZE = 4

    for batch_start in range(0, len(items), BATCH_SIZE):
        batch = items[batch_start:batch_start + BATCH_SIZE]
        to_translate = []
        for i, item in enumerate(batch):
            obj = {"idx": i}
            for f in fields_to_translate:
                if item.get(f):
                    obj[f] = item[f]
            for f in list_fields:
                if item.get(f):
                    obj[f] = item[f]
            to_translate.append(obj)

        prompt = f"""Translate to simple Hindi (Devanagari). Keep bank names, amounts (₹), numbers, URLs unchanged.
Return ONLY a JSON array — no explanation, no markdown.

{json.dumps(to_translate, ensure_ascii=False)}"""

        try:
            resp = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=3000,
            )
            raw = resp.choices[0].message.content.strip()
            # Extract JSON from response (may have markdown fences)
            if "```" in raw:
                raw = raw.split("```json")[-1].split("```")[0] if "```json" in raw else raw.split("```")[1].split("```")[0]
            raw = raw.strip()
            translated = json.loads(raw)

            for i, item in enumerate(batch):
                tr = next((t for t in translated if t.get("idx") == i), None)
                if tr:
                    item_copy = dict(item)
                    for f in fields_to_translate + list_fields:
                        if f in tr:
                            item_copy[f] = tr[f]
                    result[batch_start + i] = item_copy
        except Exception as e:
            print(f"⚠️ Hindi translation batch failed: {e}")
            # Keep originals for this batch

    return result


# ============================================
# LLM SUMMARISER
# ============================================

def _llm_credit_card_summary(ctx: dict, cards: List[dict], language: str) -> str:
    if not groq_client:
        return None

    card_names = [f"{c['name']} ({c['bank']})" for c in cards]
    lang_instruction = "Respond in Hindi." if language == "hi" else "Respond in English."

    prompt = f"""You are FinSakhi, a friendly Indian financial advisor for rural and semi-urban users.

User profile:
- Name: {ctx['name']}
- Monthly income: ₹{ctx.get('monthly_income', 'unknown')}
- Income source: {ctx.get('income_source', 'unknown')}
- Occupation: {ctx.get('occupation', 'unknown')}
- Financial literacy level: {ctx.get('literacy_level', 'beginner')}

Recommended credit cards: {', '.join(card_names)}

In 3-4 simple sentences, explain which card is BEST for this user and why. Keep language very simple (8th grade level). {lang_instruction}"""

    try:
        resp = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=300,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        print(f"⚠️ LLM credit card summary failed: {e}")
        return None


def _llm_scheme_summary(ctx: dict, schemes: List[dict], language: str) -> str:
    if not groq_client:
        return None

    scheme_names = [s["name"] for s in schemes[:8]]
    lang_instruction = "Respond in Hindi." if language == "hi" else "Respond in English."

    prompt = f"""You are FinSakhi, a friendly Indian financial advisor for rural and semi-urban users.

User profile:
- Name: {ctx['name']}
- Monthly income: ₹{ctx.get('monthly_income', 'unknown')}
- Income source: {ctx.get('income_source', 'unknown')}
- Marital status: {ctx.get('marital_status', 'unknown')}
- Children: {ctx.get('children_count', 0)}
- Financial literacy level: {ctx.get('literacy_level', 'beginner')}

Eligible government schemes: {', '.join(scheme_names)}

In 4-5 simple sentences, tell the user the TOP 3 schemes they should apply for first and why. Mention the benefit amounts. Keep language very simple (8th grade level). {lang_instruction}"""

    try:
        resp = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=400,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        print(f"⚠️ LLM scheme summary failed: {e}")
        return None


# ============================================
# API ENDPOINTS
# ============================================

@router.post("/credit-cards", response_model=CreditCardResponse)
def recommend_credit_cards(req: RecommendationRequest, db: Session = Depends(get_db)):
    """
    Recommend credit cards based on user's financial profile.
    Returns filtered cards with eligibility info and apply links.
    """
    user = db.query(User).filter(User.id == req.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    profile = db.query(FinancialProfile).filter(FinancialProfile.user_id == req.user_id).first()
    assessment = db.query(LiteracyAssessment).filter(
        LiteracyAssessment.user_id == req.user_id
    ).order_by(LiteracyAssessment.completed_at.desc()).first()

    ctx = _build_user_context(user, profile, assessment)
    matched_cards = _filter_credit_cards(ctx)

    # Translate fields if Hindi
    lang = req.language or "en"
    if lang == "hi":
        matched_cards = _translate_to_hindi(matched_cards, "credit_card")

    # Build response cards
    cards = []
    for c in matched_cards:
        cards.append(CreditCard(
            name=c["name"],
            bank=c["bank"],
            card_type=c["card_type"],
            annual_fee=c["annual_fee"],
            benefits=c["benefits"],
            best_for=c["best_for"],
            apply_url=c["apply_url"],
            eligibility=c["eligibility"],
        ))

    # AI summary
    ai_summary = _llm_credit_card_summary(ctx, matched_cards, lang)

    return CreditCardResponse(
        success=True,
        cards=cards,
        ai_summary=ai_summary,
        language=lang,
    )


@router.post("/govt-schemes", response_model=GovtSchemeResponse)
def recommend_govt_schemes(req: RecommendationRequest, db: Session = Depends(get_db)):
    """
    Recommend eligible government schemes based on user profile.
    Returns scheme details with direct apply links.
    """
    user = db.query(User).filter(User.id == req.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    profile = db.query(FinancialProfile).filter(FinancialProfile.user_id == req.user_id).first()
    assessment = db.query(LiteracyAssessment).filter(
        LiteracyAssessment.user_id == req.user_id
    ).order_by(LiteracyAssessment.completed_at.desc()).first()

    ctx = _build_user_context(user, profile, assessment)
    matched_schemes = _filter_govt_schemes(ctx)

    # Translate fields if Hindi
    lang = req.language or "en"
    if lang == "hi":
        matched_schemes = _translate_to_hindi(matched_schemes, "govt_scheme")

    schemes = []
    for s in matched_schemes:
        schemes.append(GovernmentScheme(
            name=s.get("name_hi") if lang == "hi" and s.get("name_hi") else s["name"],
            name_hi=s.get("name_hi"),
            ministry=s["ministry"],
            description=s["description"],
            benefits=s["benefits"],
            eligibility=s["eligibility"],
            how_to_apply=s["how_to_apply"],
            apply_url=s["apply_url"],
            category=s["category"],
        ))

    ai_summary = _llm_scheme_summary(ctx, matched_schemes, lang)

    return GovtSchemeResponse(
        success=True,
        schemes=schemes,
        ai_summary=ai_summary,
        language=lang,
    )


@router.get("/schemes/all")
def list_all_schemes():
    """List every government scheme in the database (no auth needed — for browsing)."""
    return {
        "success": True,
        "total": len(GOVT_SCHEMES_DB),
        "schemes": [
            {
                "name": s["name"],
                "name_hi": s.get("name_hi"),
                "category": s["category"],
                "description": s["description"],
                "apply_url": s["apply_url"],
            }
            for s in GOVT_SCHEMES_DB
        ],
    }


@router.get("/cards/all")
def list_all_cards():
    """List every credit card in the database (no auth needed — for browsing)."""
    return {
        "success": True,
        "total": len(CREDIT_CARDS_DB),
        "cards": [
            {
                "name": c["name"],
                "bank": c["bank"],
                "card_type": c["card_type"],
                "annual_fee": c["annual_fee"],
                "best_for": c["best_for"],
                "apply_url": c["apply_url"],
            }
            for c in CREDIT_CARDS_DB
        ],
    }
