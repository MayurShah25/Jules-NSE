# ☁️ Jules AWS Deployment Guide

This guide will walk you through launching an AWS EC2 server, installing the bot, and getting your daily automated trading server online.

### Step 1: Launch an AWS EC2 Instance
1. Go to the AWS Console -> **EC2 Dashboard** -> **Launch Instance**.
2. **Name:** `Jules Trading Bot`
3. **OS Image:** Select **Ubuntu 22.04 LTS** (or 24.04).
4. **Instance Type:** `t2.micro` or `t3.micro` (Free Tier is perfectly fine).
5. **Key Pair:** Create a new key pair (e.g. `trading-key.pem`) and download it.
6. **Network Settings:**
   - Check **Allow SSH traffic** (Port 22).
   - Check **Allow HTTP traffic**.
7. Click **Launch Instance**.

### Step 2: Connect to your Server
Open your terminal (Mac/Linux) or PowerShell (Windows) where your `.pem` key was downloaded.

**For Mac/Linux:**
```bash
# Secure your key
chmod 400 trading-key.pem

# SSH into the server
ssh -i "trading-key.pem" ubuntu@<YOUR_AWS_PUBLIC_IP>
```

**For Windows (PowerShell):**
```powershell
# Secure your key (Removes inherited permissions and grants access only to you)
icacls.exe trading-key.pem /reset
icacls.exe trading-key.pem /grant:r "$($env:USERNAME):(R)"
icacls.exe trading-key.pem /inheritance:r

# SSH into the server
ssh -i "trading-key.pem" ubuntu@<YOUR_AWS_PUBLIC_IP>
```

### Step 3: Install Dependencies
Once inside the AWS terminal, update the system and install Python:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3-pip python3-venv git tmux -y
```

### Step 4: Transfer the Code
You can securely copy all these files from your local machine to AWS using `scp`.
Open a **new terminal tab on your local computer** in this project directory:

```bash
scp -i "trading-key.pem" -r ./* ubuntu@<YOUR_AWS_PUBLIC_IP>:~/trading-bot/
```

### Step 5: Setup the Bot Environment
Go back to your AWS SSH terminal:

```bash
cd ~/trading-bot

# Create a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install the Python libraries
pip install pandas numpy ta kiteconnect yfinance flask
```

### Step 6: The Daily Morning Routine (Automated Sync)
Because Zerodha enforces strict validation rules that prevent redirecting directly to AWS Public IPs, we use a highly secure "Local Sync" method.

1. Ensure your Zerodha Redirect URL is set to `http://127.0.0.1:8000`.
2. Every morning around 8:45 AM, open **PowerShell** on your local Windows computer.
3. Run the automated deployment script by temporarily bypassing Windows execution policy blocks:
```powershell
powershell -ExecutionPolicy Bypass -File .\deploy_to_aws.ps1
```

**What the script does:**
1. Opens your local browser to log into Zerodha.
2. Generates the `access_token.txt` locally.
3. Asks for your AWS Public IP, then securely uploads the token to your server via SSH.
4. Tells the AWS server to quietly launch both the Nifty and BankNifty trading bots in the background.

You can safely close the PowerShell window! If you want to check on the bots later, simply SSH into your AWS server and type `cat nifty_bot.log` or `cat banknifty_bot.log`.
