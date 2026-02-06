"""
FinSakhi Goal Setting & Tracking API
Allows users to create, track, update, and complete financial goals.
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.models.database import get_db, Goal, User
from typing import Optional, List
from datetime import datetime

router = APIRouter(prefix="/api/goals", tags=["Goals"])


# ── Schemas ──────────────────────────────────────────────

class GoalCreate(BaseModel):
    user_id: int
    title: str
    category: Optional[str] = "savings"  # savings, investment, emergency, education, other
    target_amount: float
    current_amount: Optional[float] = 0.0
    deadline: Optional[str] = None  # ISO date string
    language: Optional[str] = "en"

class GoalUpdate(BaseModel):
    user_id: int
    amount_to_add: Optional[float] = None
    current_amount: Optional[float] = None
    title: Optional[str] = None
    status: Optional[str] = None  # active, completed, cancelled
    language: Optional[str] = "en"


# ── Endpoints ────────────────────────────────────────────

@router.get("/{user_id}")
def get_goals(user_id: int, db: Session = Depends(get_db)):
    """Get all goals for a user."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")

    goals = db.query(Goal).filter(Goal.user_id == user_id).order_by(Goal.created_at.desc()).all()

    active_goals = []
    completed_goals = []

    for g in goals:
        progress_pct = min(100, (g.current_amount / g.target_amount * 100) if g.target_amount > 0 else 0)
        goal_data = {
            "id": g.id,
            "title": g.title,
            "category": g.category,
            "target_amount": g.target_amount,
            "current_amount": g.current_amount,
            "progress_pct": round(progress_pct, 1),
            "deadline": g.deadline.isoformat() if g.deadline else None,
            "status": g.status,
            "created_at": g.created_at.isoformat() if g.created_at else None,
        }
        if g.status == "completed":
            completed_goals.append(goal_data)
        else:
            active_goals.append(goal_data)

    return {
        "user_id": user_id,
        "active_goals": active_goals,
        "completed_goals": completed_goals,
        "total_active": len(active_goals),
        "total_completed": len(completed_goals),
    }


@router.post("/create")
def create_goal(req: GoalCreate, db: Session = Depends(get_db)):
    """Create a new financial goal."""
    user = db.query(User).filter(User.id == req.user_id).first()
    if not user:
        raise HTTPException(404, "User not found")

    if req.target_amount <= 0:
        raise HTTPException(400, "Target amount must be positive")

    deadline = None
    if req.deadline:
        try:
            deadline = datetime.fromisoformat(req.deadline)
        except ValueError:
            raise HTTPException(400, "Invalid deadline format. Use ISO format: YYYY-MM-DD")

    goal = Goal(
        user_id=req.user_id,
        title=req.title,
        category=req.category or "savings",
        target_amount=req.target_amount,
        current_amount=req.current_amount or 0.0,
        deadline=deadline,
        status="active",
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)

    msg_en = f"Goal '{req.title}' created! Target: ₹{req.target_amount:,.0f}"
    msg_hi = f"लक्ष्य '{req.title}' बनाया! लक्ष्य राशि: ₹{req.target_amount:,.0f}"

    return {
        "success": True,
        "message": msg_hi if req.language == "hi" else msg_en,
        "goal": {
            "id": goal.id,
            "title": goal.title,
            "category": goal.category,
            "target_amount": goal.target_amount,
            "current_amount": goal.current_amount,
            "deadline": goal.deadline.isoformat() if goal.deadline else None,
            "status": goal.status,
        },
    }


@router.put("/{goal_id}")
def update_goal(goal_id: int, req: GoalUpdate, db: Session = Depends(get_db)):
    """Update a goal — add money, change title, or mark completed."""
    goal = db.query(Goal).filter(Goal.id == goal_id, Goal.user_id == req.user_id).first()
    if not goal:
        raise HTTPException(404, "Goal not found")

    if req.title:
        goal.title = req.title

    if req.amount_to_add is not None and req.amount_to_add > 0:
        goal.current_amount += req.amount_to_add

    if req.current_amount is not None:
        goal.current_amount = req.current_amount

    if req.status:
        goal.status = req.status

    # Auto-complete if target reached
    if goal.current_amount >= goal.target_amount and goal.status == "active":
        goal.status = "completed"

    goal.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(goal)

    progress_pct = min(100, (goal.current_amount / goal.target_amount * 100) if goal.target_amount > 0 else 0)

    msg_en = f"Goal '{goal.title}' updated! Progress: {progress_pct:.0f}%"
    msg_hi = f"लक्ष्य '{goal.title}' अपडेट! प्रगति: {progress_pct:.0f}%"

    return {
        "success": True,
        "message": msg_hi if req.language == "hi" else msg_en,
        "goal": {
            "id": goal.id,
            "title": goal.title,
            "category": goal.category,
            "target_amount": goal.target_amount,
            "current_amount": goal.current_amount,
            "progress_pct": round(progress_pct, 1),
            "deadline": goal.deadline.isoformat() if goal.deadline else None,
            "status": goal.status,
        },
    }


@router.delete("/{goal_id}")
def delete_goal(goal_id: int, user_id: int, db: Session = Depends(get_db)):
    """Delete a goal."""
    goal = db.query(Goal).filter(Goal.id == goal_id, Goal.user_id == user_id).first()
    if not goal:
        raise HTTPException(404, "Goal not found")

    db.delete(goal)
    db.commit()

    return {"success": True, "message": "Goal deleted"}
