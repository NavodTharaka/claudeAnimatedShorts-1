"""Flag written/literary Sinhala and risky literal phrases in the Sinhala blocks.
  PYTHONIOENCODING=utf-8 python scripts/sinhala_lint.py [files...]   (default: out/blog/drafts/*.si.html and out/blog/old/*.si.html)
Counts are hints, not errors: every hit should be read and, if it is written-style, replaced with the spoken form."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FLAGS = {  # written/literary or suspicious -> suggestion
    "ඔබ": "ඔයා", "ඔබේ": "ඔයාගේ", "ඔහු": "එයා", "ඇය": "එයා", "ඇත": "තියෙනවා", "නොමැත": "නෑ", "මෙම": "මේ", "එම": "ඒ",
    "ඇතැම්": "සමහර", "සඳහා": "වලට/ට", "විසින්": "(drop)", "පමණක්": "විතරයි", "පමණි": "විතරයි", "එබැවින්": "ඒ නිසා",
    "කෙසේ වෙතත්": "ඒත්/ඒ කොහොම වුණත්", "තවද": "ඒ වගේම", "නමුත්": "ඒත්", "මෙහි": "මෙතන", "එහි": "ඒකේ", "පවතී": "තියෙනවා",
    "ස්ථිර": "confirm වෙලා තියෙන (if it meant firm/confirmed)", "විශ්මයජනක": "නියමයි", "ප්‍රශංසා": "(simplify)", "ආකර්ෂණය": "(simplify)",
    "අවසානයේදී": "අන්තිමට", "ඒ අනුව": "(simplify)", "වන්නේය": "(written)", "කරයි": "කරනවා", "වේ.": "වෙනවා.", "විය.": "වුණා.",
    "ඇති බව": "(check)", "කළේය": "කළා", "ගියේය": "ගියා",
}
WRITTEN_END = re.compile(r"(?:ේය|ීය|ෙයි|ඇත|වේ|විය)[\s.,;:!?]")


def lint(path):
    t = re.sub(r"<[^>]+>", " ", path.read_text(encoding="utf-8"))
    t = re.sub(r"https?://\S+", " ", t)
    sinhala_words = len(re.findall(r"[඀-෿]+", t))
    S = "඀-෿"
    prefix = {"ඔබ", "ඔහු", "මෙම", "එම", "ඇතැම්", "විසින්", "ස්ථිර", "විශ්මයජනක", "ප්‍රශංසා", "ආකර්ෂණය", "මෙහි", "එහි"}
    def count(k):
        pat = r"(?<![" + S + "])" + re.escape(k) + ("" if k in prefix else r"(?![" + S + "])")
        return len(re.findall(pat, t))
    hits = {k: count(k) for k in FLAGS}
    hits = {k: v for k, v in hits.items() if v}
    return sinhala_words, hits, sum(hits.values())


if __name__ == "__main__":
    files = [Path(a) for a in sys.argv[1:]] or sorted((ROOT / "out/blog/drafts").glob("*.si.html")) + sorted((ROOT / "out/blog/old").glob("*.si.html"))
    total = 0
    for f in files:
        w, hits, n = lint(f)
        total += n
        print(f"{f.name:30} sinhala words {w:5}  flags {n:3}  " + ", ".join(f"{k}x{v}" for k, v in sorted(hits.items(), key=lambda x: -x[1])[:8]))
    print("TOTAL flags:", total)
