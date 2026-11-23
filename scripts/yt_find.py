"""Find an official trailer: yt_find.py "query" [expected channel substring]. Scrapes YouTube results, verifies via oEmbed (title + channel)."""
import re, sys, json, urllib.parse, urllib.request
UA={"User-Agent":"Mozilla/5.0","Accept-Language":"en-US,en;q=0.9"}
def get(u):
    return urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=20).read().decode("utf-8","ignore")
def is_short(i):
    """A Short keeps its /shorts/ URL; a normal video redirects to /watch."""
    try:
        r = urllib.request.urlopen(urllib.request.Request("https://www.youtube.com/shorts/" + i, headers=UA), timeout=20)
        return "/shorts/" in r.geturl()
    except Exception:
        return False


def find(q,n=8):
    h=get("https://www.youtube.com/results?search_query="+urllib.parse.quote(q))
    ids=[]
    for i in re.findall(r'"videoId":"([\w-]{11})"',h):
        if i not in ids: ids.append(i)
    out=[]
    for i in ids[:n]:
        try:
            o=json.loads(get("https://www.youtube.com/oembed?format=json&url=https://www.youtube.com/watch?v="+i))
            short = is_short(i)
            out.append((i, o["author_name"], ("[SHORT - skip] " if short else "") + o["title"]))
        except Exception as e: out.append((i,"?",str(e)[:30]))
    return out
if __name__=="__main__":
    for r in find(sys.argv[1]): print(*r,sep=" | ")
