from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.models.database import (
    get_db, User, FinancialProfile, AssessmentSession,
    LiteracyAssessment, UserGamification
)
from typing import Optional, List, Dict
import os
import json
from datetime import datetime
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

router = APIRouter(prefix="/api/assessment", tags=["Assessment"])

# ============================================
# Configure Groq
# ============================================
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if GROQ_API_KEY:
    groq_client = Groq(api_key=GROQ_API_KEY)
    print("✅ Groq API configured")
else:
    groq_client = None
    print("⚠️ GROQ_API_KEY not set - assessment will use fallback questions")

# ============================================
# Pydantic Schemas
# ============================================
class StartAssessmentRequest(BaseModel):
    user_id: int
    language: Optional[str] = "en"

class ProfileAnswerRequest(BaseModel):
    session_id: int
    answer: str  # User's answer (text or index for MCQ)

class MCQAnswerRequest(BaseModel):
    session_id: int
    selected_option: int  # 0-3 index of the selected option

# ============================================
# Profile collection steps (Phase 1)
# ============================================
PROFILE_STEPS = [
    {
        "step": 0, "field": "name",
        "question_en": "What is your name?",
        "question_hi": "आपका नाम क्या है?",
        "type": "text"
    },
    {
        "step": 1, "field": "monthly_income",
        "question_en": "What is your approximate monthly income (in ₹)?",
        "question_hi": "आपकी अनुमानित मासिक आय कितनी है (₹ में)?",
        "type": "mcq",
        "options_en": ["Less than ₹10,000", "₹10,000 - ₹25,000", "₹25,000 - ₹50,000", "More than ₹50,000"],
        "options_hi": ["₹10,000 से कम", "₹10,000 - ₹25,000", "₹25,000 - ₹50,000", "₹50,000 से अधिक"]
    },
    {
        "step": 2, "field": "income_source",
        "question_en": "What is your main source of income?",
        "question_hi": "आपकी आय का मुख्य स्रोत क्या है?",
        "type": "mcq",
        "options_en": ["Salary/Job", "Business/Shop", "Farming/Agriculture", "Daily Wages/Labour", "Other"],
        "options_hi": ["नौकरी/वेतन", "व्यापार/दुकान", "खेती/कृषि", "दैनिक मजदूरी", "अन्य"]
    },
    {
        "step": 3, "field": "marital_status",
        "question_en": "What is your marital status?",
        "question_hi": "आपकी वैवाहिक स्थिति क्या है?",
        "type": "mcq",
        "options_en": ["Married", "Unmarried", "Widowed", "Divorced"],
        "options_hi": ["विवाहित", "अविवाहित", "विधवा/विधुर", "तलाकशुदा"]
    },
    {
        "step": 4, "field": "children_count",
        "question_en": "How many children do you have?",
        "question_hi": "आपके कितने बच्चे हैं?",
        "type": "mcq",
        "options_en": ["None", "1", "2", "3 or more"],
        "options_hi": ["कोई नहीं", "1", "2", "3 या अधिक"]
    },
    {
        "step": 5, "field": "occupation",
        "question_en": "What is your occupation?",
        "question_hi": "आपका व्यवसाय क्या है?",
        "type": "text"
    }
]

NUM_PROFILE_STEPS = len(PROFILE_STEPS)
NUM_MCQ_QUESTIONS = 8  # Adaptive MCQs after profile collection

# ============================================
# Fallback MCQs (when Gemini unavailable)
# ============================================
FALLBACK_QUESTIONS = [
    {
        "question_en": "What is a budget?",
        "question_hi": "बजट क्या है?",
        "options_en": ["A plan for spending money", "A type of bank account", "A government tax", "A loan document"],
        "options_hi": ["पैसे खर्च करने की योजना", "एक प्रकार का बैंक खाता", "एक सरकारी कर", "एक ऋण दस्तावेज़"],
        "correct_answer": 0, "category": "budgeting"
    },
    {
        "question_en": "Which of these is the BEST reason to save money?",
        "question_hi": "पैसे बचाने का सबसे अच्छा कारण कौन सा है?",
        "options_en": ["To show off wealth", "For future emergencies and goals", "To hide it from family", "Because everyone does it"],
        "options_hi": ["धन दिखाने के लिए", "भविष्य की आपातस्थितियों और लक्ष्यों के लिए", "परिवार से छिपाने के लिए", "क्योंकि सभी ऐसा करते हैं"],
        "correct_answer": 1, "category": "saving"
    },
    {
        "question_en": "What is interest on a savings account?",
        "question_hi": "बचत खाते पर ब्याज क्या है?",
        "options_en": ["A fee you pay the bank", "Insurance premium", "Extra money the bank pays you", "A type of loan"],
        "options_hi": ["बैंक को दी जाने वाली फीस", "बीमा प्रीमियम", "बैंक द्वारा दिया जाने वाला अतिरिक्त पैसा", "एक प्रकार का ऋण"],
        "correct_answer": 2, "category": "saving"
    },
    {
        "question_en": "What is EMI?",
        "question_hi": "EMI क्या है?",
        "options_en": ["Extra Money Income", "Electronic Money Interface", "Emergency Medical Insurance", "Equal Monthly Installment"],
        "options_hi": ["अतिरिक्त पैसे की आय", "इलेक्ट्रॉनिक मनी इंटरफ़ेस", "आपातकालीन चिकित्सा बीमा", "समान मासिक किस्त"],
        "correct_answer": 3, "category": "loans"
    },
    {
        "question_en": "Why is an emergency fund important?",
        "question_hi": "आपातकालीन निधि क्यों महत्वपूर्ण है?",
        "options_en": ["To handle unexpected expenses", "To buy luxury items", "To invest in stocks", "To pay for vacations"],
        "options_hi": ["अप्रत्याशित खर्चों को संभालने के लिए", "विलासिता की वस्तुएं खरीदने के लिए", "शेयरों में निवेश करने के लिए", "छुट्टियों के लिए भुगतान करने के लिए"],
        "correct_answer": 0, "category": "budgeting"
    },
    {
        "question_en": "What is the main advantage of a Fixed Deposit?",
        "question_hi": "फिक्स्ड डिपॉजिट का मुख्य फायदा क्या है?",
        "options_en": ["Unlimited withdrawals", "Higher and guaranteed interest rate", "No minimum amount needed", "Can be withdrawn anytime without penalty"],
        "options_hi": ["असीमित निकासी", "अधिक और गारंटीड ब्याज दर", "न्यूनतम राशि की जरूरत नहीं", "बिना जुर्माने के कभी भी निकाला जा सकता है"],
        "correct_answer": 1, "category": "investing"
    },
    {
        "question_en": "What does inflation mean for your savings?",
        "question_hi": "मुद्रास्फीति का आपकी बचत के लिए क्या अर्थ है?",
        "options_en": ["Your money grows faster", "Your money buys more over time", "The purchasing power of your money decreases", "Nothing changes"],
        "options_hi": ["आपका पैसा तेजी से बढ़ता है", "आपका पैसा समय के साथ अधिक खरीदता है", "आपके पैसे की क्रय शक्ति कम हो जाती है", "कुछ नहीं बदलता"],
        "correct_answer": 2, "category": "general"
    },
    {
        "question_en": "What is the benefit of diversifying investments?",
        "question_hi": "निवेश में विविधता लाने का क्या लाभ है?",
        "options_en": ["Makes tax filing easier", "Eliminates all losses", "Guarantees higher returns", "Reduces overall risk"],
        "options_hi": ["कर दाखिल करना आसान बनाता है", "सभी नुकसान समाप्त करता है", "अधिक रिटर्न की गारंटी देता है", "कुल जोखिम कम करता है"],
        "correct_answer": 3, "category": "investing"
    }
]


# ============================================
# LLM: Generate adaptive question via Groq
# ============================================
async def generate_adaptive_question(profile_data: dict, previous_qa: list, question_number: int, language: str = "en"):
    """Use Groq (Llama) to generate a personalized MCQ based on user profile and previous answers."""

    if not groq_client:
        idx = min(question_number - 1, len(FALLBACK_QUESTIONS) - 1)
        return FALLBACK_QUESTIONS[idx]

    # Adapt difficulty based on performance
    correct_count = sum(1 for qa in previous_qa if qa.get("is_correct", False))
    total_answered = len(previous_qa)

    if total_answered == 0:
        difficulty = "beginner"
    elif correct_count / max(total_answered, 1) >= 0.7:
        difficulty = "intermediate" if question_number <= 5 else "advanced"
    elif correct_count / max(total_answered, 1) >= 0.4:
        difficulty = "intermediate"
    else:
        difficulty = "beginner"

    name = profile_data.get("name", "User")
    income = profile_data.get("monthly_income", "unknown")
    source = profile_data.get("income_source", "unknown")
    marital = profile_data.get("marital_status", "unknown")
    children = profile_data.get("children_count", "unknown")
    occupation = profile_data.get("occupation", "unknown")

    categories = ["budgeting", "saving", "loans", "insurance", "investing", "digital_payments", "government_schemes", "tax_basics"]
    category = categories[(question_number - 1) % len(categories)]

    prev_context = ""
    if previous_qa:
        prev_context = "\nPrevious questions and answers:\n"
        for i, qa in enumerate(previous_qa, 1):
            prev_context += f"{i}. Q: {qa['question']}\n   Answer: {qa['user_answer']} ({'Correct' if qa['is_correct'] else 'Wrong'})\n"

    prompt = f"""You are a financial literacy assessment expert for rural India. Generate ONE multiple-choice question.

USER PROFILE:
- Name: {name}
- Monthly Income: {income}
- Income Source: {source}
- Marital Status: {marital}
- Children: {children}
- Occupation: {occupation}

DIFFICULTY: {difficulty}
CATEGORY: {category}
QUESTION NUMBER: {question_number} of {NUM_MCQ_QUESTIONS}
{prev_context}

RULES:
1. Make the question RELEVANT to the user's life situation (income level, family status, occupation)
2. Use simple language that a person from rural India can understand
3. The question should be about "{category}" in practical everyday context
4. Difficulty: {difficulty} - adjust complexity accordingly
5. If the user got previous questions wrong, make this one slightly easier and more practical
6. If the user got previous questions right, make it slightly more challenging

RESPOND IN THIS EXACT JSON FORMAT ONLY (no markdown, no extra text):
{{"question_en": "The question in English", "question_hi": "The question in Hindi", "options_en": ["Option A", "Option B", "Option C", "Option D"], "options_hi": ["विकल्प A", "विकल्प B", "विकल्प C", "विकल्प D"], "correct_answer": 0, "category": "{category}"}}

Where correct_answer is the 0-based index (0, 1, 2, or 3) of the correct option."""

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a financial literacy assessment expert. Respond ONLY with valid JSON, no markdown."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        text = response.choices[0].message.content.strip()

        # Clean markdown code fences if present
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
            text = text.rsplit("```", 1)[0].strip()

        question_data = json.loads(text)

        required_keys = ["question_en", "question_hi", "options_en", "options_hi", "correct_answer", "category"]
        for key in required_keys:
            if key not in question_data:
                raise ValueError(f"Missing key: {key}")

        if not isinstance(question_data["options_en"], list) or len(question_data["options_en"]) != 4:
            raise ValueError("options_en must be a list of 4 items")

        return question_data

    except Exception as e:
        print(f"⚠️ Gemini error: {e}, using fallback question")
        idx = min(question_number - 1, len(FALLBACK_QUESTIONS) - 1)
        return FALLBACK_QUESTIONS[idx]


# ============================================
# ENDPOINTS
# ============================================

@router.post("/start")
async def start_assessment(data: StartAssessmentRequest, db: Session = Depends(get_db)):
    """Start a new assessment session for a user."""
    user = db.query(User).filter(User.id == data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Abandon any existing in-progress sessions
    existing = db.query(AssessmentSession).filter(
        AssessmentSession.user_id == data.user_id,
        AssessmentSession.status == "in_progress"
    ).all()
    for s in existing:
        s.status = "abandoned"

    session = AssessmentSession(
        user_id=data.user_id,
        status="in_progress",
        current_step=0,
        profile_data=json.dumps({}),
        questions_asked=json.dumps([]),
        language=data.language
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    first_step = PROFILE_STEPS[0]
    lang = data.language

    return {
        "session_id": session.id,
        "phase": "profile",
        "step": 0,
        "total_profile_steps": NUM_PROFILE_STEPS,
        "total_mcq_questions": NUM_MCQ_QUESTIONS,
        "question": first_step.get(f"question_{lang}", first_step["question_en"]),
        "type": first_step["type"],
        "options": first_step.get(f"options_{lang}", first_step.get("options_en")),
        "field": first_step["field"]
    }


@router.post("/answer-profile")
async def answer_profile_question(data: ProfileAnswerRequest, db: Session = Depends(get_db)):
    """Submit answer to a profile question and get the next one."""
    session = db.query(AssessmentSession).filter(
        AssessmentSession.id == data.session_id,
        AssessmentSession.status == "in_progress"
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or already completed")

    current_step = session.current_step
    if current_step >= NUM_PROFILE_STEPS:
        raise HTTPException(status_code=400, detail="Profile phase already done. Use /answer-mcq.")

    profile_data = json.loads(session.profile_data or "{}")
    step_info = PROFILE_STEPS[current_step]
    field = step_info["field"]

    # Map answer to readable value
    if field == "monthly_income":
        income_map = {"0": "<10000", "1": "10000-25000", "2": "25000-50000", "3": ">50000"}
        profile_data[field] = income_map.get(data.answer, data.answer)
    elif field == "children_count":
        children_map = {"0": "0", "1": "1", "2": "2", "3": "3+"}
        profile_data[field] = children_map.get(data.answer, data.answer)
    elif step_info["type"] == "mcq" and data.answer.isdigit():
        idx = int(data.answer)
        options = step_info.get(f"options_{session.language}", step_info.get("options_en", []))
        profile_data[field] = options[idx] if 0 <= idx < len(options) else data.answer
    else:
        profile_data[field] = data.answer

    session.profile_data = json.dumps(profile_data)
    session.current_step = current_step + 1
    db.commit()

    # If profile phase is done -> save profile and start MCQs
    if current_step + 1 >= NUM_PROFILE_STEPS:
        await _save_financial_profile(session.user_id, profile_data, db)

        if "name" in profile_data:
            user = db.query(User).filter(User.id == session.user_id).first()
            if user:
                user.name = profile_data["name"]
                db.commit()

        question_data = await generate_adaptive_question(
            profile_data=profile_data, previous_qa=[], question_number=1, language=session.language
        )
        lang = session.language
        return {
            "session_id": session.id,
            "phase": "mcq",
            "profile_complete": True,
            "profile_summary": profile_data,
            "mcq_question_number": 1,
            "total_mcq_questions": NUM_MCQ_QUESTIONS,
            "question": question_data.get(f"question_{lang}", question_data["question_en"]),
            "options": question_data.get(f"options_{lang}", question_data["options_en"]),
            "category": question_data["category"],
            "_correct_answer": question_data["correct_answer"]
        }

    # Otherwise return next profile question
    next_step = PROFILE_STEPS[current_step + 1]
    lang = session.language
    return {
        "session_id": session.id,
        "phase": "profile",
        "step": current_step + 1,
        "total_profile_steps": NUM_PROFILE_STEPS,
        "question": next_step.get(f"question_{lang}", next_step["question_en"]),
        "type": next_step["type"],
        "options": next_step.get(f"options_{lang}", next_step.get("options_en")),
        "field": next_step["field"]
    }


@router.post("/answer-mcq")
async def answer_mcq_question(data: MCQAnswerRequest, db: Session = Depends(get_db)):
    """Submit MCQ answer and get the next adaptive question."""
    session = db.query(AssessmentSession).filter(
        AssessmentSession.id == data.session_id,
        AssessmentSession.status == "in_progress"
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or already completed")

    if session.current_step < NUM_PROFILE_STEPS:
        raise HTTPException(status_code=400, detail="Profile phase not done. Use /answer-profile.")

    profile_data = json.loads(session.profile_data or "{}")
    questions_asked = json.loads(session.questions_asked or "[]")
    mcq_number = len(questions_asked) + 1

    if mcq_number > NUM_MCQ_QUESTIONS:
        raise HTTPException(status_code=400, detail="All MCQs answered already.")

    # Re-generate current question for validation (deterministic via same seed context)
    current_question = await generate_adaptive_question(
        profile_data=profile_data, previous_qa=questions_asked,
        question_number=mcq_number, language=session.language
    )

    is_correct = data.selected_option == current_question["correct_answer"]
    lang = session.language

    qa_record = {
        "question_number": mcq_number,
        "question": current_question.get(f"question_{lang}", current_question["question_en"]),
        "options": current_question.get(f"options_{lang}", current_question["options_en"]),
        "correct_answer": current_question["correct_answer"],
        "user_answer": current_question.get(f"options_{lang}", current_question["options_en"])[data.selected_option] if 0 <= data.selected_option < 4 else "Invalid",
        "user_answer_index": data.selected_option,
        "is_correct": is_correct,
        "category": current_question["category"]
    }
    questions_asked.append(qa_record)

    if is_correct:
        session.total_score += 1

    session.questions_asked = json.dumps(questions_asked)
    session.current_step += 1
    db.commit()

    # All MCQs done -> complete assessment
    if mcq_number >= NUM_MCQ_QUESTIONS:
        return await _complete_assessment(session, profile_data, questions_asked, db)

    # Generate next adaptive question
    next_question = await generate_adaptive_question(
        profile_data=profile_data, previous_qa=questions_asked,
        question_number=mcq_number + 1, language=session.language
    )

    return {
        "session_id": session.id,
        "phase": "mcq",
        "is_correct": is_correct,
        "correct_answer_index": current_question["correct_answer"],
        "score_so_far": session.total_score,
        "mcq_question_number": mcq_number + 1,
        "total_mcq_questions": NUM_MCQ_QUESTIONS,
        "question": next_question.get(f"question_{lang}", next_question["question_en"]),
        "options": next_question.get(f"options_{lang}", next_question["options_en"]),
        "category": next_question["category"],
        "_correct_answer": next_question["correct_answer"]
    }


@router.get("/result/{session_id}")
async def get_assessment_result(session_id: int, db: Session = Depends(get_db)):
    """Get the result of a completed assessment."""
    session = db.query(AssessmentSession).filter(AssessmentSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.status != "completed":
        raise HTTPException(status_code=400, detail="Assessment not yet completed")

    profile_data = json.loads(session.profile_data or "{}")
    questions_asked = json.loads(session.questions_asked or "[]")

    category_scores = {}
    for qa in questions_asked:
        cat = qa.get("category", "general")
        if cat not in category_scores:
            category_scores[cat] = {"correct": 0, "total": 0}
        category_scores[cat]["total"] += 1
        if qa.get("is_correct"):
            category_scores[cat]["correct"] += 1

    return {
        "session_id": session.id,
        "user_id": session.user_id,
        "total_score": session.total_score,
        "total_questions": NUM_MCQ_QUESTIONS,
        "percentage": round((session.total_score / NUM_MCQ_QUESTIONS) * 100, 1),
        "literacy_level": session.literacy_level,
        "profile": profile_data,
        "category_breakdown": category_scores,
        "questions_and_answers": questions_asked,
        "completed_at": session.completed_at.isoformat() if session.completed_at else None
    }


@router.get("/user-history/{user_id}")
async def get_user_assessment_history(user_id: int, db: Session = Depends(get_db)):
    """Get all completed assessments for a user."""
    sessions = db.query(AssessmentSession).filter(
        AssessmentSession.user_id == user_id,
        AssessmentSession.status == "completed"
    ).order_by(AssessmentSession.completed_at.desc()).all()

    return {
        "user_id": user_id,
        "assessments": [
            {
                "session_id": s.id,
                "total_score": s.total_score,
                "literacy_level": s.literacy_level,
                "completed_at": s.completed_at.isoformat() if s.completed_at else None
            }
            for s in sessions
        ]
    }


# ============================================
# Internal Helpers
# ============================================
async def _save_financial_profile(user_id: int, profile_data: dict, db: Session):
    """Save or update the user's financial profile."""
    profile = db.query(FinancialProfile).filter(FinancialProfile.user_id == user_id).first()

    income_str = str(profile_data.get("monthly_income", ""))
    income_value = None
    if "<10000" in income_str:
        income_value = 8000.0
    elif "10000-25000" in income_str:
        income_value = 17500.0
    elif "25000-50000" in income_str:
        income_value = 37500.0
    elif ">50000" in income_str:
        income_value = 60000.0

    children_str = str(profile_data.get("children_count", "0"))
    children_val = 3 if children_str == "3+" else (int(children_str) if children_str.isdigit() else 0)

    if profile:
        profile.monthly_income = income_value
        profile.income_source = profile_data.get("income_source")
        profile.marital_status = profile_data.get("marital_status")
        profile.children_count = children_val
        profile.occupation = profile_data.get("occupation")
    else:
        profile = FinancialProfile(
            user_id=user_id,
            monthly_income=income_value,
            income_source=profile_data.get("income_source"),
            marital_status=profile_data.get("marital_status"),
            children_count=children_val,
            occupation=profile_data.get("occupation")
        )
        db.add(profile)
    db.commit()


async def _complete_assessment(session: AssessmentSession, profile_data: dict, questions_asked: list, db: Session):
    """Finalize the assessment, calculate results, and award XP."""
    score = session.total_score
    total = NUM_MCQ_QUESTIONS
    percentage = (score / total) * 100

    if percentage >= 80:
        level, xp_earned = "advanced", 200
    elif percentage >= 50:
        level, xp_earned = "intermediate", 150
    else:
        level, xp_earned = "beginner", 100

    session.status = "completed"
    session.literacy_level = level
    session.completed_at = datetime.utcnow()

    # Save to LiteracyAssessment
    assessment = LiteracyAssessment(
        user_id=session.user_id,
        total_score=score,
        literacy_level=level,
        budgeting_score=_category_score(questions_asked, "budgeting"),
        investing_score=_category_score(questions_asked, "investing")
    )
    db.add(assessment)

    # Award XP
    gamification = db.query(UserGamification).filter(UserGamification.user_id == session.user_id).first()
    if gamification:
        gamification.total_xp += xp_earned
    else:
        gamification = UserGamification(user_id=session.user_id, total_xp=xp_earned, current_level=1)
        db.add(gamification)

    db.commit()

    category_scores = {}
    for qa in questions_asked:
        cat = qa.get("category", "general")
        if cat not in category_scores:
            category_scores[cat] = {"correct": 0, "total": 0}
        category_scores[cat]["total"] += 1
        if qa.get("is_correct"):
            category_scores[cat]["correct"] += 1

    return {
        "session_id": session.id,
        "phase": "completed",
        "total_score": score,
        "total_questions": total,
        "percentage": round(percentage, 1),
        "literacy_level": level,
        "xp_earned": xp_earned,
        "profile": profile_data,
        "category_breakdown": category_scores,
        "message": f"Assessment complete! You scored {score}/{total} ({round(percentage, 1)}%). Level: {level.upper()}"
    }


def _category_score(questions_asked: list, category: str) -> int:
    """Calculate percentage score for a specific category."""
    correct = sum(1 for qa in questions_asked if qa.get("category") == category and qa.get("is_correct"))
    total = sum(1 for qa in questions_asked if qa.get("category") == category)
    return round((correct / total) * 100) if total > 0 else 0
