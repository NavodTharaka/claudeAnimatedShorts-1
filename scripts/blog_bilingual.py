"""Build and publish the bilingual (EN + spoken-mixed Sinhala) content for all 16 posts.
New posts: out/blog/drafts/<name>.src.html (EN, markers) + <name>.si.html.   Old posts: live EN content + out/blog/old/<name>.si.html.
Sinhala blocks copy the English photo <figure>s unchanged (captions stay English). Run: PYTHONIOENCODING=utf-8 python scripts/blog_bilingual.py [--dry]"""
import html
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from blog_compile import compile_markers, bilingual, video, IMG  # noqa: E402
from blogger_api import service  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "out" / "blog"
B = "7850952045576056145"
DRY = "--dry" in sys.argv

NEW = {  # name: (post id, Sinhala title)
    "gta-6-engagement": ("8546119533762071961", "GTA 6 Launch Day එකේදි මුළු ලෝකෙම Console Playtime එකෙන් වැඩිම හරියක් ගිලගෙන! PS5 ප්ලේයර්ස්ලාගෙන් 61% ක් සහ Xbox ප්ලේයර්ස්ලාගෙන් 56% ක් පළවෙනි දවසෙම GTA 6 ගහලා! 🎮🔥"),
    "firaxis-layoffs": ("433894064751089870", "Civilization සහ XCOM හැදූ Firaxis ස්ටූඩියෝවට ලොකු පහරක්: කාර්ය මණ්ඩලයෙන් තුනෙන් එකක් ඉවතට, Studio Head ත් ඉල්ලා අස්වෙයි! 📉🎮"),
    "gta-6-sales": ("1953643074622018820", "GTA 6 පළවෙනි දවසේම ඩොලර් බිලියන 3.79 ක් හම්බ කළා කියලා Rockstar කියනවා"),
    "ubisoft-h1": ("8393321107746165025", "Ubisoft ආයතනයට මාස 6ක් ඇතුළත යුරෝ මිලියන 254.5 ක දැවැන්ත පාඩුවක්! හැබැයි Assassin's Creed Black Flag Resynced නිසා බලාපොරොත්තු වුණාටත් වඩා හොඳ ආදායමක් ලැබිලා! 🏴‍☠️📉"),
    "tga-2026": ("8300134955592675441", "The Game Awards 2026 ගේ nominees: GTA 6 නාමයෝජනා අටකින් ඉදිරියෙන්ම"),
    "gears-eday": ("1435905804581534232", "Gears of War: E-Day ගැන Online කියන දේට වඩා ඒක හොඳට යනවා"),
    "gta-6-guide": ("6997942792734697014", "GTA 6 ගැන හැමදේම එක තැනකින්: Story එක, Cheat Codes සහ අලුත් Gameplay Features!"),
    "marathon-symbiosis": ("2419027291198561330", "Marathon එකට Symbiosis update එක: ගොඩක් අය ඉල්ලපු PvE mode එක අන්තිමට එනවා"),
    "wolfenstein-3": ("7577546181935399395", "Wolfenstein 3 නිල වශයෙන් production එකේ: අපි දන්න හැම දෙයක්ම"),
    "gta-6-launch": ("884690271206636946", "GTA 6 එළියට ආවා: reviews නම් පට්ට, ඒත් 30 fps ගැන ලොකු argument එකක්"),
    "witcher-history": ("7354885347582097397", "The Witcher කතාව: අවදානම් පෝලන්ත RPG එකක් දැවැන්ත series එකක් වුණු හැටි"),
    "ac-history": ("5567926067178265619", "Assassin's Creed පැහැදිලි කිරීම: Altaïr ඉඳන් Naoe වෙනකම් හැම game එකක්ම connect වෙන හැටි"),
    "gta-history": ("1809501901829372523", "Grand Theft Auto ඉතිහාසය: 1997 top-down chaos එකේ ඉඳන් GTA 6 වෙනකම්"),
    "december-releases": ("3352089550354956110", "2026 දෙසැම්බර් අලුත් game releases: මොනවද play කරන්න වටින්නේ?"),
}
OLD = {
    "tobacco": ("5718523154716824695", "Tobacco Shop Simulator: නවත්තන්න බැරි වෙන smoke shop game එකක්"),
    "warhammer": ("6197482690499154852", "Warhammer 40,000: Space Marine – Master Crafted Edition (PC) Review"),
    "freedom": ("2251350705136960736", "Freedom Fighters: අමතක කරන්න බැරි classic game එක"),
    "aew": ("5299242005642262616", "AEW Fight Forever Review: N64 කාලේ wrestling games ආපහු ආවා"),
    "plague": ("6345967130396840822", "A Plague Tale: Innocence Review"),
    "warzone": ("7285847837392391016", "Call of Duty: Warzone 2.0: launch එකට කලින් දැනගන්න ඕන හැමදේම"),
    "witcher-remake": ("1781738108009284810", "The Witcher 3 Next-Gen Update එක දෙසැම්බර් 14 වෙනිදා එනවා"),
    "stray": ("8529189706580079568", "Stray Review: cyberpunk නගරයක බළලෙක් විදිහට ගමනක්"),
    "aoe": ("8769719555477158747", "Age of Empires: series එකේ ඉතිහාසය සහ games ඔක්කොම"),
}


FIXES = {  # proofreading fixes to the user's old English posts: (regex, replacement)
    "aew": [(r"Battle\s+Forever", "Fight Forever")],
    "aoe": [(r"Age\s+of\s+Mythology\s+\(2002\),\s+Age\s+of\s+Empires\s+III\s+\(1999\),\s+and\s+Age\s+of\s+Empires\s+II:\s+The\s+Age\s+of\s+Kings\s+\(1999\)\.\s+\(2005\)\.",
             "Age of Empires II: The Age of Kings (1999), Age of Mythology (2002), and Age of Empires III (2005).")],
    "witcher-remake": [(r"But it's currently been put delayed", "The update has already been delayed once, though.")],
    "freedom": [(r"almost\s+two\s+decades\s+ago", "more than two decades ago")],
    "plague": [(r">\s*Recommend\s*<", ">Recommended<")],
}
EN_PREFIX = {"warzone": "<p><em>Note: this guide was written for the Warzone 2.0 launch in November 2022, so the times and details are from that day.</em></p>"}
TITLES = {"witcher-remake": "The Witcher 3 Next-Gen Update Arrives December 14"}


def proofread(n, en):
    for pat, rep in FIXES.get(n, []):
        en, k = re.subn(pat, rep, en, flags=re.S | re.I)
        print("  fix", n, "ok" if k else "NOT FOUND", pat[:30])
    return EN_PREFIX.get(n, "") + en if EN_PREFIX.get(n, "") not in en else en


def defang(h):
    """Remove inline white backgrounds and hard-coded dark text colours left over from copy-pasted posts."""
    h = re.sub(r"background(?:-color)?\s*:\s*[^;\"']*;?", "", h, flags=re.I)
    h = re.sub(r"(?<![-\w])color\s*:\s*(?:black|#000000|#000|#252525|rgb\(\s*0\s*,\s*0\s*,\s*0\s*\))\s*;?", "", h, flags=re.I)
    return re.sub(r'\sstyle="\s*"', "", h)


def clean(c):
    c = re.sub(r"<!DOCTYPE[^>]*>", "", c, flags=re.I)
    c = re.sub(r"<head>.*?</head>", "", c, flags=re.S | re.I)
    c = re.sub(r"</?(html|body)[^>]*>", "", c, flags=re.I)
    c = re.sub(r"<style.*?</style>", "", c, flags=re.S | re.I)
    return re.sub(r"<meta[^>]*>", "", c, flags=re.I)


def image_blocks(orig):
    """Original (pre-figure) image blocks in document order: separator divs containing an <img>, or bare <img>s."""
    out = []
    for m in re.finditer(r'(<div class="separator"[^>]*>.*?</div>)|(<img[^>]+>)', orig, flags=re.S):
        if m.group(1) and "<img" not in m.group(1):
            continue
        out.append(m.group(0))
    return out


def copy_figure(en, key):
    base = IMG[key]["url"].split("?")[0].rsplit("/", 1)[-1]
    m = re.search(r"<figure[^>]*>(?:(?!</figure>).)*?" + re.escape(base) + r".*?</figure>", en, flags=re.S)
    if not m:
        raise SystemExit(f"figure {key} not found in English block")
    return m.group(0)


OLD_VIDEOS = {  # old posts: video placed after the first paragraph (English block and Sinhala block)
    "tobacco": ("hYNHMx9mBWQ", "Official release trailer for Tobacco Shop Simulator."),
    "warhammer": ("7YxYLWIJfP8", "Official trailer for Space Marine: Master Crafted Edition from the Warhammer channel."),
    "aew": ("jnBJapAva3k", "AEW: Fight Forever trailer from THQ Nordic."),
    "plague": ("_7Jj_G425yU", "Official gameplay overview trailer from Focus Entertainment."),
    "warzone": ("PEMQVB8RXUs", "The official Warzone 2.0 launch trailer (PlayStation channel)."),
    "witcher-remake": ("nBT2SP21f3Q", "Official next-gen update trailer from The Witcher channel."),
    "stray": ("4uP2MyUL49s", "Official launch trailer from Annapurna Interactive."),
    "freedom": ("pDkqQjyI6FY", "Trailer for the original 2003 game. It comes from a fan channel; I couldn't find an official upload."),
    "aoe": ("g5GwKbk2ihA", "Official trailer for Age of Empires: Definitive Edition."),
}


def add_old_video(n, en):
    if n not in OLD_VIDEOS or "youtube-nocookie.com/embed/" + OLD_VIDEOS[n][0] in en:
        return en
    fig = video(*OLD_VIDEOS[n])
    i = en.find("</p>")
    return en[:i + 4] + chr(10) + fig + en[i + 4:] if i >= 0 else fig + en


def copy_video(en, vid):
    m = re.search(r'<figure class="wide video">(?:(?!</figure>).)*?' + re.escape(vid) + r".*?</figure>", en, flags=re.S)
    if not m:
        raise SystemExit(f"video {vid} not found in English block")
    return m.group(0)


def fill_si(si_src, en, blocks):
    si_src = re.sub(r"\[\[vid ([\w-]{11})[^\]]*\]\]", lambda m: copy_video(en, m.group(1)), si_src)
    si = re.sub(r"\[\[img (\w+)[^\]]*\]\]", lambda m: copy_figure(en, m.group(1)), si_src)
    return re.sub(r"\[\[old (\d+)\]\]", lambda m: defang(blocks[int(m.group(1)) - 1]), si)


def snippet(si):
    m = re.search(r"<p>(.*?)</p>", re.sub(r"<figure.*?</figure>", "", si, flags=re.S), re.S)
    t = html.unescape(re.sub(r"<[^>]+>", "", m.group(1))).strip() if m else ""
    return (t[:170].rsplit(" ", 1)[0] + "…") if len(t) > 170 else t


def main():
    svc = service()
    backup = {p["id"]: p for p in json.loads((D / "backup_posts_2026-11-22.json").read_text(encoding="utf-8"))}
    jobs = []
    for n, (pid, t) in NEW.items():
        en = compile_markers((D / "drafts" / f"{n}.src.html").read_text(encoding="utf-8"), "en")
        si = fill_si((D / "drafts" / f"{n}.si.html").read_text(encoding="utf-8"), en, [])
        jobs.append((n, pid, t, en, si))
    for n, (pid, t) in OLD.items():
        live = svc.posts().get(blogId=B, postId=pid).execute()["content"]
        live = re.sub(r'^<div class="lang-en">|</div>\s*<div class="lang-si".*$', "", live, flags=re.S)  # idempotent re-run
        en = add_old_video(n, proofread(n, defang(clean(live))))
        blocks = image_blocks(clean(backup[pid]["content"]))
        si_src = (D / "old" / f"{n}.si.html").read_text(encoding="utf-8")
        if n in OLD_VIDEOS and OLD_VIDEOS[n][0] not in si_src:
            i = si_src.find("</p>")
            si_src = si_src[:i + 4] + chr(10) * 2 + "[[vid " + OLD_VIDEOS[n][0] + "]]" + si_src[i + 4:]
        si = fill_si(si_src, en, blocks)
        jobs.append((n, pid, t, en, si))
    for n, pid, t, en, si in jobs:
        h = bilingual(en, si, t, snippet(si))
        (D / "drafts" / f"{n}.bilingual.html").write_text(h, encoding="utf-8")
        if not DRY:
            body = {"content": h}
            if n in TITLES:
                body["title"] = TITLES[n]
            r = svc.posts().patch(blogId=B, postId=pid, body=body).execute()
            print("updated", r["title"][:44].ljust(44), "| figs EN", en.count("<figure"), "SI", si.count("<figure"), "| imgs EN", en.count("<img"), "SI", si.count("<img"))
        else:
            print("dry", n, "| figs", en.count("<figure"), si.count("<figure"), "| imgs", en.count("<img"), si.count("<img"))


if __name__ == "__main__":
    main()
