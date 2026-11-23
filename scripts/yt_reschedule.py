"""Move scheduled Curion videos to new publish times (or publish one now). YouTube only.
usage: python scripts/yt_reschedule.py plan.json [--apply]
plan.json: {"<videoId>": "2026-11-27T23:00:00Z" | "now", ...}
Without --apply it only prints what would change. Old settings are saved to out/curion-report/schedule-backup.json first.
Reads token.json (never printed)."""
import json, sys
from pathlib import Path
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

R = Path(__file__).resolve().parent.parent
plan = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
apply = "--apply" in sys.argv
yt = build("youtube", "v3", credentials=Credentials.from_authorized_user_file(str(R / "token.json")))
items = yt.videos().list(part="snippet,status", id=",".join(plan)).execute()["items"]
found = {v["id"]: v for v in items}
missing = [k for k in plan if k not in found]
if missing:
    sys.exit(f"not found on this channel: {missing}")
bk = R / "out/curion-report/schedule-backup.json"
old = json.loads(bk.read_text(encoding="utf-8")) if bk.exists() else {}
for vid, when in plan.items():
    v = found[vid]; st = dict(v["status"])
    print(f"{vid} | {v['snippet']['title'][:55]} | {st.get('privacyStatus')} {st.get('publishAt', '-')}  ->  {when}")
    old.setdefault(vid, {"title": v["snippet"]["title"], "privacyStatus": st.get("privacyStatus"), "publishAt": st.get("publishAt")})
if not apply:
    sys.exit("dry run: nothing changed (add --apply)")
bk.write_text(json.dumps(old, ensure_ascii=False, indent=1), encoding="utf-8")
keep = ("embeddable", "license", "publicStatsViewable", "selfDeclaredMadeForKids", "containsSyntheticMedia")
for vid, when in plan.items():
    st = found[vid]["status"]
    body = {k: st[k] for k in keep if k in st}
    if when == "now":
        body["privacyStatus"] = "public"
    else:
        body["privacyStatus"] = "private"; body["publishAt"] = when
    yt.videos().update(part="status", body={"id": vid, "status": body}).execute()
    print("OK", vid, when)
