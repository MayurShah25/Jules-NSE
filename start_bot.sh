#!/bin/bash
echo "==========================================="
echo "  Starting NSE Options Scalping Bot"
echo "  Mode: PAPER TRADING"
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

# Run the python script
python options_scalping_bot.py
