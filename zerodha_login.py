import os
import sys

try:
    from kiteconnect import KiteConnect
except ImportError:
    print("Error: kiteconnect library not found. Run: pip install kiteconnect")
    sys.exit(1)

# ==========================================
# CONFIGURATION
# ==========================================
# Enter your Zerodha credentials here.
# Keep API_SECRET highly secure and never share it.
API_KEY = "YOUR_ZERODHA_API_KEY"
API_SECRET = "YOUR_ZERODHA_API_SECRET"

TOKEN_FILE = "access_token.txt"

def get_saved_token():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r") as f:
            return f.read().strip()
    return None

def main():
    if API_KEY == "YOUR_ZERODHA_API_KEY" or API_SECRET == "YOUR_ZERODHA_API_SECRET":
        print("❌ ERROR: You must update the API_KEY and API_SECRET in zerodha_login.py before running.")
        sys.exit(1)

    print("\n=== ZERODHA KITE CONNECT AUTO-LOGIN ===")

    kite = KiteConnect(api_key=API_KEY)

    print("\n1. Generating Login URL...")
    print("--------------------------------------------------")
    print(f"👉 CLICK/COPY THIS URL: {kite.login_url()}")
    print("--------------------------------------------------")

    print("\n2. Log in using your Zerodha credentials (Password + TOTP/PIN).")
    print("3. After login, your browser will redirect you to a blank page or your redirect URL.")
    print("4. Look at the URL bar. Find the 'request_token=' parameter.")

    request_token = input("\n👉 Paste your copied Request Token here: ").strip()

    if not request_token:
        print("❌ Error: No request token provided. Exiting.")
        sys.exit(1)

    print("\n⏳ Exchanging Request Token for Daily Access Token...")
    try:
        data = kite.generate_session(request_token, api_secret=API_SECRET)
        access_token = data["access_token"]

        # Save token to file for the bot to read automatically
        with open(TOKEN_FILE, "w") as f:
            f.write(access_token)

        print(f"✅ SUCCESS! Access Token generated and saved to {TOKEN_FILE}")
        print("\nYour token is valid until 7:30 AM tomorrow.")
        print("You can now start the main bot: python options_scalping_bot.py")

    except Exception as e:
        print(f"\n❌ AUTHENTICATION FAILED: {e}")
        print("This usually happens if the request token is invalid, expired (they only last 5 mins), or has already been used.")

if __name__ == "__main__":
    main()
