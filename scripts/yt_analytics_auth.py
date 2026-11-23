"""One-off consent for read-only YouTube Analytics. Saves token_analytics.json (separate from the upload token)."""
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow
ROOT = Path(__file__).resolve().parent.parent
SCOPES = ["https://www.googleapis.com/auth/yt-analytics.readonly",
          "https://www.googleapis.com/auth/youtube.readonly"]
flow = InstalledAppFlow.from_client_secrets_file(str(ROOT / "credentials.json"), SCOPES)
creds = flow.run_local_server(port=0, prompt="consent", access_type="offline")
(ROOT / "token_analytics.json").write_text(creds.to_json(), encoding="utf-8")
print("Saved token_analytics.json")
