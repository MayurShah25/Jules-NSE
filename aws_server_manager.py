import os
import subprocess
from flask import Flask, request, redirect
from kiteconnect import KiteConnect

# Replace these with your actual keys or use Environment Variables
KITE_API_KEY = os.getenv("KITE_API_KEY", "YOUR_ZERODHA_API_KEY")
KITE_API_SECRET = os.getenv("KITE_API_SECRET", "YOUR_ZERODHA_API_SECRET")

app = Flask(__name__)
kite = KiteConnect(api_key=KITE_API_KEY)

@app.route("/")
def home():
    return "<h1>Jules Trading Server is Running</h1><a href='/login'>Click here to Login to Zerodha</a>"

@app.route("/login")
def login():
    # Redirects the user to the official Zerodha login page
    login_url = kite.login_url()
    return redirect(login_url)

@app.route("/api/callback")
def callback():
    # Zerodha redirects here with the request_token
    request_token = request.args.get("request_token")

    if not request_token:
        return "Login failed or request token missing.", 400

    try:
        # Convert request token to access token
        data = kite.generate_session(request_token, api_secret=KITE_API_SECRET)
        access_token = data["access_token"]

        # Save the token for the bots to use
        with open("access_token.txt", "w") as f:
            f.write(access_token)

        # Start the trading bots in the background using the centralized shell script
        subprocess.Popen(["bash", "start_bot.sh"])

        return "<h1>Success!</h1><p>Token generated securely. Nifty and BankNifty bots have been started in the background!</p><p>You can safely close this window.</p>"

    except Exception as e:
        return f"<h1>Error generating session</h1><p>{e}</p>", 500

if __name__ == "__main__":
    # Runs on port 8000, accessible from anywhere (0.0.0.0)
    app.run(host="0.0.0.0", port=8000)
