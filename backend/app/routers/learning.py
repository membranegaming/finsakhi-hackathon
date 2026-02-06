"""
FinSakhi Learning API — Personalized Financial Education
4 Pillars × 3 Levels, Groq-powered personalization, health score tracking
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.database import (
    get_db, User, FinancialProfile, AssessmentSession,
    Module, Lesson, LearningProgress, UserFinancialHealth,
    UserGamification
)
from typing import Optional, List
import os, json
from datetime import datetime
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

router = APIRouter(prefix="/api/learning", tags=["Learning"])

# ============================================
# Groq client
# ============================================
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# ============================================
# Pydantic Schemas
# ============================================
class ScenarioAnswerRequest(BaseModel):
    user_id: int
    selected_option: int  # 0-based index

class LessonCompleteRequest(BaseModel):
    user_id: int
    tool_used: bool = False

# ============================================
# HELPERS
# ============================================

def _get_or_create_health(db: Session, user_id: int) -> UserFinancialHealth:
    """Get or initialize financial health record."""
    health = db.query(UserFinancialHealth).filter(UserFinancialHealth.user_id == user_id).first()
    if not health:
        health = UserFinancialHealth(user_id=user_id, health_score=10)
        db.add(health)
        db.commit()
        db.refresh(health)
    return health


def _get_user_context(db: Session, user_id: int) -> dict:
    """Build user context from profile + assessment for LLM personalization."""
    profile = db.query(FinancialProfile).filter(FinancialProfile.user_id == user_id).first()
    user = db.query(User).filter(User.id == user_id).first()
    assessment = db.query(AssessmentSession).filter(
        AssessmentSession.user_id == user_id,
        AssessmentSession.status == "completed"
    ).order_by(AssessmentSession.id.desc()).first()

    ctx = {
        "name": user.name if user else "User",
        "language": user.language if user else "en",
    }
    if profile:
        ctx.update({
            "income": profile.monthly_income,
            "income_source": profile.income_source,
            "occupation": profile.occupation,
            "marital_status": profile.marital_status,
            "children": profile.children_count,
        })
    if assessment:
        ctx["literacy_level"] = assessment.literacy_level
        try:
            ctx["profile_data"] = json.loads(assessment.profile_data) if assessment.profile_data else {}
        except:
            ctx["profile_data"] = {}
    return ctx


def _check_level_unlock(db: Session, user_id: int, health: UserFinancialHealth):
    """
    Check and unlock levels:
    - Intermediate: All beginner lessons done + ≥60% scenarios correct + ≥1 tool used
    - Advanced: All intermediate done + health ≥ 70
    """
    # Count beginner lessons
    beginner_modules = db.query(Module).filter(Module.level == "beginner").all()
    beginner_lesson_ids = []
    for m in beginner_modules:
        for l in m.lessons:
            beginner_lesson_ids.append(l.id)

    if beginner_lesson_ids:
        beginner_completed = db.query(LearningProgress).filter(
            LearningProgress.user_id == user_id,
            LearningProgress.lesson_id.in_(beginner_lesson_ids),
            LearningProgress.completed == True
        ).count()

        beginner_scenario_correct = db.query(LearningProgress).filter(
            LearningProgress.user_id == user_id,
            LearningProgress.lesson_id.in_(beginner_lesson_ids),
            LearningProgress.scenario_correct == True
        ).count()

        beginner_tools = db.query(LearningProgress).filter(
            LearningProgress.user_id == user_id,
            LearningProgress.lesson_id.in_(beginner_lesson_ids),
            LearningProgress.tool_used == True
        ).count()

        total_beginner = len(beginner_lesson_ids)
        all_beginner_done = beginner_completed >= total_beginner
        scenario_rate = beginner_scenario_correct / max(total_beginner, 1)

        if all_beginner_done and scenario_rate >= 0.6 and beginner_tools >= 1:
            if not health.intermediate_unlocked:
                health.intermediate_unlocked = True
                health.current_level = "intermediate"

    # Check advanced unlock
    if health.intermediate_unlocked:
        inter_modules = db.query(Module).filter(Module.level == "intermediate").all()
        inter_lesson_ids = [l.id for m in inter_modules for l in m.lessons]

        if inter_lesson_ids:
            inter_completed = db.query(LearningProgress).filter(
                LearningProgress.user_id == user_id,
                LearningProgress.lesson_id.in_(inter_lesson_ids),
                LearningProgress.completed == True
            ).count()

            all_inter_done = inter_completed >= len(inter_lesson_ids)

            if all_inter_done and health.health_score >= 70:
                if not health.advanced_unlocked:
                    health.advanced_unlocked = True
                    health.current_level = "advanced"

    # Smart lock: if 3+ consecutive wrong scenarios, enter revision mode
    recent_wrong = db.query(LearningProgress).filter(
        LearningProgress.user_id == user_id,
        LearningProgress.scenario_correct == False
    ).order_by(LearningProgress.id.desc()).limit(3).all()

    if len(recent_wrong) == 3 and all(not r.scenario_correct for r in recent_wrong):
        health.revision_mode = True
    else:
        health.revision_mode = False

    db.commit()
    db.refresh(health)


def _personalize_lesson(lesson: Lesson, user_ctx: dict, language: str = "en") -> str:
    """Use Groq to personalize the lesson story for the user."""
    if not groq_client:
        return None

    story = lesson.story_en if language == "en" else lesson.story_hi
    name = user_ctx.get("name", "User")
    income = user_ctx.get("income", "unknown")
    occupation = user_ctx.get("occupation", "not specified")
    income_source = user_ctx.get("income_source", "not specified")
    children = user_ctx.get("children", 0)
    marital_status = user_ctx.get("marital_status", "not specified")
    literacy = user_ctx.get("literacy_level", "beginner")

    lang_instruction = "Respond in Hindi (Devanagari script)" if language == "hi" else "Respond in simple English"

    prompt = f"""You are FinSakhi, a friendly financial literacy teacher for rural India.
Personalize this lesson story for the user. Keep it SHORT (under 150 words), warm, audio-friendly.

USER CONTEXT:
- Name: {name}
- Monthly income: ₹{income}
- Income source: {income_source}
- Occupation: {occupation}
- Marital status: {marital_status}
- Children: {children}
- Literacy level: {literacy}

ORIGINAL STORY:
{story}

RULES:
- Address user by name
- Use relatable examples based on their income and occupation
- Keep language simple (grade 5 level)
- Make it feel like a friend talking, not a textbook
- {lang_instruction}
- Do NOT add any options or questions — just the story and takeaway
- End with the key takeaway

Return ONLY the personalized story text, nothing else."""

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=400
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"⚠️ Groq personalization failed: {e}")
        return None


# ============================================
# ENDPOINTS
# ============================================

@router.get("/modules/{user_id}")
def get_available_modules(user_id: int, language: str = "en", db: Session = Depends(get_db)):
    """Get all modules grouped by pillar with lock/unlock status."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    health = _get_or_create_health(db, user_id)
    _check_level_unlock(db, user_id, health)

    modules = db.query(Module).order_by(Module.order_index).all()

    pillars = {}
    for mod in modules:
        pillar = mod.pillar
        if pillar not in pillars:
            pillars[pillar] = []

        # Count completed lessons in this module for user
        lesson_ids = [l.id for l in mod.lessons]
        completed_count = 0
        if lesson_ids:
            completed_count = db.query(LearningProgress).filter(
                LearningProgress.user_id == user_id,
                LearningProgress.lesson_id.in_(lesson_ids),
                LearningProgress.completed == True
            ).count()

        # Determine lock status
        is_locked = False
        if mod.level == "intermediate" and not health.intermediate_unlocked:
            is_locked = True
        elif mod.level == "advanced" and not health.advanced_unlocked:
            is_locked = True

        pillars[pillar].append({
            "module_id": mod.id,
            "level": mod.level,
            "title": mod.title_hi if language == "hi" else mod.title_en,
            "description": mod.description_hi if language == "hi" else mod.description_en,
            "total_lessons": len(mod.lessons),
            "completed_lessons": completed_count,
            "is_locked": is_locked,
            "lock_reason": f"Complete all {mod.level} lessons to unlock" if is_locked else None
        })

    return {
        "user_id": user_id,
        "current_level": health.current_level,
        "health_score": health.health_score,
        "revision_mode": health.revision_mode,
        "beginner_unlocked": health.beginner_unlocked,
        "intermediate_unlocked": health.intermediate_unlocked,
        "advanced_unlocked": health.advanced_unlocked,
        "pillars": pillars
    }


@router.get("/module/{module_id}/lessons")
def get_module_lessons(module_id: int, user_id: int, language: str = "en", db: Session = Depends(get_db)):
    """Get all lessons for a module with completion status."""
    module = db.query(Module).filter(Module.id == module_id).first()
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")

    health = _get_or_create_health(db, user_id)

    # Check lock
    if module.level == "intermediate" and not health.intermediate_unlocked:
        raise HTTPException(status_code=403, detail="Complete all beginner lessons to unlock intermediate")
    if module.level == "advanced" and not health.advanced_unlocked:
        raise HTTPException(status_code=403, detail="Complete all intermediate lessons to unlock advanced")

    lessons = db.query(Lesson).filter(Lesson.module_id == module_id).order_by(Lesson.order_index).all()

    result = []
    for lesson in lessons:
        progress = db.query(LearningProgress).filter(
            LearningProgress.user_id == user_id,
            LearningProgress.lesson_id == lesson.id
        ).first()

        result.append({
            "lesson_id": lesson.id,
            "title": lesson.title_hi if language == "hi" else lesson.title_en,
            "completed": progress.completed if progress else False,
            "scenario_correct": progress.scenario_correct if progress else None,
            "tool_used": progress.tool_used if progress else False,
            "xp_reward": lesson.xp_reward,
            "has_scenario": lesson.scenario_en is not None,
            "has_tool": lesson.tool_suggestion is not None,
            "tool_name": lesson.tool_suggestion
        })

    return {
        "module_id": module_id,
        "pillar": module.pillar,
        "level": module.level,
        "title": module.title_hi if language == "hi" else module.title_en,
        "lessons": result
    }


@router.get("/lesson/{lesson_id}")
def get_lesson_content(lesson_id: int, user_id: int, language: str = "en", db: Session = Depends(get_db)):
    """
    Get full lesson content — personalized using Groq if user context available.
    Returns story, takeaway, scenario question, and tool suggestion.
    """
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    module = db.query(Module).filter(Module.id == lesson.module_id).first()
    health = _get_or_create_health(db, user_id)

    # Check lock
    if module and module.level == "intermediate" and not health.intermediate_unlocked:
        raise HTTPException(status_code=403, detail="Intermediate locked")
    if module and module.level == "advanced" and not health.advanced_unlocked:
        raise HTTPException(status_code=403, detail="Advanced locked")

    # Check revision mode
    revision_warning = None
    if health.revision_mode:
        revision_warning = "⚠️ You've had a few wrong answers. Take your time, re-read carefully!" if language == "en" \
            else "⚠️ कुछ गलत जवाब हुए हैं। समय लें, ध्यान से पढ़ें!"

    # Get user context for personalization
    user_ctx = _get_user_context(db, user_id)

    # Check if we already personalized this for the user
    progress = db.query(LearningProgress).filter(
        LearningProgress.user_id == user_id,
        LearningProgress.lesson_id == lesson_id
    ).first()

    personalized_story = None
    if progress and progress.personalized_content:
        personalized_story = progress.personalized_content
    else:
        # Generate personalized content
        personalized_story = _personalize_lesson(lesson, user_ctx, language)
        # Save it
        if not progress:
            progress = LearningProgress(user_id=user_id, lesson_id=lesson_id)
            db.add(progress)
        if personalized_story:
            progress.personalized_content = personalized_story
        db.commit()

    # Parse scenario
    scenario = None
    scenario_raw = lesson.scenario_hi if language == "hi" else lesson.scenario_en
    if scenario_raw:
        try:
            scenario = json.loads(scenario_raw)
        except:
            scenario = None

    return {
        "lesson_id": lesson.id,
        "module_id": lesson.module_id,
        "pillar": module.pillar if module else None,
        "level": module.level if module else None,
        "title": lesson.title_hi if language == "hi" else lesson.title_en,
        "story": personalized_story or (lesson.story_hi if language == "hi" else lesson.story_en),
        "original_story": lesson.story_hi if language == "hi" else lesson.story_en,
        "takeaway": lesson.takeaway_hi if language == "hi" else lesson.takeaway_en,
        "scenario": scenario,
        "tool_suggestion": lesson.tool_suggestion,
        "xp_reward": lesson.xp_reward,
        "revision_warning": revision_warning,
        "already_completed": progress.completed if progress else False
    }


@router.post("/lesson/{lesson_id}/scenario")
def answer_scenario(lesson_id: int, req: ScenarioAnswerRequest, db: Session = Depends(get_db)):
    """
    Submit answer to a lesson's scenario question.
    Updates health score: +10 correct, -5 wrong (unsafe choice).
    """
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    user = db.query(User).filter(User.id == req.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    language = user.language or "en"
    scenario_raw = lesson.scenario_hi if language == "hi" else lesson.scenario_en
    if not scenario_raw:
        raise HTTPException(status_code=400, detail="This lesson has no scenario")

    try:
        scenario = json.loads(scenario_raw)
    except:
        raise HTTPException(status_code=500, detail="Failed to parse scenario")

    options = scenario.get("options", [])
    if req.selected_option < 0 or req.selected_option >= len(options):
        raise HTTPException(status_code=400, detail="Invalid option index")

    is_correct = options[req.selected_option].get("correct", False)

    # Update progress
    progress = db.query(LearningProgress).filter(
        LearningProgress.user_id == req.user_id,
        LearningProgress.lesson_id == lesson_id
    ).first()
    if not progress:
        progress = LearningProgress(user_id=req.user_id, lesson_id=lesson_id)
        db.add(progress)

    progress.scenario_correct = is_correct

    # Update health score
    health = _get_or_create_health(db, req.user_id)
    health.scenarios_total += 1

    if is_correct:
        health.health_score = min(100, health.health_score + 10)
        health.scenarios_correct += 1
    else:
        health.health_score = max(0, health.health_score - 5)
        health.unsafe_choices += 1

    db.commit()

    # Check level unlock after scenario
    _check_level_unlock(db, req.user_id, health)

    # Build feedback
    if is_correct:
        feedback = "✅ Great choice! That's the safe and smart option." if language == "en" \
            else "✅ बढ़िया! यह सुरक्षित और समझदार विकल्प है।"
    else:
        correct_idx = next((i for i, o in enumerate(options) if o.get("correct")), None)
        correct_text = options[correct_idx]["text"] if correct_idx is not None else ""
        feedback_en = f"❌ Not the best choice. The better option was: {correct_text}"
        feedback_hi = f"❌ सही विकल्प नहीं। बेहतर विकल्प था: {correct_text}"
        feedback = feedback_hi if language == "hi" else feedback_en

    return {
        "correct": is_correct,
        "feedback": feedback,
        "health_score": health.health_score,
        "revision_mode": health.revision_mode,
        "selected": options[req.selected_option]["text"],
        "correct_answer": next((o["text"] for o in options if o.get("correct")), None)
    }


@router.post("/lesson/{lesson_id}/complete")
def complete_lesson(lesson_id: int, req: LessonCompleteRequest, db: Session = Depends(get_db)):
    """
    Mark a lesson as completed.
    Awards XP and updates health score: +5 lesson, +10 tool use.
    """
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    user = db.query(User).filter(User.id == req.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    progress = db.query(LearningProgress).filter(
        LearningProgress.user_id == req.user_id,
        LearningProgress.lesson_id == lesson_id
    ).first()
    if not progress:
        progress = LearningProgress(user_id=req.user_id, lesson_id=lesson_id)
        db.add(progress)

    if progress.completed:
        return {"message": "Lesson already completed", "xp_awarded": 0}

    progress.completed = True
    progress.completed_at = datetime.utcnow()
    progress.tool_used = req.tool_used

    # Update health
    health = _get_or_create_health(db, req.user_id)
    health.lessons_completed += 1
    health.health_score = min(100, health.health_score + 5)

    if req.tool_used:
        health.tools_used += 1
        health.health_score = min(100, health.health_score + 10)

    # Award XP
    xp_gained = lesson.xp_reward
    gamification = db.query(UserGamification).filter(UserGamification.user_id == req.user_id).first()
    if gamification:
        gamification.total_xp += xp_gained
        gamification.current_level = 1 + gamification.total_xp // 100
    else:
        gamification = UserGamification(user_id=req.user_id, total_xp=xp_gained, current_level=1)
        db.add(gamification)

    health.updated_at = datetime.utcnow()
    db.commit()

    # Check level unlock
    _check_level_unlock(db, req.user_id, health)

    return {
        "message": "Lesson completed! 🎉",
        "lesson_id": lesson_id,
        "xp_awarded": xp_gained,
        "tool_bonus": 10 if req.tool_used else 0,
        "total_xp": gamification.total_xp,
        "health_score": health.health_score,
        "current_level": health.current_level,
        "intermediate_unlocked": health.intermediate_unlocked,
        "advanced_unlocked": health.advanced_unlocked
    }


@router.get("/progress/{user_id}")
def get_learning_progress(user_id: int, language: str = "en", db: Session = Depends(get_db)):
    """Get complete learning progress dashboard for a user."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    health = _get_or_create_health(db, user_id)
    _check_level_unlock(db, user_id, health)

    # Per-pillar stats
    pillars_progress = {}
    for pillar_name in ["savings", "credit", "investments", "small_business"]:
        modules = db.query(Module).filter(Module.pillar == pillar_name).order_by(Module.order_index).all()
        total = 0
        completed = 0
        for m in modules:
            for l in m.lessons:
                total += 1
                prog = db.query(LearningProgress).filter(
                    LearningProgress.user_id == user_id,
                    LearningProgress.lesson_id == l.id,
                    LearningProgress.completed == True
                ).first()
                if prog:
                    completed += 1

        pillars_progress[pillar_name] = {
            "total_lessons": total,
            "completed": completed,
            "percentage": round((completed / max(total, 1)) * 100)
        }

    # Overall stats
    total_lessons = db.query(Lesson).count()
    total_completed = db.query(LearningProgress).filter(
        LearningProgress.user_id == user_id,
        LearningProgress.completed == True
    ).count()

    gamification = db.query(UserGamification).filter(UserGamification.user_id == user_id).first()

    return {
        "user_id": user_id,
        "health_score": health.health_score,
        "current_level": health.current_level,
        "revision_mode": health.revision_mode,
        "levels": {
            "beginner": health.beginner_unlocked,
            "intermediate": health.intermediate_unlocked,
            "advanced": health.advanced_unlocked
        },
        "overall": {
            "total_lessons": total_lessons,
            "completed": total_completed,
            "percentage": round((total_completed / max(total_lessons, 1)) * 100)
        },
        "pillars": pillars_progress,
        "stats": {
            "lessons_completed": health.lessons_completed,
            "scenarios_correct": health.scenarios_correct,
            "scenarios_total": health.scenarios_total,
            "tools_used": health.tools_used,
            "unsafe_choices": health.unsafe_choices
        },
        "xp": {
            "total_xp": gamification.total_xp if gamification else 0,
            "level": gamification.current_level if gamification else 1
        }
    }


@router.get("/health/{user_id}")
def get_financial_health(user_id: int, db: Session = Depends(get_db)):
    """Get financial health score and breakdown."""
    health = _get_or_create_health(db, user_id)

    # Determine health label
    if health.health_score >= 80:
        label, emoji = "Excellent", "🌟"
    elif health.health_score >= 60:
        label, emoji = "Good", "💪"
    elif health.health_score >= 40:
        label, emoji = "Fair", "📈"
    elif health.health_score >= 20:
        label, emoji = "Needs Work", "⚠️"
    else:
        label, emoji = "Just Starting", "🌱"

    return {
        "user_id": user_id,
        "health_score": health.health_score,
        "label": f"{emoji} {label}",
        "breakdown": {
            "lessons_completed": health.lessons_completed,
            "scenarios_correct": health.scenarios_correct,
            "scenarios_total": health.scenarios_total,
            "scenario_accuracy": f"{round((health.scenarios_correct / max(health.scenarios_total, 1)) * 100)}%",
            "tools_used": health.tools_used,
            "unsafe_choices": health.unsafe_choices
        },
        "current_level": health.current_level,
        "revision_mode": health.revision_mode,
        "tips": _get_health_tips(health)
    }


def _get_health_tips(health: UserFinancialHealth) -> list:
    """Generate tips based on health status."""
    tips = []
    if health.health_score < 30:
        tips.append("Complete more lessons to boost your health score!")
    if health.scenarios_total > 0 and (health.scenarios_correct / health.scenarios_total) < 0.5:
        tips.append("Re-read lesson stories carefully before answering scenarios.")
    if health.tools_used == 0:
        tips.append("Try using the suggested financial tools to earn bonus points!")
    if health.revision_mode:
        tips.append("You're in revision mode — take time to review past lessons.")
    if health.health_score >= 70 and not health.advanced_unlocked:
        tips.append("You're close to unlocking advanced content! Keep going!")
    if not tips:
        tips.append("Great progress! Keep learning and growing! 🚀")
    return tips


@router.get("/next/{user_id}")
def get_next_lesson(user_id: int, language: str = "en", db: Session = Depends(get_db)):
    """Smart recommendation: get the next lesson the user should do."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    health = _get_or_create_health(db, user_id)

    # Find first incomplete lesson at current level
    allowed_levels = ["beginner"]
    if health.intermediate_unlocked:
        allowed_levels.append("intermediate")
    if health.advanced_unlocked:
        allowed_levels.append("advanced")

    modules = db.query(Module).filter(
        Module.level.in_(allowed_levels)
    ).order_by(Module.order_index).all()

    for module in modules:
        lessons = db.query(Lesson).filter(
            Lesson.module_id == module.id
        ).order_by(Lesson.order_index).all()

        for lesson in lessons:
            progress = db.query(LearningProgress).filter(
                LearningProgress.user_id == user_id,
                LearningProgress.lesson_id == lesson.id,
                LearningProgress.completed == True
            ).first()

            if not progress:
                return {
                    "has_next": True,
                    "lesson_id": lesson.id,
                    "module_id": module.id,
                    "pillar": module.pillar,
                    "level": module.level,
                    "title": lesson.title_hi if language == "hi" else lesson.title_en,
                    "module_title": module.title_hi if language == "hi" else module.title_en
                }

    return {
        "has_next": False,
        "message": "🎉 You've completed all available lessons! New content coming soon."
    }
