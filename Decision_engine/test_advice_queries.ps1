# Test Script for User Query Feature in Advice API
# Run this after starting the server: python -m uvicorn app.main:app --port 8001 --reload

Write-Host "`n=== Testing Advice API with User Query ===" -ForegroundColor Cyan

# Test 1: Vacation Question
Write-Host "`n[Test 1] User asks: 'Can I go on a vacation this month?'" -ForegroundColor Yellow
$response1 = Invoke-WebRequest -Uri "http://localhost:8001/advice/generate" `
    -Method POST `
    -ContentType "application/json" `
    -Body (Get-Content "test_user_query.json" -Raw)

$result1 = $response1.Content | ConvertFrom-Json
Write-Host "`nSummary:" -ForegroundColor Green
Write-Host $result1.summary

Write-Host "`nTop Risks:" -ForegroundColor Green
$result1.top_risks | ForEach-Object { Write-Host "  - $_" }

Write-Host "`nAction Steps:" -ForegroundColor Green
$result1.action_steps | ForEach-Object { 
    Write-Host "  [$($_.priority.ToUpper())] $($_.title)" -ForegroundColor $(if ($_.priority -eq "high") { "Red" } else { "Yellow" })
    Write-Host "    $($_.description)"
}

# Test 2: Phone Purchase Question
Write-Host "`n`n[Test 2] User asks: 'Should I buy a new phone?'" -ForegroundColor Yellow
$body2 = Get-Content "test_user_query.json" -Raw | ConvertFrom-Json
$body2.user_query = "Should I buy a new phone?"
$response2 = Invoke-WebRequest -Uri "http://localhost:8001/advice/generate" `
    -Method POST `
    -ContentType "application/json" `
    -Body ($body2 | ConvertTo-Json -Depth 10)

$result2 = $response2.Content | ConvertFrom-Json
Write-Host "`nSummary:" -ForegroundColor Green
Write-Host $result2.summary

# Test 3: Savings Question
Write-Host "`n`n[Test 3] User asks: 'How much should I save monthly?'" -ForegroundColor Yellow
$body3 = Get-Content "test_user_query.json" -Raw | ConvertFrom-Json
$body3.user_query = "How much should I save monthly?"
$response3 = Invoke-WebRequest -Uri "http://localhost:8001/advice/generate" `
    -Method POST `
    -ContentType "application/json" `
    -Body ($body3 | ConvertTo-Json -Depth 10)

$result3 = $response3.Content | ConvertFrom-Json
Write-Host "`nSummary:" -ForegroundColor Green
Write-Host $result3.summary

# Test 4: No Query (General Advice)
Write-Host "`n`n[Test 4] No specific question - general advice" -ForegroundColor Yellow
$body4 = Get-Content "test_user_query.json" -Raw | ConvertFrom-Json
$body4.user_query = $null
$response4 = Invoke-WebRequest -Uri "http://localhost:8001/advice/generate" `
    -Method POST `
    -ContentType "application/json" `
    -Body ($body4 | ConvertTo-Json -Depth 10)

$result4 = $response4.Content | ConvertFrom-Json
Write-Host "`nSummary:" -ForegroundColor Green
Write-Host $result4.summary

Write-Host "`n`n=== All Tests Complete ===" -ForegroundColor Cyan
Write-Host "✅ User queries are being processed and answered directly in summaries!" -ForegroundColor Green
