#!/bin/bash
# ==========================================
# JULES: AUTOMATED AWS DEPLOYMENT SCRIPT
# ==========================================
# Run this script locally on your Mac/Linux machine every morning!

echo -e "\033[36m===========================================\033[0m"
echo -e "\033[36m  Jules Automated AWS Token Sync (Linux/Mac)\033[0m"
echo -e "\033[36m===========================================\033[0m"

# 1. Generate Token Locally
echo -e "\033[33mStep 1: Generating Zerodha Token Locally...\033[0m"
if [ -f "access_token.txt" ]; then
    rm access_token.txt
fi
python3 zerodha_login.py

if [ ! -f "access_token.txt" ]; then
    echo -e "\033[31m❌ Error: access_token.txt was not generated! Aborting.\033[0m"
    return 1 2>/dev/null
fi

# Prompt user for IP (can hardcode later)
read -p "Enter your AWS Public IP address: " AWS_IP

# 2. Upload Token & Code to AWS
echo -e "\033[33mStep 2: Uploading token securely to AWS Server...\033[0m"
# Assuming trading-key.pem is in the same directory
scp -i "trading-key.pem" access_token.txt ubuntu@${AWS_IP}:~/trading-bot/

if [ $? -ne 0 ]; then
    echo -e "\033[31m❌ Error: Failed to upload token. Check your SSH key and IP.\033[0m"
    return 1 2>/dev/null
fi

# 3. Start Remote Bots
echo -e "\033[33mStep 3: Triggering remote bots on AWS...\033[0m"
ssh -i "trading-key.pem" ubuntu@${AWS_IP} "cd ~/trading-bot && source venv/bin/activate && bash start_bot.sh"

echo -e "\033[32m✅ SUCCESS! All bots (Nifty, BankNifty, Crude, NatGas) are now trading live on your AWS Server!\033[0m"
echo -e "\033[32mYou can close this window. Check your AWS server logs to monitor them.\033[0m"
