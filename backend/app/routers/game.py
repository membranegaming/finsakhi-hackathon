"""
FinGame Router — RPG-style financial literacy game endpoints.
All endpoints require user_id (from FinSakhi auth).
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.services.game_service import GameService, StoryResponse, RollbackResponse, PathInfo
from pydantic import BaseModel
from typing import List

router = APIRouter(prefix="/api/game", tags=["FinGame RPG"])


class SetPathRequest(BaseModel):
    user_id: int
    path_id: str
    language: str = "english"


class ChoiceRequest(BaseModel):
    user_id: int
    choice_id: str
    language: str = "english"


class RollbackRequest(BaseModel):
    user_id: int


@router.get("/paths", response_model=List[PathInfo])
def get_paths(language: str = Query("english")):
    """Get all available story paths"""
    return GameService.get_paths(language)


@router.post("/set-path", response_model=StoryResponse)
def set_path(req: SetPathRequest, db: Session = Depends(get_db)):
    """Start or restart a story path"""
    return GameService.set_path(db, req.user_id, req.path_id, req.language)


@router.get("/current", response_model=StoryResponse)
def get_current(user_id: int = Query(...), language: str = Query("english"), db: Session = Depends(get_db)):
    """Get current game state and story node"""
    return GameService.get_current_state(db, user_id, language)


@router.post("/choose", response_model=StoryResponse)
def make_choice(req: ChoiceRequest, db: Session = Depends(get_db)):
    """Submit a choice in the current story node"""
    return GameService.make_choice(db, req.user_id, req.choice_id, req.language)


@router.post("/rollback", response_model=RollbackResponse)
def rollback(req: RollbackRequest, db: Session = Depends(get_db)):
    """Undo the last choice"""
    return GameService.rollback(db, req.user_id)
