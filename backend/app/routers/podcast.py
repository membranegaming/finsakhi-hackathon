"""
FinSakhi Podcast API — Audio Learning for Every Lesson
Generates and serves multilingual podcast episodes for financial literacy lessons.
Each lesson is automatically turned into a warm, storytelling-style podcast.
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.models.database import get_db, Lesson, Module, LessonPodcast
from app.services.podcast_service import (
    generate_podcast_for_lesson,
    get_lesson_podcasts,
    generate_all_podcasts_for_lesson,
    get_supported_languages,
    PODCAST_DIR,
    SUPPORTED_LANGUAGES,
)
from typing import Optional, List
from pathlib import Path

router = APIRouter(prefix="/api/podcasts", tags=["Podcasts"])


# ============================================
# Pydantic Schemas
# ============================================

class PodcastGenerateRequest(BaseModel):
    lesson_id: int
    language: str = "en"
    force_regenerate: bool = False


class BulkPodcastRequest(BaseModel):
    lesson_id: int
    languages: List[str] = ["en", "hi"]


# ============================================
# ENDPOINTS
# ============================================

@router.get("/languages")
def list_supported_languages():
    """Get all languages supported for podcast generation."""
    return {
        "supported_languages": get_supported_languages(),
        "total": len(SUPPORTED_LANGUAGES),
    }


@router.post("/generate")
def generate_podcast(req: PodcastGenerateRequest, db: Session = Depends(get_db)):
    """
    Generate a two-host podcast for a lesson in a specific language.
    Uses Groq LLM for dialogue script + Microsoft Edge Neural TTS for realistic audio.
    Returns cached podcast if already generated, or generates fresh.
    """
    result = generate_podcast_for_lesson(
        db=db,
        lesson_id=req.lesson_id,
        language=req.language,
        force_regenerate=req.force_regenerate,
    )

    if "error" in result and result.get("status") != "ready":
        raise HTTPException(status_code=500, detail=result["error"])

    return result


@router.post("/generate-bulk")
def generate_bulk_podcasts(req: BulkPodcastRequest, db: Session = Depends(get_db)):
    """
    Generate podcasts for a lesson in multiple languages at once.
    Default: English + Hindi.
    """
    # Validate languages
    invalid = [l for l in req.languages if l not in SUPPORTED_LANGUAGES]
    if invalid:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported languages: {invalid}. Supported: {SUPPORTED_LANGUAGES}",
        )

    results = generate_all_podcasts_for_lesson(db, req.lesson_id, req.languages)

    return {
        "lesson_id": req.lesson_id,
        "languages_requested": req.languages,
        "results": results,
    }


@router.get("/lesson/{lesson_id}")
def get_podcasts_for_lesson(lesson_id: int, db: Session = Depends(get_db)):
    """
    Get all available podcast episodes for a lesson (across all languages).
    """
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    module = db.query(Module).filter(Module.id == lesson.module_id).first()

    podcasts = get_lesson_podcasts(db, lesson_id)

    return {
        "lesson_id": lesson_id,
        "lesson_title_en": lesson.title_en,
        "lesson_title_hi": lesson.title_hi,
        "pillar": module.pillar if module else None,
        "level": module.level if module else None,
        "available_podcasts": podcasts,
        "total_languages": len(podcasts),
        "supported_languages": get_supported_languages(),
    }


@router.get("/audio/{podcast_id}")
def stream_podcast_audio(podcast_id: int, db: Session = Depends(get_db)):
    """
    Stream / download the podcast audio file (MP3).
    """
    podcast = db.query(LessonPodcast).filter(LessonPodcast.id == podcast_id).first()
    if not podcast:
        raise HTTPException(status_code=404, detail="Podcast not found")

    if podcast.status != "ready":
        raise HTTPException(status_code=400, detail=f"Podcast not ready. Status: {podcast.status}")

    # Build full file path
    audio_path = PODCAST_DIR.parent / podcast.audio_file_path
    if not audio_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found on disk")

    return FileResponse(
        path=str(audio_path),
        media_type="audio/mpeg",
        filename=audio_path.name,
        headers={"Accept-Ranges": "bytes"},
    )


@router.get("/script/{podcast_id}")
def get_podcast_script(podcast_id: int, db: Session = Depends(get_db)):
    """
    Get the text script of a podcast (useful for reading along or accessibility).
    """
    podcast = db.query(LessonPodcast).filter(LessonPodcast.id == podcast_id).first()
    if not podcast:
        raise HTTPException(status_code=404, detail="Podcast not found")

    from app.services.podcast_service import LANGUAGE_MAP
    lang_config = LANGUAGE_MAP.get(podcast.language, {})

    return {
        "podcast_id": podcast.id,
        "lesson_id": podcast.lesson_id,
        "language": podcast.language,
        "language_name": lang_config.get("name", podcast.language),
        "script": podcast.podcast_script,
        "duration_seconds": podcast.duration_seconds,
        "status": podcast.status,
        "speakers": {
            "host": lang_config.get("host_name", "Priya"),
            "cohost": lang_config.get("cohost_name", "Arjun"),
        },
    }


@router.post("/generate-all-lessons")
def generate_podcasts_for_all_lessons(
    languages: List[str] = ["en", "hi"],
    db: Session = Depends(get_db),
):
    """
    Generate podcasts for ALL lessons in specified languages.
    Useful for pre-generating all content. Runs synchronously.
    """
    # Validate
    invalid = [l for l in languages if l not in SUPPORTED_LANGUAGES]
    if invalid:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported languages: {invalid}. Supported: {SUPPORTED_LANGUAGES}",
        )

    lessons = db.query(Lesson).all()
    results = []
    success_count = 0
    fail_count = 0

    for lesson in lessons:
        for lang in languages:
            result = generate_podcast_for_lesson(db, lesson.id, lang)
            status = result.get("status", "failed")
            if status == "ready":
                success_count += 1
            else:
                fail_count += 1
            results.append({
                "lesson_id": lesson.id,
                "language": lang,
                "status": status,
                "error": result.get("error"),
            })

    return {
        "total_generated": success_count,
        "total_failed": fail_count,
        "total_lessons": len(lessons),
        "languages": languages,
        "details": results,
    }


@router.get("/overview")
def podcast_overview(db: Session = Depends(get_db)):
    """
    Dashboard: overview of all podcasts generated across all lessons and languages.
    """
    from sqlalchemy import func

    total_lessons = db.query(Lesson).count()
    total_podcasts = db.query(LessonPodcast).filter(LessonPodcast.status == "ready").count()
    total_failed = db.query(LessonPodcast).filter(LessonPodcast.status == "failed").count()

    # Breakdown by language
    lang_stats = (
        db.query(LessonPodcast.language, func.count(LessonPodcast.id))
        .filter(LessonPodcast.status == "ready")
        .group_by(LessonPodcast.language)
        .all()
    )

    # Total duration
    total_duration = (
        db.query(func.sum(LessonPodcast.duration_seconds))
        .filter(LessonPodcast.status == "ready")
        .scalar()
    ) or 0

    return {
        "total_lessons": total_lessons,
        "total_podcasts_ready": total_podcasts,
        "total_failed": total_failed,
        "total_duration_minutes": round(total_duration / 60, 1),
        "by_language": {
            lang: count for lang, count in lang_stats
        },
        "supported_languages": get_supported_languages(),
    }
