"""Direct test of the podcast service — no server needed."""
import sys, os
sys.path.insert(0, r"C:\Users\Vardh\Desktop\hackspec\finsakhi-hackathon\backend")
os.chdir(r"C:\Users\Vardh\Desktop\hackspec\finsakhi-hackathon\backend")

from app.models.database import SessionLocal, init_db
from app.services.podcast_service import (
    generate_podcast_for_lesson,
    get_supported_languages,
    LANGUAGE_MAP,
    _generate_podcast_script,
    _parse_dialogue_script,
)
import json

init_db()
db = SessionLocal()

# 1) Languages
print("=== Supported Languages ===")
langs = get_supported_languages()
for l in langs[:3]:
    print(f"  {l['code']}: {l['name']} | Host: {l['host']} | Cohost: {l['cohost']} | Voices: {l['voice_type']}")
print(f"  ... and {len(langs)-3} more ({len(langs)} total)")

# 2) Generate a podcast for lesson 1, English (force regenerate)
print("\n=== Generating Podcast (lesson 1, en) ===")
print("  Step 1: LLM dialogue script via Groq...")
print("  Step 2: edge-tts neural audio (two voices)...")
print("  This may take 30-60 seconds...\n")

import time
start = time.time()
result = generate_podcast_for_lesson(db, lesson_id=1, language="en", force_regenerate=True)
elapsed = round(time.time() - start, 1)

print(f"  Status: {result.get('status')}")
print(f"  Duration: {result.get('duration_seconds')}s")
print(f"  Speakers: {json.dumps(result.get('speakers'), ensure_ascii=False)}")
print(f"  Generation time: {elapsed}s")

if result.get("status") == "ready":
    script = result.get("podcast_script", "")
    priya_turns = script.count("PRIYA:")
    arjun_turns = script.count("ARJUN:")
    print(f"  Speaker turns: Priya={priya_turns}, Arjun={arjun_turns}")
    print(f"\n=== Script Preview ===")
    print(script[:600])
    
    audio_path = r"C:\Users\Vardh\Desktop\hackspec\finsakhi-hackathon\backend\data\podcasts\lesson_1_en.mp3"
    if os.path.exists(audio_path):
        size_kb = round(os.path.getsize(audio_path) / 1024, 1)
        print(f"\n  Audio file: {size_kb} KB")
    
    print("\n✅ SUCCESS — Two-host neural podcast generated!")
else:
    print(f"\n❌ FAILED: {result.get('error')}")

db.close()
