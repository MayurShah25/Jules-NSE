# ==========================================
# JULES: AUTOMATED AWS DEPLOYMENT SCRIPT
# ==========================================
# Run this script locally on your Windows machine every morning!

Write-Host "===========================================" -ForegroundColor Cyan
Write-Host "  Jules Automated AWS Token Sync" -ForegroundColor Cyan
Write-Host "===========================================" -ForegroundColor Cyan

# 1. Generate Token Locally
Write-Host "Step 1: Generating Zerodha Token Locally..." -ForegroundColor Yellow
if (Test-Path "access_token.txt") {
    Remove-Item "access_token.txt"
}
python zerodha_login.py

if (-Not (Test-Path "access_token.txt")) {
    Write-Host "❌ Error: access_token.txt was not generated! Aborting." -ForegroundColor Red
} else {

    # Prompt user for IP (can hardcode later)
    $AWS_IP = Read-Host -Prompt "Enter your AWS Public IP address"

    # 2. Upload Token to AWS
    Write-Host "Step 2: Uploading token securely to AWS Server..." -ForegroundColor Yellow
    scp -i "trading-key.pem" access_token.txt ubuntu@${AWS_IP}:~/trading-bot/

    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Error: Failed to upload token. Check your SSH key and IP." -ForegroundColor Red
    } else {

        # 3. Start Remote Bots
        Write-Host "Step 3: Triggering remote bots on AWS..." -ForegroundColor Yellow
        ssh -i "trading-key.pem" ubuntu@${AWS_IP} "cd ~/trading-bot && source venv/bin/activate && bash start_bot.sh"

        Write-Host "✅ SUCCESS! All bots (Nifty, BankNifty, Crude, NatGas) are now trading live on your AWS Server!" -ForegroundColor Green
        Write-Host "You can close this window. Check your AWS server logs to monitor them." -ForegroundColor Green
    }
}
Pause
