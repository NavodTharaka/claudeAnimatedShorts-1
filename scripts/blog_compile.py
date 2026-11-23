"""Turn [[img key | caption | alt | tall]] markers into <figure> blocks with licence credit (data from out/blog/images.json)."""
import html
import json
import re
from pathlib import Path

IMG = json.loads((Path(__file__).resolve().parent.parent / "out" / "blog" / "images.json").read_text(encoding="utf-8"))
FIX = {"plague_bocklin": "Arnold Böcklin", "rockstar_e3": "Cian Ginty", "plague_angel": "Wellcome Collection"}


def figure(key, caption, alt, tall=False, lang="en"):
    i = IMG[key]
    lic = i["lic"] if i["lic"] != "Attribution" else "CC BY"
    who = FIX.get(key) or re.sub(r"\s+", " ", i["author"]).split(" from ")[0].strip()
    url = i["url"].split("?")[0]
    cap = f'{html.escape(caption)} {"ඡායාරූපය" if lang == "si" else "Photo"}: {html.escape(who)} / <a href="{i["page"]}" rel="noopener" target="_blank">Wikimedia Commons</a> / {html.escape(lic)}'
    return (f'<figure class="{"tall" if tall else "wide"}"><img alt="{html.escape(alt, quote=True)}" loading="lazy" src="{url}"/>'
            f'<figcaption>{cap}</figcaption></figure>')


def video(vid, caption, lang="en"):
    cap = html.escape(caption)
    return (f'<figure class="wide video"><div style="position:relative;width:100%;aspect-ratio:16/9;background:#000;border-radius:8px;overflow:hidden">'
            f'<iframe src="https://www.youtube-nocookie.com/embed/{vid}" title="{html.escape(caption, quote=True)}" loading="lazy" '
            f'style="position:absolute;inset:0;width:100%;height:100%;border:0" allow="accelerometer; encrypted-media; gyroscope; picture-in-picture; web-share" '
            f'referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe></div>'
            f'<figcaption>{cap} <a href="https://www.youtube.com/watch?v={vid}" rel="noopener" target="_blank">Watch on YouTube</a></figcaption></figure>')


def compile_markers(text, lang="en"):
    text = re.sub(r"\[\[vid ([\w-]{11}) \| (.*?)\]\]", lambda m: video(m.group(1), m.group(2), lang), text)
    def rep(m):
        parts = [p.strip() for p in m.group(1).split("|")]
        return figure(parts[0], parts[1], parts[2] if len(parts) > 2 else parts[1], len(parts) > 3 and parts[3] == "tall", lang)
    return re.sub(r"\[\[img (.*?)\]\]", rep, text, flags=re.S)


def bilingual(en_html, si_html, si_title, si_snippet):
    """English block + Sinhala block (hidden until the visitor switches language). Blogger keeps data-* attributes."""
    q = lambda t: html.escape(t, quote=True)
    return (f'<div class="lang-en">{en_html}</div>' + chr(10) +
            f'<div class="lang-si" data-snippet="{q(si_snippet)}" data-title="{q(si_title)}" lang="si">{si_html}</div>')
