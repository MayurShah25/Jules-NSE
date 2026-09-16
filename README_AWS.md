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
   - Edit the Security Group to add a **Custom TCP Rule** for Port `8000` (Source: `0.0.0.0/0`). *This allows you to access the login URL from your phone.*
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

### Step 6: Start the Server inside Tmux
We use `tmux` so that the server stays alive even when you close your SSH connection.

```bash
# Start a tmux session
tmux new -s trading

# Activate environment and run the server
source venv/bin/activate
python3 aws_server_manager.py
```
*Tip: To safely exit the tmux screen without killing the server, press `Ctrl+B`, then `D` (detach).*

### Step 7: The Daily Morning Routine
1. Type `http://<YOUR_AWS_PUBLIC_IP>:8000` into your phone/browser.
2. Click the Login link.
3. Once authenticated, the server grabs your `access_token` and automatically launches **both** `options_scalping_bot.py` and `banknifty_scalping_bot.py` in the background.

*(Once you generate a Static/Elastic IP later, you just update the IP address!)*
