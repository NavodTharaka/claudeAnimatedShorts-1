"""One-off consent for Blogger (read + write posts). Saves token_blogger.json.

Sign in with the Google account that OWNS/administers the gaming blog.
Requires the Blogger API v3 to be enabled in the Google Cloud project that owns credentials.json.
"""
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow

ROOT = Path(__file__).resolve().parent.parent
SCOPES = ["https://www.googleapis.com/auth/blogger"]
flow = InstalledAppFlow.from_client_secrets_file(str(ROOT / "credentials.json"), SCOPES)
creds = flow.run_local_server(port=0, prompt="consent", access_type="offline")
(ROOT / "token_blogger.json").write_text(creds.to_json(), encoding="utf-8")
print("Saved token_blogger.json")
