"""Test Hindi podcast generation with the new two-host edge-tts system."""
import sys, os, json, time
sys.path.insert(0, r"C:\Users\Vardh\Desktop\hackspec\finsakhi-hackathon\backend")
os.chdir(r"C:\Users\Vardh\Desktop\hackspec\finsakhi-hackathon\backend")

from app.models.database import SessionLocal, init_db
from app.services.podcast_service import generate_podcast_for_lesson

init_db()
db = SessionLocal()

print("=== Generating Hindi Podcast (lesson 1) ===")
print("  Using hi-IN-SwaraNeural (Priya) + hi-IN-MadhurNeural (Arjun)...\n")

start = time.time()
result = generate_podcast_for_lesson(db, lesson_id=1, language="hi", force_regenerate=True)
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
    print(f"\n=== Hindi Script Preview ===")
    print(script[:600])
    
    audio_path = r"C:\Users\Vardh\Desktop\hackspec\finsakhi-hackathon\backend\data\podcasts\lesson_1_hi.mp3"
    if os.path.exists(audio_path):
        size_kb = round(os.path.getsize(audio_path) / 1024, 1)
        print(f"\n  Audio file: {size_kb} KB")
    
    print("\n✅ Hindi two-host podcast works!")
else:
    print(f"\n❌ FAILED: {result.get('error')}")

db.close()
