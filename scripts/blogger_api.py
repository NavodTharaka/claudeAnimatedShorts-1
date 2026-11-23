"""Blogger API v3 helper.

  python scripts/blogger_api.py blogs
  python scripts/blogger_api.py posts <blogId> [maxResults]      # titles, dates, URLs, labels
  python scripts/blogger_api.py get <blogId> <postId>
  python scripts/blogger_api.py publish <blogId> post.html "Title" "label1,label2" [--draft]
"""
import json
import sys
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

ROOT = Path(__file__).resolve().parent.parent
TOKEN = ROOT / "token_blogger.json"


def service():
    creds = Credentials.from_authorized_user_file(str(TOKEN))
    if not creds.valid:
        creds.refresh(Request())
        TOKEN.write_text(creds.to_json(), encoding="utf-8")
    return build("blogger", "v3", credentials=creds)


def main(a):
    s = service()
    cmd = a[0]
    if cmd == "blogs":
        for b in s.blogs().listByUser(userId="self").execute().get("items", []):
            print(b["id"], b["name"], b["url"], "posts:", b["posts"]["totalItems"])
    elif cmd == "posts":
        n = int(a[2]) if len(a) > 2 else 50
        r = s.posts().list(blogId=a[1], maxResults=n, status="LIVE", fetchBodies=False).execute()
        for p in r.get("items", []):
            print(p["id"], p["published"][:10], p["title"], p.get("labels", []), p["url"])
    elif cmd == "get":
        p = s.posts().get(blogId=a[1], postId=a[2]).execute()
        print(json.dumps(p, indent=1)[:20000])
    elif cmd == "publish":
        body = {"title": a[3], "content": Path(a[2]).read_text(encoding="utf-8")}
        if len(a) > 4 and not a[4].startswith("--"):
            body["labels"] = [x.strip() for x in a[4].split(",") if x.strip()]
        r = s.posts().insert(blogId=a[1], body=body, isDraft="--draft" in a).execute()
        print(r["id"], r["status"] if "status" in r else "", r["url"])
    else:
        print(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
