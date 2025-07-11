# PowerShell script to test authentication flow
$baseUrl = "http://localhost:5000"

# Create a web session to maintain cookies
$session = New-Object Microsoft.PowerShell.Commands.WebRequestSession
$session.UserAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Common headers
$headers = @{
    "Accept" = "application/json"
    "Content-Type" = "application/json"
    "Origin" = "http://localhost:3000"
    "Referer" = "http://localhost:3000/"
    "sec-ch-ua" = "`"Not_A Brand`";v=`"8`", `"Chromium`";v=`"120`", `"Google Chrome`";v=`"120`""
    "sec-ch-ua-mobile" = "?0"
    "sec-ch-ua-platform" = "`"Windows`""
}

Write-Host "=== PowerShell Authentication Test ===" -ForegroundColor Green

# Step 1: Login
Write-Host "`n1. Attempting login..." -ForegroundColor Yellow
$loginBody = @{
    username = "testuser"
    password = "testpass"
} | ConvertTo-Json

try {
    $loginResponse = Invoke-WebRequest -UseBasicParsing -Uri "$baseUrl/api/auth/login" `
        -Method POST `
        -Body $loginBody `
        -Headers $headers `
        -WebSession $session

    Write-Host "Login Status: $($loginResponse.StatusCode)" -ForegroundColor Green
    $loginData = $loginResponse.Content | ConvertFrom-Json
    Write-Host "Login Success: $($loginData.success)" -ForegroundColor Green
    
    # Display cookies
    Write-Host "Cookies received:" -ForegroundColor Cyan
    foreach ($cookie in $session.Cookies.GetCookies($baseUrl)) {
        Write-Host "  $($cookie.Name) = $($cookie.Value)" -ForegroundColor Gray
    }
    
} catch {
    Write-Host "Login failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Step 2: Check authentication status
Write-Host "`n2. Checking authentication status..." -ForegroundColor Yellow
try {
    $statusResponse = Invoke-WebRequest -UseBasicParsing -Uri "$baseUrl/api/auth/status" `
        -Headers $headers `
        -WebSession $session

    Write-Host "Status Check: $($statusResponse.StatusCode)" -ForegroundColor Green
    $statusData = $statusResponse.Content | ConvertFrom-Json
    Write-Host "Authenticated: $($statusData.data.authenticated)" -ForegroundColor Green
    
} catch {
    Write-Host "Status check failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Step 3: Get sessions (the failing request)
Write-Host "`n3. Getting sessions..." -ForegroundColor Yellow
try {
    $sessionsResponse = Invoke-WebRequest -UseBasicParsing -Uri "$baseUrl/api/dialogue/sessions" `
        -Headers $headers `
        -WebSession $session

    Write-Host "Sessions Request: $($sessionsResponse.StatusCode)" -ForegroundColor Green
    $sessionsData = $sessionsResponse.Content | ConvertFrom-Json
    Write-Host "Sessions Success: $($sessionsData.success)" -ForegroundColor Green
    Write-Host "Number of sessions: $($sessionsData.sessions.Count)" -ForegroundColor Green
    
} catch {
    Write-Host "Sessions request failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Response: $($_.Exception.Response)" -ForegroundColor Red
}

# Step 4: Test with x-internal-api-request header (your original request)
Write-Host "`n4. Testing with x-internal-api-request header..." -ForegroundColor Yellow
$internalHeaders = $headers.Clone()
$internalHeaders["x-internal-api-request"] = "1"

try {
    $internalResponse = Invoke-WebRequest -UseBasicParsing -Uri "$baseUrl/api/dialogue/sessions?_t=1752128498476" `
        -Headers $internalHeaders `
        -WebSession $session

    Write-Host "Internal API Request: $($internalResponse.StatusCode)" -ForegroundColor Green
    $internalData = $internalResponse.Content | ConvertFrom-Json
    Write-Host "Internal API Success: $($internalData.success)" -ForegroundColor Green
    
} catch {
    Write-Host "Internal API request failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n=== Test Complete ===" -ForegroundColor Green