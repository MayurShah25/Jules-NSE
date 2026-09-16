#!/bin/bash
echo "==========================================="
echo "  Starting NSE Options Scalping Bot"
echo "  Mode: LIVE TRADING"
echo "==========================================="
echo "Ensure you have updated your Zerodha API keys in options_scalping_bot.py"
echo "Remember to run 'python zerodha_login.py' first if your daily token has expired."
echo "Press Ctrl+C to safely stop the bot."
echo ""

if [ ! -f "access_token.txt" ]; then
    echo "❌ ERROR: access_token.txt not found."
    echo "Please run 'python zerodha_login.py' to authenticate for today before starting the bot."
    exit 1
fi

# Kill any existing bot instances to prevent duplicate live orders
echo "Terminating any existing bot instances..."
pkill -f "options_scalping_bot.py" || true
pkill -f "banknifty_scalping_bot.py" || true
sleep 2

# Run the python script securely in the background using nohup
echo "Starting Nifty Bot in the background..."
nohup python3 options_scalping_bot.py > nifty_bot.log 2>&1 &

echo "Starting BankNifty Bot in the background..."
nohup python3 banknifty_scalping_bot.py > banknifty_bot.log 2>&1 &

echo "All bots started successfully! Check nifty_bot.log and banknifty_bot.log for live output."
