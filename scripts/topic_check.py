"""Pre-flight for a NEW topic, before any script is written (user rule 2026-11-22).
usage: python scripts/topic_check.py "<working title>" "keyword1,keyword2,..." [expected_length_seconds]
Scans EVERY video on the Curion channel (public, scheduled, private) and reports:
  1. what the upload duplicate guard would flag (title ratio >= 0.8, or length within 1.5 s and ratio >= 0.5) among the last 7 days + scheduled
  2. any video anywhere on the channel with a similar title (ratio >= 0.55)
  3. every video whose title, description or tags contain one of the keywords
Reads token.json (never printed). Read-only."""
import difflib, re, sys, datetime as dt
from pathlib import Path
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

R = Path(__file__).resolve().parent.parent
title = sys.argv[1]; kws = [k.strip().lower() for k in sys.argv[2].split(",") if k.strip()] if len(sys.argv) > 2 else []
secs = float(sys.argv[3]) if len(sys.argv) > 3 else None
yt = build("youtube", "v3", credentials=Credentials.from_authorized_user_file(str(R / "token.json")))
up = yt.channels().list(part="contentDetails", mine=True).execute()["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
ids, tok = [], None
while True:
    r = yt.playlistItems().list(part="contentDetails", playlistId=up, maxResults=50, pageToken=tok).execute()
    ids += [i["contentDetails"]["videoId"] for i in r["items"]]; tok = r.get("nextPageToken")
    if not tok: break
vids = []
for i in range(0, len(ids), 50):
    vids += yt.videos().list(part="snippet,status,contentDetails", id=",".join(ids[i:i + 50])).execute()["items"]
norm = lambda s: re.sub(r"[^a-z0-9 ]+", "", s.lower())
def seconds(d):
    m = re.match(r"PT(?:(\d+)M)?(?:(\d+)S)?", d or ""); return int(m.group(1) or 0) * 60 + int(m.group(2) or 0) if m else 0
now = dt.datetime.now(dt.timezone.utc)
rows = []
for v in vids:
    s, st = v["snippet"], v["status"]
    when = st.get("publishAt") or s["publishedAt"]
    w = dt.datetime.fromisoformat(when.replace("Z", "+00:00"))
    rows.append(dict(id=v["id"], title=s["title"], desc=s.get("description", ""), tags=s.get("tags", []), secs=seconds(v["contentDetails"].get("duration")), privacy=st["privacyStatus"], when=w,
                     recent=(now - w).days <= 7 or w > now, ratio=difflib.SequenceMatcher(None, norm(title), norm(s["title"])).ratio()))
print(f"channel videos scanned: {len(rows)}   candidate: {title!r}" + (f" ({secs:.0f} s)" if secs else ""))
g = [r for r in rows if r["recent"] and (r["ratio"] >= 0.8 or (secs is not None and abs(r["secs"] - secs) <= 1.5 and r["ratio"] >= 0.5))]
print("\n1. Upload guard would flag:", "NONE" if not g else "")
for r in g: print(f"   {r['ratio']:.0%}  {r['title']}  ({r['id']}, {r['privacy']}, {r['secs']} s, {r['when']:%Y-%m-%d %H:%MZ})")
s = sorted([r for r in rows if r["ratio"] >= 0.55], key=lambda r: -r["ratio"])
print("\n2. Similar titles anywhere on the channel (>= 55%):", "NONE" if not s else "")
for r in s: print(f"   {r['ratio']:.0%}  {r['title']}  ({r['id']}, {r['privacy']})")
k = [r for r in rows if any(w in (r["title"] + " " + r["desc"] + " " + " ".join(r["tags"])).lower() for w in kws)]
print(f"\n3. Videos mentioning any of {kws}:", "NONE" if not k else "")
for r in sorted(k, key=lambda r: r["when"]):
    hit = [w for w in kws if w in (r["title"] + " " + r["desc"] + " " + " ".join(r["tags"])).lower()]
    print(f"   {r['title'][:70]}  ({r['id']}, {r['privacy']}, {r['when']:%Y-%m-%d})  hits: {hit}")
