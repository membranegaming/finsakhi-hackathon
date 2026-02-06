"""Full integration test for FinSakhi Podcast API — run while server is up on :8000"""
import urllib.request, urllib.error, json, sys

BASE = "http://127.0.0.1:8000"
passed = 0
failed = 0

def test(name, method, path, body=None):
    global passed, failed
    url = BASE + path
    try:
        if body:
            data = json.dumps(body).encode()
            req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method=method)
        else:
            req = urllib.request.Request(url, method=method)
        with urllib.request.urlopen(req, timeout=60) as resp:
            code = resp.status
            result = json.loads(resp.read().decode())
            print(f"  ✅ {name} — {code}")
            passed += 1
            return result
    except urllib.error.HTTPError as e:
        body_text = e.read().decode() if e.fp else ""
        print(f"  ❌ {name} — HTTP {e.code}: {body_text[:200]}")
        failed += 1
        return None
    except Exception as e:
        print(f"  ❌ {name} — {e}")
        failed += 1
        return None

print("=" * 60)
print("🎙️  FinSakhi Podcast API — Integration Test")
print("=" * 60)

# --- Basic health ---
print("\n📡 Server Health:")
test("Root", "GET", "/")
test("Health", "GET", "/health")

# --- Podcast endpoints (read-only) ---
print("\n🎧 Podcast Read Endpoints:")
r = test("List languages", "GET", "/api/podcasts/languages")
if r:
    assert r["total"] == 10, f"Expected 10 languages, got {r['total']}"
    print(f"     → {r['total']} languages supported")

r = test("Overview (empty)", "GET", "/api/podcasts/overview")
if r:
    print(f"     → {r['total_lessons']} lessons, {r['total_podcasts_ready']} podcasts ready")

r = test("Lesson 1 podcasts", "GET", "/api/podcasts/lesson/1")
if r:
    print(f"     → {r['total_languages']} podcast(s) available for lesson 1")

# --- Generate podcast (English) ---
print("\n🔊 Podcast Generation (English):")
r = test("Generate EN for lesson 1", "POST", "/api/podcasts/generate", {"lesson_id": 1, "language": "en"})
if r:
    print(f"     → status={r.get('status')}, duration={r.get('duration_seconds')}s")
    if r.get("podcast_script"):
        print(f"     → script preview: {r['podcast_script'][:120]}...")
    en_podcast_id = r.get("podcast_id")

    # Test audio streaming
    if en_podcast_id:
        try:
            req = urllib.request.Request(f"{BASE}/api/podcasts/audio/{en_podcast_id}")
            with urllib.request.urlopen(req, timeout=10) as resp:
                content_type = resp.headers.get("Content-Type", "")
                size = len(resp.read())
                if "audio" in content_type or size > 1000:
                    print(f"  ✅ Audio stream — {content_type}, {size} bytes")
                    passed += 1
                else:
                    print(f"  ❌ Audio stream — unexpected: {content_type}, {size} bytes")
                    failed += 1
        except Exception as e:
            print(f"  ❌ Audio stream — {e}")
            failed += 1

    # Test script endpoint
    if en_podcast_id:
        test("Get script", "GET", f"/api/podcasts/script/{en_podcast_id}")

# --- Generate podcast (Hindi) ---
print("\n🔊 Podcast Generation (Hindi):")
r = test("Generate HI for lesson 1", "POST", "/api/podcasts/generate", {"lesson_id": 1, "language": "hi"})
if r:
    print(f"     → status={r.get('status')}, duration={r.get('duration_seconds')}s")

# --- Re-check lesson podcasts ---
print("\n🔁 Re-check after generation:")
r = test("Lesson 1 podcasts (after)", "GET", "/api/podcasts/lesson/1")
if r:
    print(f"     → {r['total_languages']} podcast(s) now available")
    for p in r.get("available_podcasts", []):
        print(f"       🎧 {p['language_name']}: {p['duration_seconds']}s")

# --- Check learning endpoint integration ---
print("\n📚 Learning endpoint integration:")
r = test("Lesson content w/ podcasts", "GET", "/api/learning/lesson/1?user_id=1&language=en")
if r:
    podcasts = r.get("podcasts", [])
    hint = r.get("podcast_hint", "")
    print(f"     → {len(podcasts)} podcast(s) in lesson response")
    print(f"     → hint: {hint}")

# --- Overview after generation ---
print("\n📊 Final Overview:")
r = test("Overview (after gen)", "GET", "/api/podcasts/overview")
if r:
    print(f"     → {r['total_podcasts_ready']} podcasts ready, {r['total_duration_minutes']} min total")
    print(f"     → by language: {r['by_language']}")

# --- Summary ---
print("\n" + "=" * 60)
total = passed + failed
print(f"Results: {passed}/{total} passed, {failed} failed")
if failed == 0:
    print("🎉 ALL TESTS PASSED!")
else:
    print(f"⚠️  {failed} test(s) failed")
print("=" * 60)
sys.exit(0 if failed == 0 else 1)
