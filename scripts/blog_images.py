"""Resolve a curated list of Wikimedia Commons images (key -> search query + title substring) into out/blog/images.json.
Slow on purpose (Commons rate-limits). Run: PYTHONIOENCODING=utf-8 python scripts/blog_images.py"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from commons_images import search  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / "out" / "blog" / "images.json"

# key: (query, substring that must be in the Commons file title)
SPEC = {
    "pc_setup": ("gaming PC", "Astaroth"),
    "ps5": ("PlayStation 5 console", "PlayStation 5 and DualSense.jpg"),
    "xbox_x": ("Xbox Series X console", "Xbox Series X 2"),
    "bungie_pax": ("Bungie", "Bungie Booth"),
    "miami": ("Miami skyline", "Miami skyline from the ocean"),
    "rockstar_e3": ("Rockstar Games", "buses at E3 2005"),
    "witcher2_press": ("Witcher gamescom", "press-kit from GamesCom 2010"),
    "witcher2_bartel": ("Witcher gamescom", "The Witcher 2.jpg"),
    "geralt_cosplay": ("Geralt Witcher cosplay", "Vladislav as Geralt"),
    "ciri_cosplay": ("Witcher 3", "Ciri Cosplay"),
    "iwinski": ("CD Projekt Red", "Marcin Iwiński.jpg"),
    "cyberpunk_pga": ("Cyberpunk 2077 CD Projekt", "PGA 2019 Cyberpunk"),
    "ac_cosplay1": ("Assassin's Creed cosplay", "group 01"),
    "ac_cosplay2": ("Assassin's Creed cosplay", "group 02"),
    "ezio": ("Assassin's Creed cosplay", "Ezio Auditore"),
    "masyaf": ("Masyaf Castle", "Masyaf castle by"),
    "venice": ("Venice Grand Canal", "Panorama of Canal Grande"),
    "giza": ("Giza pyramids", "All Gizah Pyramids"),
    "acropolis": ("Acropolis Athens", "Acropolis of Athens in Greece at night"),
    "longship": ("Viking longship", "Viking longship from The Odyssey"),
    "himeji": ("Himeji castle", "Himeji Castle, November 2016"),
    "baghdad": ("Baghdad", "Sunset in Baghdad"),
    "ubisoft_gc": ("Ubisoft", "Gamescom 2009 - Ubisoft"),
    "gamescom25": ("gamescom hall visitors", "Gamescom 2025"),
    "stray_gdc": ("Stray video game", "Stray GDC 2023.jpg"),
    "aoe4": ("Age of Empires", "Concept Art von Age of Empires IV"),
    "plague_bocklin": ("Black Death plague painting", "The Plague, 1898"),
    "plague_angel": ("Black Death plague painting", "angel of death striking a door"),
    "aew_page": ("All Elite Wrestling", "Hangman Adam Pag"),
    "aew_women": ("All Elite Wrestling", "Women's World Champion"),
    "cod_gc19": ("Call of Duty Modern Warfare", "Gamescom 2019"),
    "wh_e3": ("Warhammer 40,000", "Promotion of Warhammer 40,000"),
    "wh_marine": ("Warhammer 40,000", "Space Marine of the Salamanders"),
    "dundee": ("Dundee Scotland", "Dundee"),
    "la_skyline": ("Los Angeles skyline downtown", "Los Angeles"),
    "nyc": ("Manhattan skyline", "Manhattan"),
    "bj": ("Wolfenstein cosplay Blazkowicz", "Blazkowicz"),
    "doom_cos": ("Doom Slayer cosplay", "Doom"),
    "ac_origins_gc": ("Assassin's Creed Origins", "Gamescom Assassins Creed Origins (36680349392)"),
    "ac_origins_chars": ("Assassin's Creed Origins", "Gamescom Assassins Creed Origins Characters"),
    "ac_unity_pax": ("Assassin's Creed Unity", "PAX South 2015 - Assassin's Creed- Unity"),
    "ac_unity_elise": ("Assassin's Creed Unity", "Elise (Assassin's Creed Unity) - Salon du Livre de Paris 2015.jpg"),
    "ac_iv_ewen": ("Assassin's Creed Black Flag", "Assassin's Creed IV by Ewen Roberts"),
    "altair_cos": ("Altair Assassin's Creed cosplay", "Geek Kon 2014 (15096237332)"),
    "valhalla_cos": ("Assassin's Creed Valhalla", "Pyrkon 2023 cosplay"),
    "bastille": ("Bastille Paris", "Prise de la Bastille clean"),
    "notre_dame": ("Notre-Dame de Paris 2015", "Cathédrale Notre Dame, Paris 30 September 2015"),
    "tower_bridge": ("Tower Bridge London", "Tower Bridge from London City Hall 2015"),
    "old_north": ("Boston Old North Church", "Old North Church exterior.jpg"),
    "galleon": ("Spanish galleon replica ship", "Spanish Galleon replica MAR CCSD 02 2018"),
    "gta4a": ("Grand Theft Auto", "Grand Theft Auto IV.jpg"),
    "gta4b": ("Grand Theft Auto", "Grand Theft Auto IV 03.jpg"),
    "gta4c": ("Grand Theft Auto", "Grand Theft Auto 4.jpg"),
    "houser": ("Grand Theft Auto V", "Sam Houser and Dan Houser"),
    "rockstar_gdc": ("Rockstar Games", "Game Developers Choice Awards 2019"),
    "rockstar_north": ("Rockstar Games", "Former Rockstar North building"),
    "vegas": ("Las Vegas Strip", "Las Vegas Strip panorama"),
    "ggb": ("Golden Gate Bridge San Francisco", "Golden Gate bridge 3"),
    "gears_cos": ("Gears of War", "Gears of War cosplay at Comic-Con"),
    "fortnite_gdc": ("Fortnite", "Fortnite Battle Royale at GDC 2018"),
    "rockstar_north2": ("Rockstar North Edinburgh", "20231022 Rockstar North"),
    "dualsense": ("DualSense controller", "Playstation Dualsense controller.jpg"),
    "civ6_logo": ("Civilization VI Firaxis", "Civilization VI logo.jpg"),
    "sid_meier2": ("Sid Meier", "Sid Meier 2015-02-25.jpg"),
    "cod_mw2_launch": ("Call of Duty Modern Warfare", "Modern Warfare 2 Launch Party"),
}

if __name__ == "__main__":
    have = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    for k, (q, sub) in SPEC.items():
        if k in have:
            continue
        for attempt in range(5):
            try:
                hits = search(q, 12, 1280)
                break
            except Exception as e:
                time.sleep(10 * (attempt + 1))
                hits = []
        m = [h for h in hits if sub.lower() in h["title"].lower()]
        print(k, "OK" if m else "MISSING", (m[0]["title"][:60] if m else ""))
        if m:
            have[k] = m[0]
        OUT.write_text(json.dumps(have, ensure_ascii=False, indent=1), encoding="utf-8")
        time.sleep(3)
