"""Quick test: generate a two-host podcast for lesson 1 in English using the new edge-tts system."""
import requests, json, time

BASE = "http://127.0.0.1:8000/api/podcasts"

# 1) Check languages
print("=== Languages ===")
r = requests.get(f"{BASE}/languages")
langs = r.json()
print(json.dumps(langs["supported_languages"][0], indent=2, ensure_ascii=False))
print(f"Total: {langs['total']}")

# 2) Generate English podcast for lesson 1 (force regenerate to use new engine)
print("\n=== Generating Podcast (lesson 1, English) ===")
print("This will take ~30-60 seconds for LLM script + edge-tts audio...")
start = time.time()
r = requests.post(f"{BASE}/generate", json={
    "lesson_id": 1,
    "language": "en",
    "force_regenerate": True,
})
elapsed = round(time.time() - start, 1)
data = r.json()
print(f"Status: {data.get('status')}")
print(f"Duration: {data.get('duration_seconds')}s")
print(f"Speakers: {json.dumps(data.get('speakers'), ensure_ascii=False)}")
print(f"Generation time: {elapsed}s")

if data.get("status") == "ready":
    pid = data["podcast_id"]
    # 3) Check script
    print(f"\n=== Script (podcast_id={pid}) ===")
    r2 = requests.get(f"{BASE}/script/{pid}")
    script_data = r2.json()
    script = script_data.get("script", "")
    print(f"Speakers in response: {json.dumps(script_data.get('speakers'), ensure_ascii=False)}")
    # Show first 500 chars of script
    print(f"Script preview:\n{script[:500]}...")
    
    # Count speaker turns
    priya_turns = script.count("PRIYA:")
    arjun_turns = script.count("ARJUN:")
    print(f"\nSpeaker turns: Priya={priya_turns}, Arjun={arjun_turns}")
    
    # 4) Verify audio file
    import os
    audio_path = r"C:\Users\Vardh\Desktop\hackspec\finsakhi-hackathon\backend\data\podcasts\lesson_1_en.mp3"
    if os.path.exists(audio_path):
        size_kb = round(os.path.getsize(audio_path) / 1024, 1)
        print(f"\nAudio file: {size_kb} KB")
    
    print("\n✅ SUCCESS — Two-host neural podcast generated!")
else:
    print(f"\n❌ FAILED: {data.get('error', 'Unknown error')}")
