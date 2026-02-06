"""Quick test for the Podcast API"""
import requests
import json

BASE = "http://127.0.0.1:8000"

print("=" * 60)
print("🎙️  FinSakhi Podcast API Test")
print("=" * 60)

# 1. Test /languages
print("\n1️⃣  GET /api/podcasts/languages")
r = requests.get(f"{BASE}/api/podcasts/languages")
print(f"   Status: {r.status_code}")
data = r.json()
print(f"   Languages: {data['total']} supported")
for lang in data["supported_languages"]:
    print(f"     - {lang['code']}: {lang['name']}")

# 2. Test /overview
print("\n2️⃣  GET /api/podcasts/overview")
r = requests.get(f"{BASE}/api/podcasts/overview")
print(f"   Status: {r.status_code}")
print(f"   Overview: {json.dumps(r.json(), indent=2)}")

# 3. Generate podcast for lesson 1 in English
print("\n3️⃣  POST /api/podcasts/generate (lesson 1, English)")
r = requests.post(f"{BASE}/api/podcasts/generate", json={
    "lesson_id": 1,
    "language": "en"
})
print(f"   Status: {r.status_code}")
data = r.json()
print(f"   Result: status={data.get('status')}, duration={data.get('duration_seconds')}s")
if data.get("audio_url"):
    print(f"   Audio URL: {data['audio_url']}")
if data.get("podcast_script"):
    print(f"   Script preview: {data['podcast_script'][:200]}...")

# 4. Generate podcast for lesson 1 in Hindi
print("\n4️⃣  POST /api/podcasts/generate (lesson 1, Hindi)")
r = requests.post(f"{BASE}/api/podcasts/generate", json={
    "lesson_id": 1,
    "language": "hi"
})
print(f"   Status: {r.status_code}")
data = r.json()
print(f"   Result: status={data.get('status')}, duration={data.get('duration_seconds')}s")
if data.get("audio_url"):
    print(f"   Audio URL: {data['audio_url']}")

# 5. Get lesson podcasts
print("\n5️⃣  GET /api/podcasts/lesson/1")
r = requests.get(f"{BASE}/api/podcasts/lesson/1")
print(f"   Status: {r.status_code}")
data = r.json()
print(f"   Available: {data['total_languages']} language(s)")
for p in data["available_podcasts"]:
    print(f"     - {p['language_name']}: {p['audio_url']} ({p['duration_seconds']}s)")

# 6. Test lesson content endpoint includes podcasts
print("\n6️⃣  GET /api/learning/lesson/1 (check podcast integration)")
r = requests.get(f"{BASE}/api/learning/lesson/1?user_id=1&language=en")
print(f"   Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    print(f"   Podcasts in lesson response: {len(data.get('podcasts', []))} available")
    print(f"   Podcast hint: {data.get('podcast_hint', 'N/A')}")

print("\n" + "=" * 60)
print("✅ Podcast API test complete!")
print("=" * 60)
