"""Quick smoke test for the Investment API"""
import requests, json

BASE = "http://localhost:8000"

def test(label, url):
    print(f"\n{'='*50}")
    print(f"  {label}")
    print(f"{'='*50}")
    try:
        r = requests.get(url, timeout=30)
        data = r.json()
        print(json.dumps(data, indent=2, default=str)[:1500])
        print(f"\n  ✅ Status: {r.status_code}")
    except Exception as e:
        print(f"  ❌ FAILED: {e}")

# Test 1: All commodities
test("Commodities (Gold, Silver, Oil)", f"{BASE}/api/investments/commodities")

# Test 2: Single commodity
test("Gold Price", f"{BASE}/api/investments/commodities/gold")

# Test 3: Gold history
test("Gold 1-Month History (first 3 points)", f"{BASE}/api/investments/commodities/gold/history?period=1mo")

# Test 4: Popular mutual funds  
test("Popular Mutual Funds", f"{BASE}/api/investments/mutual-funds/popular")

# Test 5: Search mutual funds
test("Search MF: 'SBI'", f"{BASE}/api/investments/mutual-funds/search?q=SBI")

# Test 6: Specific MF NAV
test("SBI Bluechip Fund NAV (120503)", f"{BASE}/api/investments/mutual-funds/120503")

# Test 7: MF history
test("SBI Bluechip 30-day NAV History", f"{BASE}/api/investments/mutual-funds/120503/history?days=30")

# Test 8: Chart embed config
test("Chart Embed Config", f"{BASE}/api/investments/charts/embed-config")

# Test 9: Full dashboard
test("Investment Dashboard", f"{BASE}/api/investments/dashboard")

print(f"\n{'='*50}")
print("  ALL TESTS DONE!")
print(f"{'='*50}")
print(f"\n  📘 Swagger UI: {BASE}/docs")
