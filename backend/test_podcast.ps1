# FinSakhi Podcast API — PowerShell Integration Test
$base = "http://127.0.0.1:8000"
$pass = 0; $fail = 0

function Test-Endpoint($name, $method, $path, $body=$null) {
    try {
        $params = @{ Uri = "$base$path"; Method = $method; UseBasicParsing = $true; TimeoutSec = 90 }
        if ($body) {
            $params["Body"] = ($body | ConvertTo-Json)
            $params["ContentType"] = "application/json"
        }
        $r = Invoke-WebRequest @params
        $data = $r.Content | ConvertFrom-Json
        Write-Host "  OK $name — $($r.StatusCode)" -ForegroundColor Green
        $script:pass++
        return $data
    } catch {
        Write-Host "  FAIL $name — $($_.Exception.Message)" -ForegroundColor Red
        $script:fail++
        return $null
    }
}

Write-Host "`n============================================"
Write-Host "   FinSakhi Podcast API Test"
Write-Host "============================================"

Write-Host "`n--- Server Health ---"
Test-Endpoint "Root" "GET" "/"
Test-Endpoint "Health" "GET" "/health"

Write-Host "`n--- Podcast Read Endpoints ---"
$langs = Test-Endpoint "Languages" "GET" "/api/podcasts/languages"
if ($langs) { Write-Host "     $($langs.total) languages supported" }

$overview = Test-Endpoint "Overview" "GET" "/api/podcasts/overview"
if ($overview) { Write-Host "     $($overview.total_lessons) lessons, $($overview.total_podcasts_ready) podcasts" }

$lp = Test-Endpoint "Lesson 1 podcasts" "GET" "/api/podcasts/lesson/1"
if ($lp) { Write-Host "     $($lp.total_languages) podcast(s) available" }

Write-Host "`n--- Generate English Podcast ---"
$gen = Test-Endpoint "Generate EN" "POST" "/api/podcasts/generate" @{lesson_id=1; language="en"}
if ($gen) {
    Write-Host "     status=$($gen.status), duration=$($gen.duration_seconds)s"
    if ($gen.podcast_script) {
        $preview = $gen.podcast_script.Substring(0, [Math]::Min(120, $gen.podcast_script.Length))
        Write-Host "     script: $preview..."
    }
}

Write-Host "`n--- Generate Hindi Podcast ---"
$genh = Test-Endpoint "Generate HI" "POST" "/api/podcasts/generate" @{lesson_id=1; language="hi"}
if ($genh) {
    Write-Host "     status=$($genh.status), duration=$($genh.duration_seconds)s"
}

Write-Host "`n--- Verify Audio Streaming ---"
if ($gen -and $gen.podcast_id) {
    try {
        $audioResp = Invoke-WebRequest -Uri "$base/api/podcasts/audio/$($gen.podcast_id)" -Method GET -UseBasicParsing -TimeoutSec 10
        $ct = $audioResp.Headers["Content-Type"]
        $sz = $audioResp.Content.Length
        Write-Host "  OK Audio stream — $ct, $sz bytes" -ForegroundColor Green
        $script:pass++
    } catch {
        Write-Host "  FAIL Audio stream — $($_.Exception.Message)" -ForegroundColor Red
        $script:fail++
    }
}

Write-Host "`n--- Script Endpoint ---"
if ($gen -and $gen.podcast_id) {
    Test-Endpoint "Get script" "GET" "/api/podcasts/script/$($gen.podcast_id)"
}

Write-Host "`n--- Lesson 1 after generation ---"
$lp2 = Test-Endpoint "Lesson podcasts" "GET" "/api/podcasts/lesson/1"
if ($lp2) {
    Write-Host "     $($lp2.total_languages) podcast(s) now available:"
    foreach ($p in $lp2.available_podcasts) {
        Write-Host "       $($p.language_name): $($p.duration_seconds)s"
    }
}

Write-Host "`n--- Learning API Integration ---"
$lesson = Test-Endpoint "Lesson content" "GET" "/api/learning/lesson/1?user_id=1&language=en"
if ($lesson) {
    $pc = if ($lesson.podcasts) { $lesson.podcasts.Count } else { 0 }
    Write-Host "     podcasts in response: $pc"
    Write-Host "     hint: $($lesson.podcast_hint)"
}

Write-Host "`n--- Final Overview ---"
$ov = Test-Endpoint "Overview" "GET" "/api/podcasts/overview"
if ($ov) {
    Write-Host "     $($ov.total_podcasts_ready) ready, $($ov.total_duration_minutes) min total"
    Write-Host "     by_language: $($ov.by_language | ConvertTo-Json -Compress)"
}

Write-Host "`n============================================"
$total = $pass + $fail
Write-Host "Results: $pass/$total passed, $fail failed"
if ($fail -eq 0) { Write-Host "ALL TESTS PASSED!" -ForegroundColor Green }
else { Write-Host "$fail test(s) failed" -ForegroundColor Yellow }
Write-Host "============================================"
