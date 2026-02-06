"""
FinSakhi Chatbot API — Context-Aware Financial Assistant
Multi-turn conversations with full user context: profile, assessment,
learning progress, financial health, gamification, and investments.
Powered by Groq (Llama 3.3 70B).
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.database import (
    get_db, User, FinancialProfile, AssessmentSession,
    LiteracyAssessment, UserFinancialHealth, UserGamification,
    LearningProgress, Module, Lesson, Portfolio, Investment,
    ChatMessage,
)
from typing import Optional, List
import os, json, uuid
from datetime import datetime
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

router = APIRouter(prefix="/api/chat", tags=["Chatbot"])

# ============================================
# Groq LLM
# ============================================
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
if groq_client:
    print("✅ Groq API configured for chatbot")
else:
    print("⚠️ GROQ_API_KEY not set — chatbot will return errors")

# Max conversation history turns to send to LLM (to stay within token limits)
MAX_HISTORY_TURNS = 12  # 12 messages ≈ 6 back-and-forth turns


# ============================================
# Pydantic Schemas
# ============================================

class ChatRequest(BaseModel):
    user_id: int
    message: str
    conversation_id: Optional[str] = None  # None → start new conversation
    language: Optional[str] = "en"

class ChatResponse(BaseModel):
    conversation_id: str
    reply: str
    user_context_used: dict
    suggestions: List[str] = []

class ConversationSummary(BaseModel):
    conversation_id: str
    message_count: int
    started_at: str
    last_message_at: str
    preview: str  # First user message as preview


# ============================================
# DEEP USER CONTEXT BUILDER
# ============================================

def _build_full_user_context(user_id: int, db: Session) -> Optional[dict]:
    """
    Build the FULL context of a user from every table:
    - User basics (name, phone, language)
    - Financial profile (income, occupation, risk, family)
    - Assessment results (literacy level, score, category breakdown)
    - Learning progress (lessons completed, pillars covered, current level)
    - Financial health (health score, revision mode, level unlocks)
    - Gamification (XP, streak, level)
    - Portfolio & Investments
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None

    ctx = {
        "name": user.name or "User",
        "phone": user.phone,
        "language": user.language or "en",
        "member_since": user.created_at.strftime("%Y-%m-%d") if user.created_at else "unknown",
    }

    # ── Financial Profile ──
    profile = db.query(FinancialProfile).filter(FinancialProfile.user_id == user_id).first()
    if profile:
        ctx["financial_profile"] = {
            "monthly_income": profile.monthly_income,
            "income_source": profile.income_source,
            "risk_appetite": profile.risk_appetite,
            "occupation": profile.occupation,
            "marital_status": profile.marital_status,
            "children_count": profile.children_count,
        }
    else:
        ctx["financial_profile"] = None  # Assessment not yet done

    # ── Latest Assessment ──
    assessment = (
        db.query(AssessmentSession)
        .filter(AssessmentSession.user_id == user_id, AssessmentSession.status == "completed")
        .order_by(desc(AssessmentSession.completed_at))
        .first()
    )
    if assessment:
        questions_asked = json.loads(assessment.questions_asked or "[]")
        # Build category breakdown
        category_scores = {}
        for qa in questions_asked:
            cat = qa.get("category", "general")
            if cat not in category_scores:
                category_scores[cat] = {"correct": 0, "total": 0}
            category_scores[cat]["total"] += 1
            if qa.get("is_correct"):
                category_scores[cat]["correct"] += 1

        # Find weak & strong areas
        weak_areas = [c for c, s in category_scores.items() if s["total"] > 0 and s["correct"] / s["total"] < 0.5]
        strong_areas = [c for c, s in category_scores.items() if s["total"] > 0 and s["correct"] / s["total"] >= 0.7]

        ctx["assessment"] = {
            "literacy_level": assessment.literacy_level,
            "score": assessment.total_score,
            "total_questions": 8,
            "percentage": round((assessment.total_score / 8) * 100, 1),
            "category_scores": category_scores,
            "weak_areas": weak_areas,
            "strong_areas": strong_areas,
            "completed_at": assessment.completed_at.strftime("%Y-%m-%d") if assessment.completed_at else None,
        }
    else:
        ctx["assessment"] = None

    # ── Literacy Assessment (budgeting/investing scores) ──
    literacy = (
        db.query(LiteracyAssessment)
        .filter(LiteracyAssessment.user_id == user_id)
        .order_by(desc(LiteracyAssessment.completed_at))
        .first()
    )
    if literacy:
        ctx["literacy_scores"] = {
            "budgeting": literacy.budgeting_score,
            "investing": literacy.investing_score,
        }

    # ── Financial Health ──
    health = db.query(UserFinancialHealth).filter(UserFinancialHealth.user_id == user_id).first()
    if health:
        ctx["financial_health"] = {
            "health_score": health.health_score,
            "lessons_completed": health.lessons_completed,
            "scenarios_correct": health.scenarios_correct,
            "scenarios_total": health.scenarios_total,
            "tools_used": health.tools_used,
            "unsafe_choices": health.unsafe_choices,
            "current_level": health.current_level,
            "beginner_unlocked": health.beginner_unlocked,
            "intermediate_unlocked": health.intermediate_unlocked,
            "advanced_unlocked": health.advanced_unlocked,
            "revision_mode": health.revision_mode,
        }

    # ── Learning Progress (which lessons/pillars done) ──
    progress_records = (
        db.query(LearningProgress, Lesson, Module)
        .join(Lesson, LearningProgress.lesson_id == Lesson.id)
        .join(Module, Lesson.module_id == Module.id)
        .filter(LearningProgress.user_id == user_id, LearningProgress.completed == True)
        .all()
    )
    if progress_records:
        pillars_done = set()
        lessons_detail = []
        for prog, lesson, module in progress_records:
            pillars_done.add(module.pillar)
            lessons_detail.append({
                "lesson": lesson.title_en,
                "pillar": module.pillar,
                "level": module.level,
                "scenario_correct": prog.scenario_correct,
                "tool_used": prog.tool_used,
            })
        ctx["learning"] = {
            "completed_lessons": len(lessons_detail),
            "pillars_covered": list(pillars_done),
            "recent_lessons": lessons_detail[-5:],  # Last 5 for brevity
        }
    else:
        ctx["learning"] = {"completed_lessons": 0, "pillars_covered": [], "recent_lessons": []}

    # Total lessons available
    total_lessons = db.query(Lesson).count()
    ctx["learning"]["total_lessons_available"] = total_lessons

    # ── Gamification ──
    gam = db.query(UserGamification).filter(UserGamification.user_id == user_id).first()
    if gam:
        ctx["gamification"] = {
            "total_xp": gam.total_xp,
            "current_level": gam.current_level,
            "login_streak": gam.login_streak,
        }

    # ── Portfolio & Investments ──
    portfolio = db.query(Portfolio).filter(Portfolio.user_id == user_id).first()
    investments = db.query(Investment).filter(Investment.user_id == user_id).all()
    if portfolio or investments:
        ctx["portfolio"] = {
            "total_invested": portfolio.total_invested if portfolio else 0,
            "current_value": portfolio.current_value if portfolio else 0,
            "total_returns": portfolio.total_returns if portfolio else 0,
            "holdings": [
                {
                    "asset": inv.asset_name,
                    "symbol": inv.asset_symbol,
                    "quantity": inv.quantity,
                    "buy_price": inv.buy_price,
                    "invested": inv.invested_amount,
                }
                for inv in investments
            ]
        }

    return ctx


# ============================================
# SYSTEM PROMPT BUILDER
# ============================================

def _build_system_prompt(user_context: dict, language: str = "en") -> str:
    """
    Craft a detailed system prompt that injects the user's full context
    so the LLM answers as a personalized financial advisor.
    """
    name = user_context.get("name", "User")
    lang_instruction = (
        "ALWAYS respond in Hindi (Devanagari script). Use simple Hindi that a village person understands."
        if language == "hi"
        else "Respond in simple English (grade 5 reading level). Use short sentences."
    )

    # Format financial profile
    profile = user_context.get("financial_profile")
    if profile:
        profile_block = f"""FINANCIAL PROFILE:
- Monthly Income: ₹{profile.get('monthly_income') or 'Not disclosed'}
- Income Source: {profile.get('income_source') or 'Unknown'}
- Occupation: {profile.get('occupation') or 'Unknown'}
- Risk Appetite: {profile.get('risk_appetite', 'medium')}
- Marital Status: {profile.get('marital_status') or 'Unknown'}
- Children: {profile.get('children_count', 0)}"""
    else:
        profile_block = "FINANCIAL PROFILE: Not yet collected (user hasn't completed assessment)"

    # Format assessment results
    assessment = user_context.get("assessment")
    if assessment:
        assessment_block = f"""ASSESSMENT RESULTS:
- Literacy Level: {assessment['literacy_level']}
- Score: {assessment['score']}/{assessment['total_questions']} ({assessment['percentage']}%)
- Weak Areas: {', '.join(assessment['weak_areas']) if assessment['weak_areas'] else 'None identified'}
- Strong Areas: {', '.join(assessment['strong_areas']) if assessment['strong_areas'] else 'None identified'}"""
    else:
        assessment_block = "ASSESSMENT: Not yet taken"

    # Format learning progress
    learning = user_context.get("learning", {})
    learning_block = f"""LEARNING PROGRESS:
- Lessons Completed: {learning.get('completed_lessons', 0)} / {learning.get('total_lessons_available', 16)}
- Pillars Covered: {', '.join(learning.get('pillars_covered', [])) or 'None yet'}"""
    if learning.get("recent_lessons"):
        learning_block += "\n- Recent lessons: " + ", ".join(
            l["lesson"] for l in learning["recent_lessons"]
        )

    # Format financial health
    health = user_context.get("financial_health")
    if health:
        health_block = f"""FINANCIAL HEALTH:
- Health Score: {health['health_score']}/100
- Current Level: {health['current_level']}
- Scenarios Correct: {health['scenarios_correct']}/{health['scenarios_total']}
- Tools Used: {health['tools_used']}
- Revision Mode: {'Yes — user is struggling, be extra supportive!' if health['revision_mode'] else 'No'}"""
    else:
        health_block = "FINANCIAL HEALTH: Not tracked yet"

    # Format gamification
    gam = user_context.get("gamification")
    gam_block = ""
    if gam:
        gam_block = f"""GAMIFICATION:
- Total XP: {gam['total_xp']}
- Level: {gam['current_level']}
- Login Streak: {gam['login_streak']} days"""

    # Format portfolio
    portfolio = user_context.get("portfolio")
    portfolio_block = ""
    if portfolio:
        portfolio_block = f"""PORTFOLIO:
- Total Invested: ₹{portfolio['total_invested']:,.0f}
- Current Value: ₹{portfolio['current_value']:,.0f}
- Returns: ₹{portfolio['total_returns']:,.0f}
- Holdings: {len(portfolio.get('holdings', []))} assets"""
        for h in portfolio.get("holdings", [])[:5]:
            portfolio_block += f"\n  • {h['asset']} — qty: {h['quantity']}, bought at ₹{h['buy_price']}"

    system_prompt = f"""You are FinSakhi (फिनसखी), a warm, friendly, and trustworthy financial literacy assistant for rural India (Bharat).

You are chatting with {name}. You know EVERYTHING about this user from the data below.
Use this context to give PERSONALIZED answers. Reference their specific situation.
For example, if they earn ₹15,000/month from farming, use farming examples and that income range.

{profile_block}

{assessment_block}

{learning_block}

{health_block}

{gam_block}

{portfolio_block}

YOUR PERSONALITY:
- You are like a wise, caring elder sister (दीदी) or elder brother (भैया) from the village
- You explain complex financial concepts using everyday examples (farming, ration shop, chai stall)
- You celebrate the user's progress ("You completed 5 lessons — great job!")
- If the user is in revision mode or struggling, be extra supportive and encouraging
- You NEVER judge the user for their income level or knowledge gaps
- You give actionable advice, not just theory ("Save ₹500 this month in your Jan Dhan account")

RULES:
1. {lang_instruction}
2. Keep responses SHORT — max 150 words unless user asks for detail
3. If user asks about investments, relate to their income and risk appetite
4. If user asks about something covered in their completed lessons, reference it ("Remember the savings lesson you completed?")
5. If user hasn't done their assessment yet, gently encourage them to take it
6. If user has weak areas from assessment, proactively offer tips on those topics
7. Always be encouraging, never condescending
8. For numbers, use ₹ symbol and Indian formatting (lakhs, not millions)
9. If you don't know something, say so honestly — don't make up financial data
10. End important advice with a simple action step the user can take TODAY

TOPICS YOU CAN HELP WITH:
- Savings, budgeting, expense tracking
- Understanding loans, EMI, interest rates
- Mutual funds, SIP, gold, silver investments
- Government schemes (Jan Dhan, PM-KISAN, Sukanya Samriddhi, etc.)
- Insurance basics
- Starting and managing a small business
- Digital payments (UPI, PhonePe, etc.)
- Tax basics for small earners
- Credit score and credit cards
- Children's education planning
- Emergency fund planning"""

    return system_prompt


# ============================================
# CONVERSATION HISTORY HELPERS
# ============================================

def _get_conversation_history(db: Session, conversation_id: str) -> list:
    """Fetch recent messages for this conversation, formatted for LLM."""
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.conversation_id == conversation_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )
    # Keep only the last N messages to respect token limits
    recent = messages[-MAX_HISTORY_TURNS:]
    return [{"role": msg.role, "content": msg.content} for msg in recent]


def _save_message(
    db: Session, user_id: int, conversation_id: str,
    role: str, content: str, language: str = "en",
    context_snapshot: dict = None,
):
    """Persist a chat message to the database."""
    msg = ChatMessage(
        user_id=user_id,
        conversation_id=conversation_id,
        role=role,
        content=content,
        language=language,
        context_snapshot=json.dumps(context_snapshot) if context_snapshot else None,
    )
    db.add(msg)
    db.commit()
    return msg


# ============================================
# SUGGESTED FOLLOW-UP GENERATOR
# ============================================

def _generate_suggestions(user_context: dict, language: str = "en") -> list:
    """Generate 3 contextual follow-up suggestions based on user state."""
    suggestions = []

    assessment = user_context.get("assessment")
    profile = user_context.get("financial_profile")
    learning = user_context.get("learning", {})
    health = user_context.get("financial_health")

    if language == "hi":
        if not assessment:
            suggestions.append("मेरा वित्तीय मूल्यांकन शुरू करो")
        if not profile:
            suggestions.append("मुझे बचत के बारे में बताओ")
        if assessment and assessment.get("weak_areas"):
            weak = assessment["weak_areas"][0]
            suggestions.append(f"मुझे {weak} के बारे में और बताओ")
        if learning.get("completed_lessons", 0) == 0:
            suggestions.append("मैं सीखना कहाँ से शुरू करूँ?")
        if profile and profile.get("monthly_income"):
            suggestions.append("मेरी आय से कितना बचत करूँ?")
        if health and health.get("revision_mode"):
            suggestions.append("मुझे दोबारा समझाओ")
        if learning.get("completed_lessons", 0) > 0:
            suggestions.append("मेरी प्रगति कैसी है?")
        suggestions.append("SIP क्या है?")
    else:
        if not assessment:
            suggestions.append("Help me take my financial assessment")
        if not profile:
            suggestions.append("Tell me about saving money")
        if assessment and assessment.get("weak_areas"):
            weak = assessment["weak_areas"][0]
            suggestions.append(f"Teach me more about {weak}")
        if learning.get("completed_lessons", 0) == 0:
            suggestions.append("Where should I start learning?")
        if profile and profile.get("monthly_income"):
            suggestions.append("How much should I save from my income?")
        if health and health.get("revision_mode"):
            suggestions.append("Can you explain that topic again?")
        if learning.get("completed_lessons", 0) > 0:
            suggestions.append("How is my progress?")
        suggestions.append("What is SIP and should I start one?")

    return suggestions[:3]


# ============================================
# ENDPOINTS
# ============================================

@router.post("/send", response_model=None)
async def send_message(data: ChatRequest, db: Session = Depends(get_db)):
    """
    💬 Send a message to FinSakhi chatbot.

    The chatbot has access to the user's FULL context:
    financial profile, assessment scores, learning progress,
    health score, gamification, and investments.

    - Pass `conversation_id` to continue a conversation.
    - Omit it (or pass null) to start a new conversation.
    - Supports both English and Hindi.

    Example:
    ```json
    {
      "user_id": 1,
      "message": "How much should I save every month?",
      "language": "en"
    }
    ```
    """
    if not data.message or len(data.message.strip()) < 1:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    if not groq_client:
        raise HTTPException(status_code=503, detail="Chatbot unavailable — GROQ_API_KEY not configured")

    # 1. Build full user context
    user_context = _build_full_user_context(data.user_id, db)
    if not user_context:
        raise HTTPException(status_code=404, detail="User not found. Please sign up first.")

    language = data.language or user_context.get("language", "en")

    # 2. Conversation ID (new or existing)
    conversation_id = data.conversation_id or f"conv_{data.user_id}_{uuid.uuid4().hex[:8]}"

    # 3. Get conversation history
    history = _get_conversation_history(db, conversation_id)

    # 4. Save user message
    _save_message(db, data.user_id, conversation_id, "user", data.message.strip(), language)

    # 5. Build messages for LLM
    system_prompt = _build_system_prompt(user_context, language)
    llm_messages = [{"role": "system", "content": system_prompt}]
    llm_messages.extend(history)
    llm_messages.append({"role": "user", "content": data.message.strip()})

    # 6. Call Groq
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=llm_messages,
            temperature=0.7,
            max_tokens=800,
        )
        reply = response.choices[0].message.content.strip()
    except Exception as e:
        print(f"⚠️ Groq chatbot error: {e}")
        # Friendly fallback
        reply = (
            "माफ़ कीजिए, अभी मुझसे बात नहीं हो पा रही। कृपया थोड़ी देर बाद कोशिश करें।"
            if language == "hi"
            else "Sorry, I'm having trouble responding right now. Please try again in a moment."
        )

    # 7. Save assistant reply
    _save_message(db, data.user_id, conversation_id, "assistant", reply, language)

    # 8. Generate contextual suggestions
    suggestions = _generate_suggestions(user_context, language)

    # 9. Build minimal context snapshot for response
    context_used = {
        "name": user_context.get("name"),
        "has_profile": user_context.get("financial_profile") is not None,
        "has_assessment": user_context.get("assessment") is not None,
        "literacy_level": (user_context.get("assessment") or {}).get("literacy_level"),
        "health_score": (user_context.get("financial_health") or {}).get("health_score"),
        "lessons_completed": user_context.get("learning", {}).get("completed_lessons", 0),
        "total_xp": (user_context.get("gamification") or {}).get("total_xp"),
    }

    return {
        "conversation_id": conversation_id,
        "reply": reply,
        "user_context_used": context_used,
        "suggestions": suggestions,
        "generated_at": datetime.utcnow().isoformat(),
    }


@router.get("/conversations/{user_id}")
async def get_user_conversations(
    user_id: int,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    📋 List all conversations for a user (most recent first).
    Returns conversation_id, message count, timestamps, and preview.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    from sqlalchemy import func as sqla_func

    # Get distinct conversations with stats
    conversations_raw = (
        db.query(
            ChatMessage.conversation_id,
            sqla_func.count(ChatMessage.id).label("msg_count"),
            sqla_func.min(ChatMessage.created_at).label("started_at"),
            sqla_func.max(ChatMessage.created_at).label("last_at"),
        )
        .filter(ChatMessage.user_id == user_id)
        .group_by(ChatMessage.conversation_id)
        .order_by(sqla_func.max(ChatMessage.created_at).desc())
        .limit(limit)
        .all()
    )

    conversations = []
    for conv_id, msg_count, started, last in conversations_raw:
        # Get first user message as preview
        first_msg = (
            db.query(ChatMessage)
            .filter(
                ChatMessage.conversation_id == conv_id,
                ChatMessage.role == "user",
            )
            .order_by(ChatMessage.created_at.asc())
            .first()
        )
        preview = first_msg.content[:100] if first_msg else ""

        conversations.append({
            "conversation_id": conv_id,
            "message_count": msg_count,
            "started_at": started.isoformat() if started else None,
            "last_message_at": last.isoformat() if last else None,
            "preview": preview,
        })

    return {
        "user_id": user_id,
        "total_conversations": len(conversations),
        "conversations": conversations,
    }


@router.get("/conversations/{user_id}/{conversation_id}")
async def get_conversation_messages(
    user_id: int,
    conversation_id: str,
    db: Session = Depends(get_db),
):
    """
    💬 Get all messages in a specific conversation.
    Returns the full chat history in chronological order.
    """
    messages = (
        db.query(ChatMessage)
        .filter(
            ChatMessage.user_id == user_id,
            ChatMessage.conversation_id == conversation_id,
        )
        .order_by(ChatMessage.created_at.asc())
        .all()
    )

    if not messages:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return {
        "conversation_id": conversation_id,
        "user_id": user_id,
        "message_count": len(messages),
        "messages": [
            {
                "id": msg.id,
                "role": msg.role,
                "content": msg.content,
                "language": msg.language,
                "created_at": msg.created_at.isoformat() if msg.created_at else None,
            }
            for msg in messages
        ],
    }


@router.delete("/conversations/{user_id}/{conversation_id}")
async def delete_conversation(
    user_id: int,
    conversation_id: str,
    db: Session = Depends(get_db),
):
    """🗑️ Delete a conversation and all its messages."""
    deleted = (
        db.query(ChatMessage)
        .filter(
            ChatMessage.user_id == user_id,
            ChatMessage.conversation_id == conversation_id,
        )
        .delete()
    )
    db.commit()

    if deleted == 0:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return {"deleted": True, "messages_removed": deleted}


@router.get("/context/{user_id}")
async def get_user_context_debug(user_id: int, db: Session = Depends(get_db)):
    """
    🔍 Debug endpoint: see the full context the chatbot uses for a user.
    Useful during development to verify what the LLM "knows" about the user.
    """
    ctx = _build_full_user_context(user_id, db)
    if not ctx:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "user_id": user_id,
        "context": ctx,
        "note": "This is the full context injected into every chatbot response for this user.",
    }
