@echo off
echo ===========================================
echo   Starting Options Scalping Bots Menu
echo   Mode: LIVE TRADING
echo ===========================================
echo Ensure you have updated your Zerodha API keys.
echo Remember to run 'python zerodha_login.py' first if your daily token has expired.
echo Press Ctrl+C to safely stop the bot.
echo.

:: Check if access token exists
if not exist access_token.txt (
    echo [ERROR] access_token.txt not found.
    echo Please run zerodha_login.py to authenticate for today before starting the bot.
    pause
    exit /b
)

echo Select the bot you want to run:
echo 1. Nifty Options Scalping Bot
echo 2. BankNifty Options Scalping Bot
echo 3. Crude Oil MCX Mini Futures Scalping Bot
echo 4. Natural Gas MCX Mini Futures Scalping Bot
echo.

set /p choice="Enter your choice (1/2/3/4): "

if "%choice%"=="1" (
    python options_scalping_bot.py
) else if "%choice%"=="2" (
    python banknifty_scalping_bot.py
) else if "%choice%"=="3" (
    python crude_scalping_bot.py
) else if "%choice%"=="4" (
    python natgas_scalping_bot.py
) else (
    echo Invalid choice. Exiting.
)
pause
