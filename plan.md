1. **Fix deploy_to_aws.ps1:**
   - Remove any existing `access_token.txt` before running the python login script to ensure we only upload a fresh token.

2. **Fix start_bot.sh:**
   - Add `pkill -f` to cleanly kill any existing bot instances before starting new ones, preventing duplicate live orders.
   - Add `nohup` to ensure the bots remain running after the SSH command disconnects.

3. **Update README_AWS.md:**
   - Modify the guide to reflect the new Option A workflow, removing references to the Flask AWS server.
