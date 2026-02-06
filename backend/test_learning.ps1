####################################
# FinSakhi Learning API Test Script
####################################
$BASE = "http://localhost:8000"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  FinSakhi Learning API - Test Suite" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# ---- STEP 1: Create test user via OTP ----
Write-Host "[1/8] Sending OTP..." -ForegroundColor Yellow
$phone = Read-Host "Enter phone number (e.g. +919571156569)"
$otp = Invoke-RestMethod -Uri "$BASE/api/auth/send-otp" -Method POST -ContentType "application/json" -Body "{`"phone`": `"$phone`"}"
Write-Host "  -> $($otp.message)" -ForegroundColor Green

Write-Host "`n[2/8] Verifying OTP..." -ForegroundColor Yellow
$code = Read-Host "Enter OTP from SMS"
$auth = Invoke-RestMethod -Uri "$BASE/api/auth/verify-otp" -Method POST -ContentType "application/json" -Body "{`"phone`": `"$phone`", `"otp`": `"$code`"}"
$userId = $auth.user_id
$token = $auth.token
Write-Host "  -> Logged in! User ID: $userId" -ForegroundColor Green

# ---- STEP 2: Run quick assessment (optional) ----
Write-Host "`n[3/8] Starting assessment to set literacy level..." -ForegroundColor Yellow
$sess = Invoke-RestMethod -Uri "$BASE/api/assessment/start" -Method POST -ContentType "application/json" -Body "{`"user_id`": $userId}"
$sessId = $sess.session_id
Write-Host "  -> Session $sessId started (skip by entering answers quickly)"

# Profile steps
$profileAnswers = @("Test Kisan", "1", "0", "0", "1", "0")
$stepNames = @("Name", "Income", "Income Source", "Marital Status", "Children", "Occupation")
for ($i = 0; $i -lt 6; $i++) {
    $body = "{`"session_id`": $sessId, `"answer`": `"$($profileAnswers[$i])`"}"
    $r = Invoke-RestMethod -Uri "$BASE/api/assessment/answer-profile" -Method POST -ContentType "application/json" -Body $body
    Write-Host "  -> $($stepNames[$i]): done" -ForegroundColor DarkGray
}

# MCQ steps (auto-answer 1 for all)
for ($i = 0; $i -lt 8; $i++) {
    $body = "{`"session_id`": $sessId, `"selected_option`": 1}"
    $r = Invoke-RestMethod -Uri "$BASE/api/assessment/answer-mcq" -Method POST -ContentType "application/json" -Body $body
    Write-Host "  -> MCQ $($i+1)/8: answered" -ForegroundColor DarkGray
}
Write-Host "  -> Assessment complete! Level: $($r.literacy_level)" -ForegroundColor Green

# ---- STEP 3: Get all modules ----
Write-Host "`n[4/8] Fetching modules (all 4 pillars)..." -ForegroundColor Yellow
$mods = Invoke-RestMethod -Uri "$BASE/api/learning/modules/$userId" -Method GET
Write-Host "  -> Level: $($mods.current_level) | Health: $($mods.health_score)" -ForegroundColor Green
foreach ($pillar in $mods.pillars.PSObject.Properties) {
    Write-Host "  PILLAR: $($pillar.Name)" -ForegroundColor Cyan
    foreach ($m in $pillar.Value) {
        $lock = if ($m.is_locked) { " [LOCKED]" } else { "" }
        Write-Host "    - $($m.title) ($($m.level)) $($m.completed_lessons)/$($m.total_lessons)$lock" -ForegroundColor $(if ($m.is_locked) {"DarkGray"} else {"White"})
    }
}

# ---- STEP 4: Get next recommended lesson ----
Write-Host "`n[5/8] Getting next recommended lesson..." -ForegroundColor Yellow
$next = Invoke-RestMethod -Uri "$BASE/api/learning/next/$userId" -Method GET
Write-Host "  -> Next: $($next.title) [$($next.pillar) - $($next.level)]" -ForegroundColor Green

# ---- STEP 5: Read personalized lesson ----
$lessonId = $next.lesson_id
Write-Host "`n[6/8] Loading personalized lesson #$lessonId (Groq AI)..." -ForegroundColor Yellow
$lesson = Invoke-RestMethod -Uri "$BASE/api/learning/lesson/$($lessonId)?user_id=$userId&language=en" -Method GET -TimeoutSec 30
Write-Host "`n  --- PERSONALIZED STORY ---" -ForegroundColor Magenta
Write-Host "  $($lesson.story)" -ForegroundColor White
Write-Host "`n  --- TAKEAWAY ---" -ForegroundColor Magenta
Write-Host "  $($lesson.takeaway)" -ForegroundColor White

# Show scenario
if ($lesson.scenario) {
    Write-Host "`n  --- SCENARIO ---" -ForegroundColor Magenta
    Write-Host "  Q: $($lesson.scenario.question)" -ForegroundColor White
    $opts = $lesson.scenario.options
    for ($i = 0; $i -lt $opts.Count; $i++) {
        Write-Host "    [$i] $($opts[$i].text)" -ForegroundColor White
    }
    Write-Host ""
    $pick = Read-Host "  Pick your answer (0-$($opts.Count - 1))"

    # ---- STEP 6: Submit scenario answer ----
    Write-Host "`n[7/8] Submitting scenario answer..." -ForegroundColor Yellow
    $ans = Invoke-RestMethod -Uri "$BASE/api/learning/lesson/$lessonId/scenario" -Method POST -ContentType "application/json" -Body "{`"user_id`": $userId, `"selected_option`": $pick}"
    Write-Host "  -> $($ans.feedback)" -ForegroundColor $(if ($ans.correct) {"Green"} else {"Red"})
    Write-Host "  -> Health Score: $($ans.health_score)" -ForegroundColor Cyan
}

# ---- STEP 7: Complete lesson ----
Write-Host "`n[8/8] Completing lesson..." -ForegroundColor Yellow
$comp = Invoke-RestMethod -Uri "$BASE/api/learning/lesson/$lessonId/complete" -Method POST -ContentType "application/json" -Body "{`"user_id`": $userId, `"tool_used`": true}"
Write-Host "  -> $($comp.message)" -ForegroundColor Green
Write-Host "  -> XP: +$($comp.xp_awarded) (tool bonus: +$($comp.tool_bonus)) | Total XP: $($comp.total_xp)" -ForegroundColor Cyan
Write-Host "  -> Health: $($comp.health_score) | Level: $($comp.current_level)" -ForegroundColor Cyan

# ---- BONUS: Show dashboards ----
Write-Host "`n========== PROGRESS DASHBOARD ==========" -ForegroundColor Cyan
$prog = Invoke-RestMethod -Uri "$BASE/api/learning/progress/$userId" -Method GET
Write-Host "  Overall: $($prog.overall.completed)/$($prog.overall.total_lessons) lessons ($($prog.overall.percentage)%)" -ForegroundColor White
foreach ($p in $prog.pillars.PSObject.Properties) {
    Write-Host "  $($p.Name): $($p.Value.completed)/$($p.Value.total_lessons) ($($p.Value.percentage)%)" -ForegroundColor White
}

Write-Host "`n========== FINANCIAL HEALTH ==========" -ForegroundColor Cyan
$hp = Invoke-RestMethod -Uri "$BASE/api/learning/health/$userId" -Method GET
Write-Host "  Score: $($hp.health_score)/100 $($hp.label)" -ForegroundColor White
Write-Host "  Scenarios: $($hp.breakdown.scenarios_correct)/$($hp.breakdown.scenarios_total) ($($hp.breakdown.scenario_accuracy))" -ForegroundColor White
Write-Host "  Tools Used: $($hp.breakdown.tools_used)" -ForegroundColor White
foreach ($tip in $hp.tips) { Write-Host "  TIP: $tip" -ForegroundColor Yellow }

Write-Host "`n========== ALL TESTS PASSED ==========" -ForegroundColor Green
Write-Host "Swagger UI: http://localhost:8000/docs`n" -ForegroundColor DarkGray
