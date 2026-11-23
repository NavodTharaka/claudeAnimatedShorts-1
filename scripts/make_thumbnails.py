#!/usr/bin/env python3
"""Build designed YouTube thumbnails for every Curion short, in two sizes:
  out/thumbnails/vertical_1080x1920/   (Shorts: Google recommends 9:16)
  out/thumbnails/landscape_1280x720/   (search, channel page, Facebook cover)
Design rules (from the 2026 thumbnail research): a character/face, high contrast, 2-3 big bold words, text kept out of the
character, nothing tiny. Layout: navy hook band on top (line 1 white, line 2 yellow, black outline) + the frame below; a small
CURION tag bottom-right. Old videos have captions burned in, so only the part above the caption area is used.

Run from the project root with Pillow on the path:
  PYTHONPATH=.claude/skills/youtube-upload/_deps python scripts/make_thumbnails.py
"""
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "out" / "thumbnails"
WORK = OUT / "_work"
FONT = ROOT / ".claude/skills/faceless-shorts/styles/tall-tale/example/fonts/Inter-Black.otf"
NAVY = (20, 24, 46)
YELLOW = (255, 226, 31)
WHITE = (255, 255, 255)
INK = (10, 10, 16)

# key, title, YouTube id, source (png/jpg frame OR (mp4, seconds)), caption-safe height (None = clean frame),
# hook lines, accent colour, vertical image top (y0 of the 1480px window), landscape image top (y0 of the 1215px window)
VIDEOS = [
    ("01-why-do-we-yawn", "Why do we yawn when someone else yawns?", "tJQeESYP1mg", WORK / "why-yawn/t1.50.jpg", None, ("YAWNS ARE", "CONTAGIOUS"), (150, 110, 230), 330, 380),
    ("02-why-do-we-get-hiccups", "Why do we get hiccups?", "A_J72pQhJKU", WORK / "why-hiccups/t0.60.jpg", None, ("68 YEARS OF", "HICCUPS"), (232, 69, 107), 250, 330),
    ("03-why-does-brain-freeze-hurt", "Why does brain freeze hurt so much?", "9Oydb6TvrNg", WORK / "why-brain-freeze/t3.60.jpg", None, ("YOUR BRAIN", "ISN'T FREEZING"), (60, 158, 216), 300, 450),
    ("04-why-do-fingers-get-wrinkly", "Why do our fingers get wrinkly in water?", "SCnPgbKzNNc", WORK / "why-wrinkly-fingers/t5.70.jpg", None, ("NOT JUST", "WATER"), (80, 200, 230), 200, 300),
    ("05-why-do-we-sneeze-eyes-closed", "Why do we sneeze with our eyes closed?", "-lcBVBBenGA", WORK / "why-sneeze-eyes-closed/t14.20.jpg", None, ("EYES WON'T", "POP OUT"), (255, 154, 42), 420, 400),
    ("06-why-do-you-get-goosebumps", "Why do you get goosebumps?", "fXIaTinstJA", (ROOT / "out/goosebumps/renders/why-do-you-get-goosebumps.mp4", 6.02), 1235, ("A LEFTOVER", "FROM FUR"), (60, 158, 216), 0, 0),
    ("07-what-happens-if-you-swallow-gum", "What Really Happens If You Swallow Gum?", "q_DJp-Hfa5g", (ROOT / "out/gum/renders/gum.mp4", 45.5), 1235, ("NOT", "7 YEARS!"), (232, 69, 107), 0, 0),
    ("08-what-happens-when-you-hold-your-breath", "The burn when you hold your breath", "iyZ0UXSLHKg", (ROOT / "out/holdbreath/renders/what-happens-when-you-hold-your-breath.mp4", 1.92), 1400, ("NOT OUT OF", "OXYGEN"), (232, 69, 107), 0, 0),
    ("09-where-does-your-food-go-after-the-stomach", "Where does your food go after the stomach?", "yX10EEgBNmw", (ROOT / "out/digestion-journey/renders/where-does-your-food-go-after-the-stomach.mp4", 3.15), 1235, ("WHERE FOOD", "GOES NEXT"), (109, 187, 74), 0, 0),
]


def load_frame(src):
    if isinstance(src, tuple):
        mp4, t = src
        tmp = WORK / f"_{mp4.stem}_{t}.jpg"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(t), "-i", str(mp4), "-frames:v", "1", "-vf", "scale=1080:1920", str(tmp)], check=True)
        src = tmp
    return Image.open(src).convert("RGB").resize((1080, 1920), Image.LANCZOS)


def boost(im):
    im = ImageEnhance.Color(im).enhance(1.12)
    return ImageEnhance.Contrast(im).enhance(1.06)


def fit_font(text, max_w, max_size):
    size = max_size
    while size > 20:
        f = ImageFont.truetype(str(FONT), size)
        if f.getlength(text) <= max_w:
            return f
        size -= 4
    return ImageFont.truetype(str(FONT), 20)


def draw_outlined(d, xy, text, font, fill, outline_w):
    x, y = xy
    for dx in range(-outline_w, outline_w + 1, 2):                                # shadow + thick outline
        for dy in range(-outline_w, outline_w + 1, 2):
            if dx * dx + dy * dy <= outline_w * outline_w:
                d.text((x + dx + 4, y + dy + 8), text, font=font, fill=(0, 0, 0, 110))
    for dx in range(-outline_w, outline_w + 1):
        for dy in range(-outline_w, outline_w + 1):
            if dx * dx + dy * dy <= outline_w * outline_w:
                d.text((x + dx, y + dy), text, font=font, fill=INK)
    d.text((x, y), text, font=font, fill=fill)


def hook_block(canvas, lines, box, accent, align="center"):
    """Draw the two hook lines inside box = (x0, y0, x1, y1), auto-sized so both lines fit."""
    x0, y0, x1, y1 = box
    d = ImageDraw.Draw(canvas)
    w = x1 - x0
    fonts = [fit_font(lines[0], w, 190), fit_font(lines[1], w, 190)]
    size = min(f.size for f in fonts)                                            # same size on both lines
    f = ImageFont.truetype(str(FONT), size)
    lh = int(size * 1.02)
    total = lh * 2
    ty = y0 + ((y1 - y0) - total) // 2
    ow = max(6, size // 11)
    for i, (txt, col) in enumerate(zip(lines, (WHITE, YELLOW))):
        tw = f.getlength(txt)
        tx = x0 + (w - tw) / 2 if align == "center" else x0
        draw_outlined(d, (tx, ty + i * lh - size * 0.1), txt, f, col, ow)


def tag(canvas, x_right, y_bottom, scale=1.0):
    d = ImageDraw.Draw(canvas)
    f = ImageFont.truetype(str(FONT), int(40 * scale))
    tw = f.getlength("CURION")
    pad = int(18 * scale)
    x0, y0 = x_right - tw - 2 * pad, y_bottom - int(40 * scale) - 2 * pad + 8
    d.rounded_rectangle([x0, y0, x_right, y_bottom], radius=int(22 * scale), fill=YELLOW, outline=INK, width=4)
    d.text((x0 + pad, y0 + pad - 4), "CURION", font=f, fill=INK)


def vertical(im, safe_h, hook, accent, y0):
    W, H, BAND = 1080, 1920, 440
    canvas = Image.new("RGB", (W, H), NAVY)
    area_h = H - BAND                                                            # 1480
    if safe_h:                                                                   # old video: use only the part above the captions
        src = im.crop((0, 0, W, safe_h))
        s = area_h / safe_h
        src = src.resize((int(W * s), area_h), Image.LANCZOS)
        left = (src.width - W) // 2
        img = src.crop((left, 0, left + W, area_h))
    else:
        img = im.crop((0, y0, W, y0 + area_h))
    canvas.paste(boost(img), (0, BAND))
    d = ImageDraw.Draw(canvas)
    for i in range(BAND):                                                        # a soft top-to-bottom navy gradient
        shade = int(14 * (1 - i / BAND))
        d.line([(0, i), (W, i)], fill=(NAVY[0] + shade, NAVY[1] + shade, NAVY[2] + shade * 2))
    d.rectangle([0, BAND - 16, W, BAND], fill=accent)
    hook_block(canvas, hook, (50, 40, W - 50, BAND - 40), accent)
    d.rectangle([0, 0, W - 1, H - 1], outline=accent, width=10)
    tag(canvas, W - 36, H - 36)
    return canvas


def landscape(im, safe_h, hook, accent, y0):
    W, H, LEFT = 1280, 720, 640
    canvas = Image.new("RGB", (W, H), NAVY)
    if safe_h:
        crop_h = min(safe_h, 1215)
        img = im.crop((0, 0, 1080, crop_h))
    else:
        crop_h = 1215
        img = im.crop((0, y0, 1080, y0 + crop_h))
    s = 720 / crop_h
    img = img.resize((int(1080 * s), 720), Image.LANCZOS)
    left = (img.width - 640) // 2
    canvas.paste(boost(img.crop((left, 0, left + 640, 720))), (LEFT, 0))
    d = ImageDraw.Draw(canvas)
    d.rectangle([LEFT - 14, 0, LEFT, H], fill=accent)
    hook_block(canvas, hook, (36, 90, LEFT - 36, H - 150), accent)
    d.rectangle([0, 0, W - 1, H - 1], outline=accent, width=8)
    tag(canvas, LEFT - 36, H - 36, 0.9)
    return canvas


def main():
    WORK.mkdir(parents=True, exist_ok=True)
    (OUT / "vertical_1080x1920").mkdir(parents=True, exist_ok=True)
    (OUT / "landscape_1280x720").mkdir(parents=True, exist_ok=True)
    rows = []
    for key, title, vid, src, safe, hook, accent, vy0, ly0 in VIDEOS:
        im = load_frame(src)
        v = vertical(im, safe, hook, accent, vy0)
        v.save(OUT / "vertical_1080x1920" / f"{key}.jpg", quality=92)
        l = landscape(im, safe, hook, accent, ly0)
        l.save(OUT / "landscape_1280x720" / f"{key}.jpg", quality=92)
        rows.append((key, title, vid, " ".join(hook)))
        print("made", key)
    # overview sheet + README
    sheet = Image.new("RGB", (9 * 270, 480 + 190 * 2 + 20), (30, 30, 40))
    for i, (key, *_r) in enumerate(rows):
        sheet.paste(Image.open(OUT / "vertical_1080x1920" / f"{key}.jpg").resize((270, 480)), (i * 270, 0))
    for i, (key, *_r) in enumerate(rows):
        sheet.paste(Image.open(OUT / "landscape_1280x720" / f"{key}.jpg").resize((338, 190)), ((i % 4) * 338 + 10, 490 + (i // 4) * 195))
    sheet.save(OUT / "overview.jpg", quality=88)
    md = ["# Curion thumbnails", "", "Vertical 1080x1920 (Shorts, recommended 9:16) and landscape 1280x720 (search / channel page).", "",
          "| file | video | YouTube | hook |", "|---|---|---|---|"]
    for key, title, vid, hook in rows:
        md.append(f"| {key}.jpg | {title} | https://youtube.com/shorts/{vid} | {hook} |")
    (OUT / "README.md").write_text("\n".join(md) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
