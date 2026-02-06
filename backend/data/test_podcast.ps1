# Test the new two-host podcast system
$ErrorActionPreference = "Continue"
$outFile = "C:\Users\Vardh\Desktop\hackspec\finsakhi-hackathon\backend\data\test_results.txt"

try {
    "=== Languages ===" | Out-File $outFile
    $langs = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/podcasts/languages" -Method GET
    "Total: $($langs.total)" | Out-File $outFile -Append
    $langs.supported_languages | ForEach-Object { "$($_.code) - $($_.name) - Host: $($_.host) - Cohost: $($_.cohost)" } | Out-File $outFile -Append
    
    "`n=== Generating Podcast (lesson 1, en, force_regenerate) ===" | Out-File $outFile -Append
    "This uses Groq LLM + edge-tts neural voices..." | Out-File $outFile -Append
    $body = @{ lesson_id = 1; language = "en"; force_regenerate = $true } | ConvertTo-Json
    $start = Get-Date
    $gen = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/podcasts/generate" -Method POST -Body $body -ContentType "application/json"
    $elapsed = ((Get-Date) - $start).TotalSeconds
    "Status: $($gen.status)" | Out-File $outFile -Append
    "Duration: $($gen.duration_seconds)s" | Out-File $outFile -Append
    "Speakers host: $($gen.speakers.host)" | Out-File $outFile -Append
    "Speakers cohost: $($gen.speakers.cohost)" | Out-File $outFile -Append
    "Generation time: $([math]::Round($elapsed,1))s" | Out-File $outFile -Append
    "Podcast ID: $($gen.podcast_id)" | Out-File $outFile -Append
    
    if ($gen.status -eq "ready") {
        $pid = $gen.podcast_id
        "`n=== Script (podcast_id=$pid) ===" | Out-File $outFile -Append
        $script = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/podcasts/script/$pid" -Method GET
        "Language: $($script.language_name)" | Out-File $outFile -Append
        "Script speakers: Host=$($script.speakers.host), Cohost=$($script.speakers.cohost)" | Out-File $outFile -Append
        $scriptText = $script.script
        $priyaCount = ([regex]::Matches($scriptText, "PRIYA:")).Count
        $arjunCount = ([regex]::Matches($scriptText, "ARJUN:")).Count
        "Speaker turns: Priya=$priyaCount, Arjun=$arjunCount" | Out-File $outFile -Append
        "`nScript preview (first 600 chars):" | Out-File $outFile -Append
        $scriptText.Substring(0, [Math]::Min(600, $scriptText.Length)) | Out-File $outFile -Append
        
        $audioPath = "C:\Users\Vardh\Desktop\hackspec\finsakhi-hackathon\backend\data\podcasts\lesson_1_en.mp3"
        if (Test-Path $audioPath) {
            $sizeKB = [math]::Round((Get-Item $audioPath).Length / 1024, 1)
            "`nAudio file size: $($sizeKB) KB" | Out-File $outFile -Append
        }
        "`nSUCCESS - Two-host neural podcast generated!" | Out-File $outFile -Append
    } else {
        "`nFAILED: $($gen.error)" | Out-File $outFile -Append
    }
} catch {
    "ERROR: $($_.Exception.Message)" | Out-File $outFile -Append
}
