# Test Assessment API Flow
$baseUrl = "http://localhost:8000"

Write-Host "`n=== Step 1: Send OTP ===" -ForegroundColor Cyan
$otpResponse = Invoke-RestMethod -Uri "$baseUrl/api/auth/send-otp" -Method Post -ContentType "application/json" -Body '{"phone": "+919571156569"}'
$otpResponse | ConvertTo-Json
Write-Host "Check your phone for OTP (or check terminal logs for test OTP)" -ForegroundColor Yellow

# For testing, use OTP from terminal or enter manually
$otp = Read-Host "`nEnter the OTP you received"

Write-Host "`n=== Step 2: Verify OTP & Get Token ===" -ForegroundColor Cyan
$authResponse = Invoke-RestMethod -Uri "$baseUrl/api/auth/verify-otp" -Method Post -ContentType "application/json" -Body "{`"phone`": `"+919571156569`", `"otp`": `"$otp`", `"name`": `"Test User`"}"
$authResponse | ConvertTo-Json -Depth 5
$token = $authResponse.token
$userId = $authResponse.user_id
Write-Host "User ID: $userId" -ForegroundColor Green

Write-Host "`n=== Step 3: Start Assessment ===" -ForegroundColor Cyan
$startResponse = Invoke-RestMethod -Uri "$baseUrl/api/assessment/start" -Method Post -ContentType "application/json" -Body "{`"user_id`": $userId, `"language`": `"en`"}"
$startResponse | ConvertTo-Json -Depth 5
$sessionId = $startResponse.session_id

Write-Host "`n=== Step 4: Answer Profile Questions (6 questions) ===" -ForegroundColor Cyan

# Question 1: Name
Write-Host "`nQ1: $($startResponse.question)" -ForegroundColor Yellow
$answer1 = Read-Host "Your answer"
$response1 = Invoke-RestMethod -Uri "$baseUrl/api/assessment/answer-profile" -Method Post -ContentType "application/json" -Body "{`"session_id`": $sessionId, `"answer`": `"$answer1`"}"
Write-Host "Next question: $($response1.question)" -ForegroundColor White

# Question 2: Income
Write-Host "`nOptions: $($response1.options -join ', ')" -ForegroundColor White
$answer2 = Read-Host "Your answer (0-3)"
$response2 = Invoke-RestMethod -Uri "$baseUrl/api/assessment/answer-profile" -Method Post -ContentType "application/json" -Body "{`"session_id`": $sessionId, `"answer`": `"$answer2`"}"
Write-Host "Next question: $($response2.question)" -ForegroundColor White

# Question 3: Income Source
Write-Host "`nOptions: $($response2.options -join ', ')" -ForegroundColor White
$answer3 = Read-Host "Your answer (0-4)"
$response3 = Invoke-RestMethod -Uri "$baseUrl/api/assessment/answer-profile" -Method Post -ContentType "application/json" -Body "{`"session_id`": $sessionId, `"answer`": `"$answer3`"}"
Write-Host "Next question: $($response3.question)" -ForegroundColor White

# Question 4: Marital Status
Write-Host "`nOptions: $($response3.options -join ', ')" -ForegroundColor White
$answer4 = Read-Host "Your answer (0-3)"
$response4 = Invoke-RestMethod -Uri "$baseUrl/api/assessment/answer-profile" -Method Post -ContentType "application/json" -Body "{`"session_id`": $sessionId, `"answer`": `"$answer4`"}"
Write-Host "Next question: $($response4.question)" -ForegroundColor White

# Question 5: Children
Write-Host "`nOptions: $($response4.options -join ', ')" -ForegroundColor White
$answer5 = Read-Host "Your answer (0-3)"
$response5 = Invoke-RestMethod -Uri "$baseUrl/api/assessment/answer-profile" -Method Post -ContentType "application/json" -Body "{`"session_id`": $sessionId, `"answer`": `"$answer5`"}"
Write-Host "Next question: $($response5.question)" -ForegroundColor White

# Question 6: Occupation
$answer6 = Read-Host "Your answer"
$response6 = Invoke-RestMethod -Uri "$baseUrl/api/assessment/answer-profile" -Method Post -ContentType "application/json" -Body "{`"session_id`": $sessionId, `"answer`": `"$answer6`"}"

Write-Host "`n=== Profile Complete! Starting MCQ Phase ===" -ForegroundColor Green
Write-Host "Profile Summary:" -ForegroundColor Cyan
$response6.profile_summary | ConvertTo-Json

Write-Host "`n=== Step 5: Answer MCQ Questions (8 questions) ===" -ForegroundColor Cyan
$currentQuestion = $response6

for ($i = 1; $i -le 8; $i++) {
    Write-Host "`n--- MCQ Question $i/8 ---" -ForegroundColor Yellow
    Write-Host "Category: $($currentQuestion.category)" -ForegroundColor Magenta
    Write-Host "Q: $($currentQuestion.question)" -ForegroundColor White
    Write-Host "Options:" -ForegroundColor White
    for ($j = 0; $j -lt $currentQuestion.options.Count; $j++) {
        Write-Host "  [$j] $($currentQuestion.options[$j])" -ForegroundColor White
    }
    
    $answer = Read-Host "Your answer (0-3)"
    
    $currentQuestion = Invoke-RestMethod -Uri "$baseUrl/api/assessment/answer-mcq" -Method Post -ContentType "application/json" -Body "{`"session_id`": $sessionId, `"selected_option`": $answer}"
    
    if ($currentQuestion.is_correct -ne $null) {
        if ($currentQuestion.is_correct) {
            Write-Host "✅ Correct!" -ForegroundColor Green
        } else {
            Write-Host "❌ Wrong. Correct answer was: $($currentQuestion.correct_answer_index)" -ForegroundColor Red
        }
        Write-Host "Score so far: $($currentQuestion.score_so_far)" -ForegroundColor Cyan
    }
}

Write-Host "`n=== Assessment Complete! ===" -ForegroundColor Green
Write-Host "`nFinal Results:" -ForegroundColor Cyan
$currentQuestion | ConvertTo-Json -Depth 5

Write-Host "`n=== Step 6: Get Full Results ===" -ForegroundColor Cyan
$results = Invoke-RestMethod -Uri "$baseUrl/api/assessment/result/$sessionId" -Method Get
$results | ConvertTo-Json -Depth 5

Write-Host "`n✅ Assessment test complete!" -ForegroundColor Green
Write-Host "Session ID: $sessionId" -ForegroundColor White
Write-Host "Score: $($results.total_score)/$($results.total_questions) ($($results.percentage)%)" -ForegroundColor White
Write-Host "Literacy Level: $($results.literacy_level)" -ForegroundColor White
