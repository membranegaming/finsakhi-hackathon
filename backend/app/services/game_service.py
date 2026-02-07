"""
Game Service — manages game state, choices, rollback for the FinGame RPG.
Uses the main FinSakhi database (finsakhi.db).
"""

import json
from sqlalchemy.orm import Session
from app.models.database import GameSession, GameHistoryLog, UserGamification
from app.services.story_engine import StoryEngine


# ── Pydantic response schemas ──────────────────────────────
from pydantic import BaseModel
from typing import List, Optional, Dict


class ChoiceFeedback(BaseModel):
    isCorrect: bool
    advice: Dict[str, str]
    nextScenario: Dict[str, str]


class Choice(BaseModel):
    id: str
    text: str
    cost: Optional[int] = 0
    feedback: Optional[ChoiceFeedback] = None


class Character(BaseModel):
    id: str
    name: str
    role: str
    avatar: str
    description: Optional[str] = None
    personality: Optional[str] = None


class DialogueLine(BaseModel):
    speaker: str
    position: str
    text: str
    emotion: str


class StoryNode(BaseModel):
    id: str
    text: Optional[str] = None
    scene: Optional[str] = None
    dialogue: Optional[List[DialogueLine]] = None
    choices: List[Choice]
    speaker: Optional[Character] = None
    characters: Optional[List[Character]] = None


class GameState(BaseModel):
    savings: int
    debt: int
    confidence: int


class StoryResponse(BaseModel):
    node: StoryNode
    state: GameState
    warning: Optional[str] = None


class PathInfo(BaseModel):
    path_id: str
    title: str
    description: str
    protagonist: str


class RollbackResponse(BaseModel):
    message: str
    restored_node: str


# ── Service ────────────────────────────────────────────────
class GameService:

    @staticmethod
    def get_paths(language: str = "english") -> List[PathInfo]:
        return [PathInfo(**p) for p in StoryEngine.get_available_paths(language)]

    @staticmethod
    def set_path(db: Session, user_id: int, path_id: str, language: str = "english") -> StoryResponse:
        session = db.query(GameSession).filter(GameSession.user_id == user_id).first()

        path_data = StoryEngine._paths.get(path_id)
        if not path_data:
            path_id = "farming"
            path_data = StoryEngine._paths.get(path_id)

        initial_stats = path_data.get("initial_state", {}) if path_data else {}

        if session:
            session.current_path = path_id
            session.current_node_id = "start"
            session.savings = initial_stats.get("savings", 0)
            session.debt = initial_stats.get("debt", 0)
            session.confidence = initial_stats.get("confidence", 50)
            db.query(GameHistoryLog).filter(GameHistoryLog.session_id == session.id).delete()
        else:
            session = GameSession(
                user_id=user_id,
                current_path=path_id,
                current_node_id="start",
                savings=initial_stats.get("savings", 0),
                debt=initial_stats.get("debt", 0),
                confidence=initial_stats.get("confidence", 50),
            )
            db.add(session)

        db.commit()
        db.refresh(session)
        return GameService.get_current_state(db, user_id, language)

    @staticmethod
    def get_current_state(db: Session, user_id: int, language: str = "english") -> StoryResponse:
        session = db.query(GameSession).filter(GameSession.user_id == user_id).first()

        if not session:
            default_path = "farming"
            path_data = StoryEngine._paths.get(default_path)
            initial_stats = path_data.get("initial_state", {}) if path_data else {}

            session = GameSession(
                user_id=user_id,
                current_path=default_path,
                current_node_id="start",
                savings=initial_stats.get("savings", 0),
                debt=initial_stats.get("debt", 0),
                confidence=initial_stats.get("confidence", 50),
            )
            db.add(session)
            db.commit()
            db.refresh(session)

        current_node = None
        if session.current_node_id == "start":
            current_node = StoryEngine.get_start_node(session.current_path)
            if current_node:
                session.current_node_id = current_node["node_id"]
                db.commit()
        else:
            current_node = StoryEngine.get_node(session.current_path, session.current_node_id)

        if not current_node:
            return StoryResponse(
                node=StoryNode(id="end", text="Story Completed!", choices=[]),
                state=GameState(savings=session.savings, debt=session.debt, confidence=session.confidence),
            )

        return GameService._build_response(current_node, session, language)

    @staticmethod
    def make_choice(db: Session, user_id: int, choice_id: str, language: str = "english") -> StoryResponse:
        session = db.query(GameSession).filter(GameSession.user_id == user_id).first()
        if not session:
            return GameService.get_current_state(db, user_id, language)

        current_node = StoryEngine.get_node(session.current_path, session.current_node_id)
        if not current_node:
            return GameService.get_current_state(db, user_id, language)

        selected = next((c for c in current_node["choices"] if c["id"] == choice_id), None)
        if not selected:
            return GameService.get_current_state(db, user_id, language)

        # Log history for rollback
        prev_stats = json.dumps({
            "savings": session.savings,
            "debt": session.debt,
            "confidence": session.confidence,
            "current_node_id": session.current_node_id,
        })
        db.add(GameHistoryLog(
            session_id=session.id,
            node_id=session.current_node_id,
            choice_id=choice_id,
            previous_stats=prev_stats,
        ))

        # Apply impact
        impact = selected.get("impact", {})
        session.savings += impact.get("savings", 0)
        session.debt += impact.get("debt", 0)
        session.confidence += impact.get("confidence", 0)

        # Advance node
        if "next_node" in selected and selected["next_node"]:
            next_node = StoryEngine.get_node(session.current_path, selected["next_node"])
            session.current_node_id = next_node["node_id"] if next_node else "end"
        elif "next_node" in selected and selected["next_node"] is None:
            session.current_node_id = "end"
        else:
            next_node = StoryEngine.get_next_node(session.current_path, current_node.get("sequence", 0))
            session.current_node_id = next_node["node_id"] if next_node else "end"

        db.commit()
        db.refresh(session)

        # Check if story ended → award XP
        if session.current_node_id == "end":
            GameService._award_xp(db, user_id, 50)

        return GameService.get_current_state(db, user_id, language)

    @staticmethod
    def rollback(db: Session, user_id: int) -> RollbackResponse:
        session = db.query(GameSession).filter(GameSession.user_id == user_id).first()
        if not session:
            return RollbackResponse(message="No session found", restored_node="")

        last_log = (
            db.query(GameHistoryLog)
            .filter(GameHistoryLog.session_id == session.id)
            .order_by(GameHistoryLog.id.desc())
            .first()
        )
        if not last_log:
            return RollbackResponse(message="Cannot rollback further", restored_node=session.current_node_id)

        prev = json.loads(last_log.previous_stats) if last_log.previous_stats else {}
        session.savings = prev.get("savings", session.savings)
        session.debt = prev.get("debt", session.debt)
        session.confidence = prev.get("confidence", session.confidence)
        session.current_node_id = prev.get("current_node_id", session.current_node_id)

        db.delete(last_log)
        db.commit()

        return RollbackResponse(message="Rolled back successfully", restored_node=session.current_node_id)

    # ── helpers ─────────────────────────────────────────────
    @staticmethod
    def _build_response(node: dict, session: GameSession, language: str = "english") -> StoryResponse:
        resolve = StoryEngine.resolve_text
        # Build choices
        choices_list = []
        for c in node.get("choices", []):
            fb = None
            if c.get("feedback"):
                f = c["feedback"]
                fb = ChoiceFeedback(
                    isCorrect=f.get("isCorrect", False),
                    advice=f.get("advice", {"english": "", "hindi": ""}),
                    nextScenario=f.get("nextScenario", {"english": "", "hindi": ""}),
                )
            choices_list.append(Choice(id=c["id"], text=resolve(c["text"], language), feedback=fb))

        # Speaker (legacy)
        speaker_char = None
        if node.get("speaker"):
            cdata = StoryEngine.get_character(node["speaker"])
            if cdata:
                speaker_char = Character(
                    id=node["speaker"], name=resolve(cdata["name"], language), role=resolve(cdata["role"], language),
                    avatar=cdata["avatar"], description=resolve(cdata.get("description"), language),
                    personality=resolve(cdata.get("personality"), language),
                )

        # Dialogue characters
        chars_list = None
        dialogue_data = node.get("dialogue", [])
        if dialogue_data:
            speaker_ids = set(d.get("speaker") for d in dialogue_data if d.get("speaker"))
            chars_list = []
            for cid in speaker_ids:
                cdata = StoryEngine.get_character(cid)
                if cdata:
                    chars_list.append(Character(
                        id=cid, name=resolve(cdata["name"], language), role=resolve(cdata["role"], language),
                        avatar=cdata["avatar"], description=resolve(cdata.get("description"), language),
                        personality=resolve(cdata.get("personality"), language),
                    ))

        # Narrative text with placeholder replacement
        narrative = resolve(node.get("narrative", ""), language)
        if narrative:
            narrative = (
                narrative
                .replace("{savings}", str(session.savings))
                .replace("{debt}", str(session.debt))
                .replace("{confidence}", str(session.confidence))
            )

        # Dialogue lines with placeholder replacement
        dialogue_lines = None
        if dialogue_data:
            dialogue_lines = []
            for d in dialogue_data:
                txt = resolve(d.get("text", ""), language)
                txt = txt.replace("{savings}", str(session.savings))
                txt = txt.replace("{debt}", str(session.debt))
                txt = txt.replace("{confidence}", str(session.confidence))
                dialogue_lines.append(DialogueLine(
                    speaker=d.get("speaker", ""),
                    position=d.get("position", "left"),
                    text=txt,
                    emotion=d.get("emotion", "neutral"),
                ))

        return StoryResponse(
            node=StoryNode(
                id=node["node_id"],
                text=narrative or None,
                scene=node.get("scene"),
                dialogue=dialogue_lines,
                choices=choices_list,
                speaker=speaker_char,
                characters=chars_list,
            ),
            state=GameState(
                savings=session.savings,
                debt=session.debt,
                confidence=session.confidence,
            ),
        )

    @staticmethod
    def _award_xp(db: Session, user_id: int, xp: int):
        """Award XP to user's gamification record on story completion"""
        gam = db.query(UserGamification).filter(UserGamification.user_id == user_id).first()
        if gam:
            gam.total_xp += xp
        else:
            gam = UserGamification(user_id=user_id, total_xp=xp, current_level=1)
            db.add(gam)
        db.commit()
