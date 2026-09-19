# ============================================================
# JeevanPath AI — One-Click Server Startup Script
# Starts FastAPI backend + ngrok tunnel
# Run this on your PC before sharing the Vercel URL
# ============================================================

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "  JeevanPath AI — Starting Backend" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# ── Check ngrok is installed ─────────────────────────────────
if (-not (Get-Command ngrok -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: ngrok not found." -ForegroundColor Red
    Write-Host "Install it from: https://ngrok.com/download" -ForegroundColor Yellow
    Write-Host "Then run: ngrok config add-authtoken YOUR_TOKEN" -ForegroundColor Yellow
    exit 1
}

# ── Start FastAPI backend in background ──────────────────────
Write-Host "Starting FastAPI backend on port 8000..." -ForegroundColor Green
$backend = Start-Process -PassThru -FilePath "python" `
    -ArgumentList "-m uvicorn main:app --host 0.0.0.0 --port 8000" `
    -WorkingDirectory "$PSScriptRoot\backend" `
    -WindowStyle Normal

Write-Host "Backend started (PID: $($backend.Id))" -ForegroundColor Green
Write-Host "Waiting 5 seconds for backend to load Whisper model..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# ── Start ngrok tunnel ───────────────────────────────────────
Write-Host ""
Write-Host "Starting ngrok tunnel..." -ForegroundColor Green
$ngrok = Start-Process -PassThru -FilePath "ngrok" `
    -ArgumentList "http 8000" `
    -WindowStyle Normal

Start-Sleep -Seconds 3

# ── Get the public ngrok URL ─────────────────────────────────
try {
    $ngrokApi = Invoke-RestMethod -Uri "http://localhost:4040/api/tunnels"
    $publicUrl = $ngrokApi.tunnels | Where-Object { $_.proto -eq "https" } | Select-Object -First 1 -ExpandProperty public_url

    Write-Host ""
    Write-Host "=========================================" -ForegroundColor Green
    Write-Host "  BACKEND IS LIVE!" -ForegroundColor Green
    Write-Host "=========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "  ngrok URL: $publicUrl" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  NEXT STEP:" -ForegroundColor Cyan
    Write-Host "  Go to Vercel Dashboard → Your Project → Settings → Environment Variables" -ForegroundColor White
    Write-Host "  Add: VITE_BACKEND_URL = $publicUrl" -ForegroundColor White
    Write-Host "  Then redeploy your Vercel project." -ForegroundColor White
    Write-Host ""
    Write-Host "  OR test locally:" -ForegroundColor Cyan
    Write-Host "  Open: $publicUrl/health" -ForegroundColor White
    Write-Host ""

    # Copy URL to clipboard
    $publicUrl | Set-Clipboard
    Write-Host "  (URL copied to clipboard!)" -ForegroundColor Gray

} catch {
    Write-Host ""
    Write-Host "ngrok is running. Check http://localhost:4040 for your public URL." -ForegroundColor Yellow
    Write-Host "Copy the HTTPS URL and set it as VITE_BACKEND_URL in Vercel." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Press Ctrl+C or close this window to stop the server." -ForegroundColor Red
Write-Host ""

# Keep script running
Wait-Process -Id $backend.Id
