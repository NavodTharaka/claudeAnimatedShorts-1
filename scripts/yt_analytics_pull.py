import json, sys
from pathlib import Path
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
R = Path(__file__).resolve().parent.parent
O = R / "out/curion-report"; O.mkdir(parents=True, exist_ok=True)
a = build("youtubeAnalytics", "v2", credentials=Credentials.from_authorized_user_file(str(R / "token_analytics.json")))
S, E = "2026-10-28", "2026-11-22"
def q(name, **kw):
    try:
        r = a.reports().query(ids="channel==MINE", startDate=S, endDate=E, **kw).execute()
        (O / f"an_{name}.json").write_text(json.dumps(r), encoding="utf-8")
        print("OK", name, len(r.get("rows", [])))
    except HttpError as e:
        print("ERR", name, e.resp.status, str(e)[:300]); return False
    return True
M = "views,estimatedMinutesWatched,averageViewDuration,averageViewPercentage,likes,comments,shares,subscribersGained,subscribersLost"
if not q("daily", metrics=M, dimensions="day", sort="day"): sys.exit(1)
q("video", metrics=M, dimensions="video", sort="-views", maxResults=50)
q("traffic", metrics="views,estimatedMinutesWatched,averageViewPercentage", dimensions="insightTrafficSourceType", sort="-views")
q("country", metrics="views,estimatedMinutesWatched,averageViewPercentage,subscribersGained", dimensions="country", sort="-views", maxResults=15)
q("demo", metrics="viewerPercentage", dimensions="ageGroup,gender")
q("device", metrics="views,averageViewPercentage", dimensions="deviceType", sort="-views")
q("sharing", metrics="shares", dimensions="sharingService", sort="-shares")
q("subsource", metrics="views,subscribersGained", dimensions="subscribedStatus")
q("shortsfeed", metrics="views,averageViewPercentage", dimensions="creatorContentType")
