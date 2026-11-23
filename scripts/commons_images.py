"""Search Wikimedia Commons for freely licensed images.
  python scripts/commons_images.py "query" [n] [thumbWidth]
Prints title | size | license | author | thumb url. Use PYTHONIOENCODING=utf-8 on Windows."""
import json
import re
import sys
import urllib.parse
import urllib.request

UA = "BlogImageFinder/1.0 (free-image search)"


def search(q, n=8, w=1280):
    p = {"action": "query", "generator": "search", "gsrnamespace": 6, "gsrsearch": q + " filetype:bitmap", "gsrlimit": n,
         "prop": "imageinfo", "iiprop": "url|extmetadata|size", "iiurlwidth": w, "format": "json"}
    r = urllib.request.Request("https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(p), headers={"User-Agent": UA})
    d = json.load(urllib.request.urlopen(r)).get("query", {}).get("pages", {})
    out = []
    for pg in sorted(d.values(), key=lambda x: x.get("index", 0)):
        i = pg["imageinfo"][0]
        m = i["extmetadata"]
        out.append(dict(title=pg["title"], w=i["width"], h=i["height"], url=i.get("thumburl") or i["url"], page=i["descriptionurl"],
                        lic=m.get("LicenseShortName", {}).get("value", ""),
                        author=re.sub("<[^>]+>", "", m.get("Artist", {}).get("value", "")).strip()))
    return out


if __name__ == "__main__":
    for x in search(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 8, int(sys.argv[3]) if len(sys.argv) > 3 else 1280):
        print(x["title"][:60], "|", x["w"], "x", x["h"], "|", x["lic"], "|", x["author"][:25], "|", x["url"])
