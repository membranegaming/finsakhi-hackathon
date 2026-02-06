"""
FinSakhi Podcast Service — Realistic Two-Host Multilingual Audio Learning
==========================================================================
Generates realistic two-host podcast episodes for each lesson:

  1. Groq LLM → writes a natural dialogue between Host (Priya ♀) and Co-host (Arjun ♂)
  2. Microsoft Edge Neural TTS → high-quality, natural-sounding Indian voices
     - Dedicated female voice for Priya (Host)
     - Dedicated male voice for Arjun (Co-host)
  3. Audio stitching → merges alternating speaker segments into one podcast

10 Indian languages with native neural voice pairs.
"""

import os
import asyncio
import shutil
import tempfile
import traceback
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple, List

from sqlalchemy.orm import Session
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

# ============================================
# Config
# ============================================
BASE_DIR = Path(__file__).resolve().parent.parent.parent
PODCAST_DIR = BASE_DIR / "data" / "podcasts"
PODCAST_DIR.mkdir(parents=True, exist_ok=True)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# ============================================
# Microsoft Edge Neural TTS — Indian Voice Pairs
# Female host (Priya) + Male co-host (Arjun) per language
# ============================================
LANGUAGE_MAP = {
    "en": {
        "name": "English",
        "host_voice": "en-IN-NeerjaExpressiveNeural",
        "cohost_voice": "en-IN-PrabhatNeural",
        "host_name": "Priya",
        "cohost_name": "Arjun",
    },
    "hi": {
        "name": "Hindi",
        "host_voice": "hi-IN-SwaraNeural",
        "cohost_voice": "hi-IN-MadhurNeural",
        "host_name": "प्रिया",
        "cohost_name": "अर्जुन",
    },
    "ta": {
        "name": "Tamil",
        "host_voice": "ta-IN-PallaviNeural",
        "cohost_voice": "ta-IN-ValluvarNeural",
        "host_name": "பிரியா",
        "cohost_name": "அர்ஜுன்",
    },
    "te": {
        "name": "Telugu",
        "host_voice": "te-IN-ShrutiNeural",
        "cohost_voice": "te-IN-MohanNeural",
        "host_name": "ప్రియా",
        "cohost_name": "అర్జున్",
    },
    "bn": {
        "name": "Bengali",
        "host_voice": "bn-IN-TanishaaNeural",
        "cohost_voice": "bn-IN-BashkarNeural",
        "host_name": "প্রিয়া",
        "cohost_name": "অর্জুন",
    },
    "mr": {
        "name": "Marathi",
        "host_voice": "mr-IN-AarohiNeural",
        "cohost_voice": "mr-IN-ManoharNeural",
        "host_name": "प्रिया",
        "cohost_name": "अर्जुन",
    },
    "gu": {
        "name": "Gujarati",
        "host_voice": "gu-IN-DhwaniNeural",
        "cohost_voice": "gu-IN-NiranjanNeural",
        "host_name": "પ્રિયા",
        "cohost_name": "અર્જુન",
    },
    "kn": {
        "name": "Kannada",
        "host_voice": "kn-IN-SapnaNeural",
        "cohost_voice": "kn-IN-GaganNeural",
        "host_name": "ಪ್ರಿಯಾ",
        "cohost_name": "ಅರ್ಜುನ್",
    },
    "ml": {
        "name": "Malayalam",
        "host_voice": "ml-IN-SobhanaNeural",
        "cohost_voice": "ml-IN-MidhunNeural",
        "host_name": "പ്രിയ",
        "cohost_name": "അർജുൻ",
    },
    "pa": {
        "name": "Punjabi",
        "host_voice": "hi-IN-SwaraNeural",      # Fallback: Hindi voices
        "cohost_voice": "hi-IN-MadhurNeural",    # (edge-tts lacks Punjabi)
        "host_name": "ਪ੍ਰਿਯਾ",
        "cohost_name": "ਅਰਜੁਨ",
        "tts_note": "Uses Hindi neural voices (Punjabi TTS not yet available)",
    },
}

SUPPORTED_LANGUAGES = list(LANGUAGE_MAP.keys())


def get_supported_languages() -> list:
    """Return list of supported language info with voice/host details."""
    return [
        {
            "code": code,
            "name": info["name"],
            "host": info["host_name"],
            "cohost": info["cohost_name"],
            "voice_type": "neural",
            "note": info.get("tts_note", ""),
        }
        for code, info in LANGUAGE_MAP.items()
    ]


# ============================================
# 1) LLM SCRIPT GENERATION — Two-Person Dialogue
# ============================================

def _generate_podcast_script(
    title: str,
    story: str,
    takeaway: str,
    language: str = "en",
    pillar: str = "",
    level: str = "",
) -> Optional[str]:
    """
    Use Groq LLM to generate a realistic two-host podcast dialogue.
    Returns a script with PRIYA: and ARJUN: markers for each speaker turn.
    """
    if not groq_client:
        # Fallback: minimal dialogue
        return (
            f"PRIYA: Namaste everyone! Welcome to FinSakhi Radio. "
            f"Today, let me tell you about {title}.\n"
            f"ARJUN: Sounds interesting, Priya didi! Tell us more.\n"
            f"PRIYA: {story}\n"
            f"ARJUN: Wow, that really makes sense!\n"
            f"PRIYA: Remember this — {takeaway}\n"
            f"ARJUN: Thank you didi! That was very helpful.\n"
            f"PRIYA: Until next time, keep learning and keep growing!"
        )

    lang_name = LANGUAGE_MAP.get(language, {}).get("name", "English")

    # Language-specific instructions
    if language == "en":
        lang_instruction = (
            "Write the dialogue in simple, everyday Indian English. "
            "Sprinkle in natural Hindi words like 'achha', 'bilkul', 'dekho', 'suno na' "
            "the way real Indians casually speak English."
        )
    elif language == "hi":
        lang_instruction = (
            "Write the ENTIRE dialogue in Hindi (Devanagari script). "
            "Use simple, everyday Hindustani — the kind spoken in small towns and villages. "
            "Keep it warm and desi."
        )
    else:
        lang_instruction = (
            f"Write the ENTIRE dialogue in {lang_name} using its native script. "
            f"Use simple, everyday {lang_name} that ordinary people speak at home. "
            f"Translate ALL content into authentic {lang_name}. "
            f"Do NOT leave English sentences — everything must be in {lang_name}."
        )

    prompt = f"""You are writing a script for "FinSakhi Radio" — India's favourite financial literacy podcast.

TWO HOSTS:
- PRIYA: A warm, knowledgeable didi (elder sister) figure. She explains financial concepts through stories. Speaks gently but with confidence. She's like a trusted friend who happens to know a lot about money.
- ARJUN: A curious, relatable bhai (brother) figure. He represents the everyday listener. He asks questions, sometimes gets confused, makes common mistakes, and has genuine "aha!" moments. He's learning alongside the audience.

LESSON CONTENT TO COVER:
- Title: {title}
- Topic: {pillar} ({level} level)
- Story/Content: {story}
- Key Takeaway: {takeaway}

WRITE A NATURAL PODCAST DIALOGUE.

STRICT FORMAT (CRITICAL — follow exactly):
- Every line MUST begin with exactly "PRIYA:" or "ARJUN:"
- No other speaker labels — ONLY "PRIYA:" and "ARJUN:"
- Do NOT use [brackets], (parentheses), *asterisks*, or stage directions
- Do NOT write actions like "[laughs]" or "(pauses)" — express emotions through words only

CONVERSATION FLOW:
1. PRIYA opens warmly — greets listeners, introduces today's topic with excitement
2. ARJUN responds enthusiastically, relates to the topic from personal experience
3. PRIYA tells the main story, breaking it into digestible parts
4. After each part, ARJUN reacts naturally — asks genuine questions, shares doubts
5. Include a moment where ARJUN makes a common financial mistake or assumption and PRIYA gently corrects him with patience
6. ARJUN has a clear "aha moment" where the concept clicks for him
7. PRIYA delivers the key takeaway clearly
8. ARJUN repeats it in his own simpler words to confirm understanding
9. Both sign off warmly — PRIYA encouraging, ARJUN thanking

STYLE:
- 300-400 words total (about 3 minutes when spoken)
- Grade 5 reading level — very simple language
- Natural reactions throughout: "Achha?", "Sach mein?", "Hmm, samajh aaya!", "Waah!", "Arey!"
- Feels like two friends chatting over chai, NOT a classroom lecture
- Keep ₹ amounts exactly as-is
- Make it engaging, warm, and genuinely helpful
- {lang_instruction}

Return ONLY the dialogue lines starting with PRIYA: or ARJUN: — nothing else. No title, no notes."""

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.75,
            max_tokens=1200,
        )
        script = response.choices[0].message.content.strip()

        # Validate: must contain both speakers
        if "PRIYA:" not in script and "ARJUN:" not in script:
            script = f"PRIYA: {script}"
        elif "PRIYA:" not in script:
            script = f"PRIYA: Welcome to FinSakhi Radio!\n{script}"
        elif "ARJUN:" not in script:
            lines = script.split("\n")
            enriched = []
            for i, line in enumerate(lines):
                enriched.append(line)
                if i == 1:
                    enriched.append("ARJUN: That's really interesting, Priya didi!")
                elif i == len(lines) - 2:
                    enriched.append("ARJUN: Wow, I learned so much today!")
            script = "\n".join(enriched)

        return script

    except Exception as e:
        print(f"⚠️ Groq podcast script generation failed: {e}")
        return (
            f"PRIYA: Namaste! Welcome to FinSakhi Radio. Today's topic: {title}.\n"
            f"ARJUN: Oh, this is something I really need to know about!\n"
            f"PRIYA: {story}\n"
            f"ARJUN: That makes a lot of sense, didi!\n"
            f"PRIYA: And here's the most important thing to remember — {takeaway}\n"
            f"ARJUN: Thank you, Priya didi! I won't forget this.\n"
            f"PRIYA: That's all for today. Keep learning, keep growing. Bye!"
        )


# ============================================
# 2) DIALOGUE PARSING
# ============================================

def _parse_dialogue_script(script: str) -> List[Tuple[str, str]]:
    """
    Parse a PRIYA:/ARJUN: formatted dialogue into speaker segments.
    Returns list of (role, text) where role is 'HOST' or 'COHOST'.
    """
    segments: List[Tuple[str, str]] = []
    current_speaker: Optional[str] = None
    current_lines: List[str] = []

    for raw_line in script.split("\n"):
        line = raw_line.strip()
        if not line:
            continue

        upper = line.upper()

        if upper.startswith("PRIYA:"):
            if current_speaker and current_lines:
                segments.append((current_speaker, " ".join(current_lines)))
            current_speaker = "HOST"
            text = line[6:].strip()
            current_lines = [text] if text else []

        elif upper.startswith("ARJUN:"):
            if current_speaker and current_lines:
                segments.append((current_speaker, " ".join(current_lines)))
            current_speaker = "COHOST"
            text = line[6:].strip()
            current_lines = [text] if text else []

        elif current_speaker:
            current_lines.append(line)

    # Flush last segment
    if current_speaker and current_lines:
        segments.append((current_speaker, " ".join(current_lines)))

    return segments


# ============================================
# 3) EDGE-TTS AUDIO GENERATION — Multi-Voice
# ============================================

async def _generate_segment_audio(text: str, voice: str, output_path: Path):
    """Generate audio for one speaker segment using edge-tts neural voice."""
    import edge_tts  # type: ignore[import-not-found]
    communicate = edge_tts.Communicate(text, voice, rate="-8%", volume="+0%")
    await communicate.save(str(output_path))


async def _generate_dialogue_audio(
    segments: List[Tuple[str, str]],
    language: str,
    output_path: Path,
) -> Tuple[bool, Optional[float], Optional[str]]:
    """
    Generate multi-voice podcast audio from dialogue segments.
    Uses edge-tts with different neural voices for Host and Co-host.
    Stitches segments by concatenating MP3 bytes (MP3 is frame-based).
    """
    from mutagen.mp3 import MP3  # type: ignore[import-untyped]

    lang_config = LANGUAGE_MAP.get(language, LANGUAGE_MAP["en"])
    host_voice = lang_config["host_voice"]
    cohost_voice = lang_config["cohost_voice"]

    temp_dir = Path(tempfile.mkdtemp(prefix="finsakhi_pod_"))
    temp_files: List[Path] = []

    try:
        for i, (speaker, text) in enumerate(segments):
            if not text.strip():
                continue
            voice = host_voice if speaker == "HOST" else cohost_voice
            temp_path = temp_dir / f"seg_{i:03d}.mp3"

            await _generate_segment_audio(text, voice, temp_path)

            if temp_path.exists() and temp_path.stat().st_size > 0:
                temp_files.append(temp_path)

        if not temp_files:
            return False, None, "No audio segments were generated"

        # Stitch all MP3 segments into one file
        with open(output_path, "wb") as outfile:
            for temp_path in temp_files:
                outfile.write(temp_path.read_bytes())

        # Measure total duration
        audio_info = MP3(str(output_path))
        duration = round(audio_info.info.length, 1)

        return True, duration, None

    except Exception as e:
        error_msg = f"Edge-TTS generation failed: {str(e)}\n{traceback.format_exc()}"
        print(f"⚠️ {error_msg}")
        return False, None, error_msg

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def _run_async(coro):
    """Safely run an async coroutine from a synchronous (threaded) context."""
    try:
        asyncio.get_running_loop()
        # Inside an existing loop — spin up a fresh one in a new thread
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(asyncio.run, coro).result()
    except RuntimeError:
        # No running loop — safe to use asyncio.run() directly
        return asyncio.run(coro)


def _text_to_audio(
    script: str, language: str, output_path: Path,
) -> Tuple[bool, Optional[float], Optional[str]]:
    """Convert a PRIYA:/ARJUN: dialogue script to multi-voice MP3 audio."""
    try:
        segments = _parse_dialogue_script(script)

        if not segments:
            segments = [("HOST", script)]

        success, duration, error = _run_async(
            _generate_dialogue_audio(segments, language, output_path)
        )
        return success, duration, error

    except Exception as e:
        error_msg = f"Podcast audio failed: {str(e)}\n{traceback.format_exc()}"
        print(f"⚠️ {error_msg}")
        return False, None, error_msg


# ============================================
# 4) MAIN ORCHESTRATION
# ============================================

def generate_podcast_for_lesson(
    db: Session,
    lesson_id: int,
    language: str = "en",
    force_regenerate: bool = False,
) -> dict:
    """
    Generate a two-host podcast for a specific lesson in a specific language.
    Returns dict with status, audio_url, duration, speakers info, etc.
    """
    from app.models.database import Lesson, Module, LessonPodcast

    if language not in SUPPORTED_LANGUAGES:
        return {"error": f"Language '{language}' not supported. Supported: {SUPPORTED_LANGUAGES}"}

    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        return {"error": "Lesson not found"}

    lang_config = LANGUAGE_MAP[language]

    # Check for cached podcast
    existing = db.query(LessonPodcast).filter(
        LessonPodcast.lesson_id == lesson_id,
        LessonPodcast.language == language,
    ).first()

    if existing and existing.status == "ready" and not force_regenerate:
        return {
            "status": "ready",
            "podcast_id": existing.id,
            "lesson_id": lesson_id,
            "language": language,
            "language_name": lang_config["name"],
            "audio_url": f"/api/podcasts/audio/{existing.id}",
            "duration_seconds": existing.duration_seconds,
            "podcast_script": existing.podcast_script,
            "speakers": {
                "host": lang_config["host_name"],
                "cohost": lang_config["cohost_name"],
            },
            "created_at": str(existing.created_at),
        }

    # Create or reset podcast record
    if not existing:
        podcast = LessonPodcast(
            lesson_id=lesson_id,
            language=language,
            status="generating",
        )
        db.add(podcast)
        db.commit()
        db.refresh(podcast)
    else:
        podcast = existing
        podcast.status = "generating"
        podcast.error_message = None
        db.commit()

    try:
        module = db.query(Module).filter(Module.id == lesson.module_id).first()
        pillar = module.pillar if module else ""
        level = module.level if module else ""

        # Pick source content
        if language == "hi":
            title = lesson.title_hi
            story = lesson.story_hi
            takeaway = lesson.takeaway_hi or ""
        else:
            title = lesson.title_en
            story = lesson.story_en
            takeaway = lesson.takeaway_en or ""

        # Step 1 — LLM dialogue script
        script = _generate_podcast_script(
            title=title, story=story, takeaway=takeaway,
            language=language, pillar=pillar, level=level,
        )
        if not script:
            podcast.status = "failed"
            podcast.error_message = "Script generation returned empty"
            db.commit()
            return {"error": "Script generation failed", "status": "failed"}

        podcast.podcast_script = script

        # Step 2 — Multi-voice audio
        audio_filename = f"lesson_{lesson_id}_{language}.mp3"
        audio_path = PODCAST_DIR / audio_filename

        success, duration, error = _text_to_audio(script, language, audio_path)

        if success:
            podcast.audio_file_path = f"podcasts/{audio_filename}"
            podcast.duration_seconds = duration
            podcast.status = "ready"
            podcast.updated_at = datetime.utcnow()
            db.commit()

            return {
                "status": "ready",
                "podcast_id": podcast.id,
                "lesson_id": lesson_id,
                "language": language,
                "language_name": lang_config["name"],
                "audio_url": f"/api/podcasts/audio/{podcast.id}",
                "duration_seconds": duration,
                "podcast_script": script,
                "speakers": {
                    "host": lang_config["host_name"],
                    "cohost": lang_config["cohost_name"],
                },
                "created_at": str(podcast.created_at),
            }
        else:
            podcast.status = "failed"
            podcast.error_message = error
            db.commit()
            return {"error": error, "status": "failed"}

    except Exception as e:
        error_msg = f"Podcast generation error: {str(e)}\n{traceback.format_exc()}"
        podcast.status = "failed"
        podcast.error_message = error_msg
        db.commit()
        return {"error": str(e), "status": "failed"}


# ============================================
# 5) UTILITY / QUERY HELPERS
# ============================================

def get_lesson_podcasts(db: Session, lesson_id: int) -> list:
    """Get all available podcasts for a lesson across all languages."""
    from app.models.database import LessonPodcast

    podcasts = db.query(LessonPodcast).filter(
        LessonPodcast.lesson_id == lesson_id,
        LessonPodcast.status == "ready",
    ).all()

    return [
        {
            "podcast_id": p.id,
            "language": p.language,
            "language_name": LANGUAGE_MAP.get(p.language, {}).get("name", p.language),
            "audio_url": f"/api/podcasts/audio/{p.id}",
            "duration_seconds": p.duration_seconds,
            "speakers": {
                "host": LANGUAGE_MAP.get(p.language, {}).get("host_name", "Priya"),
                "cohost": LANGUAGE_MAP.get(p.language, {}).get("cohost_name", "Arjun"),
            },
            "created_at": str(p.created_at),
        }
        for p in podcasts
    ]


def generate_all_podcasts_for_lesson(
    db: Session, lesson_id: int, languages: list = None,
) -> list:
    """Generate podcasts for a lesson in multiple languages."""
    if languages is None:
        languages = ["en", "hi"]

    results = []
    for lang in languages:
        result = generate_podcast_for_lesson(db, lesson_id, lang)
        results.append(result)
    return results
