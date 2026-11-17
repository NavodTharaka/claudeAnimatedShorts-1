"""The Stars Speak: synthesized score + SFX, mixed with the narration (voice unchanged, music +3 dB, SFX -6 dB
against the standard bed). Every cue is placed on the picture's frame numbers (see src/videos/stars/story.ts).
Output: audio/out/mix.wav (48 kHz stereo, exactly TOTAL/30 s), stems and cues.md."""
import json, os, sys
import numpy as np
from scipy import signal as sg
from scipy.io import wavfile

SR = 48000
FPS = 30
TOTAL = 2250
DUR = TOTAL / FPS
N = int(round(DUR * SR))
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(HERE, "out")
os.makedirs(OUT, exist_ok=True)
rs = np.random.RandomState(7)
f2t = lambda f: f / FPS


def tvec(d): return np.arange(int(d * SR)) / SR
def db(x): return 10 ** (x / 20)
def lp(x, f, o=2): return sg.sosfilt(sg.butter(o, f, "low", fs=SR, output="sos"), x)
def hp(x, f, o=2): return sg.sosfilt(sg.butter(o, f, "high", fs=SR, output="sos"), x)
def bp(x, a, b, o=2): return sg.sosfilt(sg.butter(o, [a, b], "band", fs=SR, output="sos"), x)
def noise(d): return rs.randn(int(d * SR))
def env_ad(n, a, d, p=2.0):
    t = np.arange(n) / SR
    e = np.minimum(t / max(a, 1e-4), 1.0) * np.exp(-t / d)
    return e
def fade(x, fi=0.005, fo=0.02):
    n = len(x); a = int(fi * SR); b = int(fo * SR)
    if a: x[:a] *= np.linspace(0, 1, a)
    if b: x[-b:] *= np.linspace(1, 0, b)
    return x


class Bus:
    def __init__(self): self.L = np.zeros(N); self.R = np.zeros(N)
    def add(self, x, t, g=1.0, pan=0.0):
        i = int(round(t * SR))
        if i >= N or i + len(x) <= 0: return
        a = max(0, -i); b = min(len(x), N - i)
        th = (pan + 1) * np.pi / 4
        self.L[i + a:i + b] += x[a:b] * g * np.cos(th)
        self.R[i + a:i + b] += x[a:b] * g * np.sin(th)
    def st(self): return np.stack([self.L, self.R])


# ---------------- instruments ----------------
def mtof(m): return 440.0 * 2 ** ((m - 69) / 12)

def pluck(f, d=1.2, vel=0.7, bright=0.5):
    """Karplus-Strong string (oud / lute)"""
    n = int(d * SR); L = max(2, int(SR / f))
    buf = rs.uniform(-1, 1, L) * vel
    buf = lp(buf, 2500 + 6000 * bright, 1)
    out = np.zeros(n); k = 0
    damp = 0.9965 - 0.0008 * (f / 400)
    for i in range(n):
        out[i] = buf[k]
        buf[k] = damp * 0.5 * (buf[k] + buf[(k + 1) % L])
        k = (k + 1) % L
    return fade(out, 0.001, 0.05)

def bell(f, d=2.5, vel=0.5):
    t = tvec(d); x = np.zeros_like(t)
    for r, a, dc in [(1, 1, 1.0), (2.76, 0.5, 0.6), (5.4, 0.28, 0.35), (8.93, 0.16, 0.2)]:
        x += a * np.sin(2 * np.pi * f * r * t + rs.rand() * 6) * np.exp(-t / (d * 0.5 * dc))
    return fade(x * vel * 0.4, 0.002, 0.05)

def drum(f=70, d=0.5, vel=0.8):
    t = tvec(d); fr = f * (1 + 1.4 * np.exp(-t / 0.035))
    x = np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-t / 0.16)
    x += 0.25 * lp(noise(d), 600, 2) * np.exp(-t / 0.03)
    return fade(x * vel, 0.001, 0.03)

def slap(d=0.18, vel=0.6):
    x = bp(noise(d), 900, 3800) * np.exp(-tvec(d) / 0.05)
    return fade(x * vel * 1.6, 0.0005, 0.02)

def pad(freqs, d, vel=0.4, warm=900, att=1.0, rel=1.2, det=0.004):
    t = tvec(d); x = np.zeros_like(t)
    for f in freqs:
        for dt in (-det, 0, det):
            ph = rs.rand() * 6.28
            ff = f * (1 + dt)
            x += sg.sawtooth(2 * np.pi * ff * t + ph, 0.5) * 0.18
    x = lp(x, warm, 2)
    e = np.minimum(t / att, 1) * np.minimum((d - t) / rel, 1).clip(0, 1)
    return x * e * vel

def brass(f, d=0.5, vel=0.7, slide=0.0):
    t = tvec(d)
    ff = f * (1 + slide * (t / d))
    ph = 2 * np.pi * np.cumsum(ff) / SR
    x = sg.sawtooth(ph) * 0.5 + np.sin(ph) * 0.5
    x = lp(x, 1600, 2) * 0.7 + lp(x, 600, 2) * 0.5
    return fade(x * np.minimum(t / 0.05, 1) * vel, 0.002, 0.06)

def reverb(x, rt=1.6, wet=0.25, seed=3):
    r = np.random.RandomState(seed)
    n = int(rt * SR); t = np.arange(n) / SR
    ir = r.randn(n) * np.exp(-t * 6.9 / rt); ir = lp(ir, 5000, 1); ir[0] = 0
    ir /= np.sqrt(np.sum(ir ** 2)) + 1e-9
    return x + wet * sg.fftconvolve(x, ir)[:len(x)]


# ---------------- score ----------------
cues = []
def cue(t, what): cues.append((t, what))

mus = Bus()
# D Phrygian dominant: D Eb F# G A Bb C
D3, Eb3, Fs3, G3, A3, Bb3, C4, D4 = 50, 51, 54, 55, 57, 58, 60, 62
SC = [50, 51, 54, 55, 57, 58, 60, 62, 63, 66, 67, 69, 70, 72, 74]
def lute(t, m, vel=0.6, g=0.5, pan=0.0, d=1.2, bright=0.5):
    mus.add(pluck(mtof(m), d, vel, bright), t, g, pan)

# 0-6.4 hook: low drone + heartbeat
mus.add(pad([mtof(38), mtof(45)], 7.4, 0.55, 500, 1.2, 1.5), 0.0, 0.8)
for k in range(5): mus.add(drum(58, 0.5, 0.7), 2.4 + k * 0.84, 0.7)
cue(0.0, "drone + heartbeat (hook)")
# 6.4-12.9 city: lute theme over frame drum
th = [(0, 62), (0.5, 63), (1.0, 66), (1.5, 67), (2.0, 69), (2.5, 67), (3.0, 66), (3.5, 63), (4.0, 62), (4.5, 63), (5.0, 66), (5.5, 69), (6.0, 70), (6.5, 69)]
for dt, m in th: lute(6.4 + dt * 0.92, m + 12 * (m < 60), 0.7, 0.55, -0.2)
for k in range(14):
    mus.add(drum(75, 0.4, 0.7 if k % 2 == 0 else 0.45), 6.4 + k * 0.46, 0.6)
    if k % 2: mus.add(slap(0.15, 0.5), 6.4 + k * 0.46, 0.3, 0.3)
mus.add(pad([mtof(38), mtof(45), mtof(50)], 6.8, 0.45, 800, 0.8, 1.2), 6.2, 0.55)
cue(6.4, "city theme: lute + frame drum")
# 12.9-19.6 night: sparse bells, drone
mus.add(pad([mtof(38), mtof(41), mtof(45)], 7.6, 0.5, 600, 1.5, 1.5), 12.7, 0.6)
for k, m in enumerate([74, 70, 69, 67, 69, 66, 62, 63]): mus.add(bell(mtof(m), 3.0, 0.5), 13.2 + k * 0.8, 0.45, (-1) ** k * 0.4)
cue(12.9, "night climb: bells + drone")
# 19.6-34.5 eclipse tension: tremolo cluster rising + heartbeat accelerating
t0, t1 = 19.6, 34.4
cl = pad([mtof(38), mtof(51), mtof(54), mtof(57)], t1 - t0 + 1.0, 0.7, 1400, 3.0, 0.8, 0.012)
trem = 0.65 + 0.35 * np.sin(2 * np.pi * np.linspace(5, 9, len(cl)) * tvec(len(cl) / SR))
mus.add(cl * trem, t0, 0.75)
tt = t0 + 0.2; gap = 1.1
while tt < 34.2:
    mus.add(drum(52, 0.45, 0.8), tt, 0.8); mus.add(drum(52, 0.45, 0.55), tt + 0.22, 0.6)
    tt += gap; gap = max(0.46, gap * 0.93)
cue(19.6, "eclipse tension: tremolo cluster + accelerating heartbeat")
mus.add(drum(45, 1.2, 1.0), 28.3, 1.1); mus.add(brass(mtof(38), 1.4, 0.9), 28.3, 0.55)
cue(28.3, "'danger to the king' stab")
# 30.3-40.6 court: slow low march, silence at 34.5
for k in range(8): mus.add(drum(60, 0.5, 0.8 if k % 2 == 0 else 0.55), 30.4 + k * 0.52, 0.8)
cue(34.5, "music drops out on 'The court goes silent'")
mus.add(pad([mtof(38), mtof(45)], 6.2, 0.4, 500, 1.5, 1.0), 36.0, 0.5)
mus.add(pad([mtof(38), mtof(45)], 3.0, 0.3, 450, 1.2, 1.0), 33.9, 0.45)  # gap fill
mus.add(pad([mtof(45), mtof(50)], 1.8, 0.3, 700, 0.4, 0.8), 41.9, 0.45)  # gap fill under the 42.2 breath
for k, m in enumerate([50, 51, 54, 51, 50]): lute(36.9 + k * 0.7, m, 0.55, 0.45, 0.2)
# 40.6 Luckily: bright major lute; 42.6 Unluckily: tuba wah-wah
for k, m in enumerate([62, 66, 69, 74]): lute(40.75 + k * 0.25, m, 0.7, 0.5, -0.2, 1.4, 0.8)
cue(40.6, "'Luckily': relieved lute arpeggio")
mus.add(brass(mtof(46), 0.5, 0.8, -0.0), 43.4, 0.6); mus.add(brass(mtof(45), 0.5, 0.8), 43.9, 0.6); mus.add(brass(mtof(44), 0.5, 0.8), 44.4, 0.6)
mus.add(brass(mtof(40), 1.2, 0.85, -0.18), 44.9, 0.7)
cue(43.4, "'Unluckily': sad tuba wah-wah slide down")
# 45.3-50 stand-in: comic oompah
for k in range(10):
    t = 45.5 + k * 0.44
    mus.add(brass(mtof(38 if k % 2 == 0 else 45), 0.28, 0.75), t, 0.5); mus.add(slap(0.1, 0.4), t + 0.22, 0.25)
for k, m in enumerate([74, 69, 70, 74, 69, 66, 62, 69]): lute(45.5 + k * 0.44, m, 0.7, 0.5, 0.25, 0.7, 0.8)
cue(45.3, "stand-in: comic oompah")
# 50-64.5 clever part: pizzicato + marimba-ish
mus.add(bell(mtof(86), 2.5, 0.8), 50.35, 0.5)
cue(50.4, "lightbulb chime")
mus.add(pad([mtof(50), mtof(57), mtof(62)], 14.5, 0.35, 900, 1.5, 1.5), 50.4, 0.5)
seq = [62, 66, 69, 66, 62, 69, 74, 69]
for k in range(30):
    m = seq[k % 8] + (12 if (k // 8) % 2 else 0)
    lute(51.2 + k * 0.42, m - 12 + 12, 0.5, 0.35, (-1) ** k * 0.3, 0.5, 0.9)
for k in range(30): mus.add(slap(0.08, 0.3), 51.2 + k * 0.42 + 0.21, 0.18, 0.4)
cue(51.2, "scholarly pizzicato bounce")
# 64.5-72.8 warm resolve
mus.add(pad([mtof(50), mtof(57), mtof(66), mtof(69)], 8.5, 0.5, 1000, 1.2, 1.5), 64.4, 0.6)
for k, m in enumerate([74, 73, 69, 66, 69, 73, 74, 78]): lute(64.7 + k * 0.62, m, 0.65, 0.5, -0.25, 1.4, 0.7)
cue(64.5, "warm resolve")
# 72.8-75 button: cheeky pluck + low drone + final sting
for k, m in enumerate([74, 73, 74, 69]): lute(73.1 + k * 0.28, m, 0.6, 0.45, 0.1, 0.8, 0.7)
mus.add(brass(mtof(38), 1.4, 0.9), 74.2, 0.6); mus.add(drum(60, 0.8, 1.0), 74.2, 0.8)
cue(73.1, "closing button")

# ---------------- SFX ----------------
sfx = Bus()
def whoosh(t, d=0.5, g=0.5, pan=0.0, up=True):
    n = noise(d); tt_ = tvec(d)
    f = np.linspace(300, 3500, len(n)) if up else np.linspace(3500, 300, len(n))
    out = np.zeros_like(n); step = 512
    for i in range(0, len(n) - step, step):
        out[i:i + step] = bp(n[i:i + step + 0], max(200, f[i] * 0.6), min(f[i] * 1.5, 18000), 2)[:step] if False else n[i:i + step]
    out = bp(n, 400, 4000) * np.sin(np.pi * np.minimum(tt_ / d, 1)) ** 2
    sfx.add(fade(out * 0.9, 0.01, 0.05), t, g, pan)
def thump(t, f=60, g=0.9, d=0.6): sfx.add(drum(f, d, 1.0), t, g)
def step(t, g=0.3, pan=0.0, hard=0.6):
    x = lp(noise(0.12), 1400) * np.exp(-tvec(0.12) / 0.018) * hard + 0.3 * np.sin(2 * np.pi * 120 * tvec(0.12)) * np.exp(-tvec(0.12) / 0.03)
    sfx.add(fade(x, 0.0005, 0.02), t, g, pan)
def clay(t, g=0.4, pan=0.0):
    d = 0.1; x = bp(noise(d), 1200, 3200) * np.exp(-tvec(d) / 0.012) + 0.4 * np.sin(2 * np.pi * 260 * tvec(d)) * np.exp(-tvec(d) / 0.02)
    sfx.add(fade(x, 0.0003, 0.01), t, g, pan)
def scratch(t, d=0.35, g=0.25, pan=0.0):
    n = noise(d); x = hp(n, 2500) * (0.5 + 0.5 * np.sin(2 * np.pi * 22 * tvec(d))) * np.sin(np.pi * np.minimum(tvec(d) / d, 1))
    sfx.add(x * 0.5, t, g, pan)
def gasp(t, d=0.4, g=0.3, pan=0.0):
    x = bp(noise(d), 500, 2500) * np.sin(np.pi * np.minimum(tvec(d) / d, 1)) ** 1.5
    sfx.add(x, t, g, pan)
def twinkle(t, base=2000, n=5, g=0.25):
    for k in range(n): sfx.add(bell(base * (1 + 0.25 * k), 0.8, 0.5), t + k * 0.06, g, (-1) ** k * 0.5)
def pop(t, f=500, g=0.4):
    x = np.sin(2 * np.pi * np.cumsum(f * (1 + 2.5 * np.exp(-tvec(0.12) / 0.02))) / SR) * np.exp(-tvec(0.12) / 0.03)
    sfx.add(x, t, g)
def creak(t, d=0.8, g=0.3, f0=180, f1=90, pan=0.0):
    tt_ = tvec(d); f = np.linspace(f0, f1, len(tt_)) * (1 + 0.04 * np.sin(2 * np.pi * 9 * tt_))
    x = sg.sawtooth(2 * np.pi * np.cumsum(f) / SR) * 0.4 * np.sin(np.pi * np.minimum(tt_ / d, 1))
    sfx.add(lp(x, 900, 2), t, g, pan)
def murmur(t, d, g=0.12):
    x = bp(noise(d), 200, 1400) * (0.6 + 0.4 * np.sin(2 * np.pi * 3.1 * tvec(d) + rs.rand() * 6)) * np.minimum(tvec(d) / 0.5, 1) * np.minimum((d - tvec(d)) / 0.5, 1).clip(0, 1)
    sfx.add(x, t, g)
def cheer(t, d, g=0.2):
    x = bp(noise(d), 600, 3800) * (0.7 + 0.3 * np.sin(2 * np.pi * 5.2 * tvec(d))) * np.minimum(tvec(d) / 0.3, 1) * np.minimum((d - tvec(d)) / 0.4, 1).clip(0, 1)
    sfx.add(x, t, g)
def crickets(t, d, g=0.06):
    base = hp(noise(d), 3800) * 0
    x = np.zeros(int(d * SR)); tt_ = tvec(d)
    for fr_, ph in [(4300, 0), (4700, 0.4), (5100, 0.7)]:
        gate = (np.sin(2 * np.pi * 7 * tt_ + ph * 6) > 0.3).astype(float)
        x += np.sin(2 * np.pi * fr_ * tt_) * gate * 0.3
    sfx.add(x * np.minimum(tt_ / 1.0, 1) * np.minimum((d - tt_) / 1.0, 1).clip(0, 1), t, g)
def rumble(t, d, g=0.3, pan=0.0, pitch=70):
    x = lp(noise(d), 160, 2) * (1 + 0.5 * np.sin(2 * np.pi * 6 * tvec(d)))
    x += 0.4 * lp(noise(d), 700, 1) * (0.5 + 0.5 * np.sin(2 * np.pi * 11 * tvec(d)))
    sfx.add(x * np.minimum(tvec(d) / 0.8, 1) * np.minimum((d - tvec(d)) / 0.6, 1).clip(0, 1), t, g, pan)
def ding(t, g=0.35): sfx.add(bell(1760, 2.2, 0.8), t, g); sfx.add(bell(2349, 1.8, 0.5), t + 0.03, g * 0.7)
def sparkle_up(t, d=0.9, g=0.25):
    for k in range(8): sfx.add(bell(900 * 2 ** (k / 4), 0.6, 0.5), t + k * d / 8, g, (-1) ** k * 0.5)
def impact(t, g=0.8):
    thump(t, 48, g, 1.2); whoosh(t - 0.05, 0.3, 0.3, 0, True)

F = lambda f: f / FPS
# hook flash
whoosh(F(119) - 0.35, 0.45, 0.4); impact(F(119), 0.9); sfx.add(bell(1400, 2.0, 0.6), F(119), 0.3)
# cuts and place changes (whooshes)
for f in (191, 388, 970, 1502, 1930, 2085): whoosh(F(f) - 0.3, 0.6, 0.3, 0, True)
# city murmur + cheer 6.4-12.9
# night climb steps 388-528
for k in range(15): step(F(388) + k * 0.34 + 0.2, 0.22, -0.2, 0.5)
# eclipse bite 19.75
sparkle_up(19.5, 1.2, 0.22); creak(19.7, 1.4, 0.25, 220, 70)
# tablets 22.4, 23.7 ; sit 24.9
for t in (22.45, 22.7, 22.95): clay(t, 0.4, 0.2); scratch(22.5, 0.3, 0.2, 0.2)
for t in (23.75, 24.0): clay(t, 0.4, -0.2)
sfx.add(lp(noise(0.5), 500) * np.exp(-tvec(0.5) / 0.12), 24.95, 0.5)  # sit thump
gasp(25.3, 0.5, 0.2)
# omen, tablet CU
impact(28.3, 1.0); creak(28.5, 1.8, 0.35, 260, 60); sfx.add(bell(220, 3.0, 0.9), 28.3, 0.35)
# creaking omen sparkles 28.3-30
for k in range(2): creak(28.8 + k * 0.45, 0.4, 0.15, 400, 200, (-1) ** k * 0.5)
# descent + court
for k in range(12): step(F(909) + k * 0.4 + 0.1, 0.22, 0.1, 0.5)
for k in range(8): step(F(970) + k * 0.5 + 0.1, 0.22, -0.3, 0.55)
# 34.5 silence: nothing but a faint air; 35.8 king creak lean
creak(35.8, 0.8, 0.28, 150, 100)
# swallows (gulp) 37.0
clay(38.2, 0.4); clay(38.55, 0.3)
# Luckily/Unluckily: crown ting, gasp
ding(44.0, 0.3); gasp(44.3, 0.5, 0.35, -0.3); gasp(44.55, 0.4, 0.3, 0.3)
impact(44.0, 0.7); impact(44.55, 0.5)
# stand-in: sparkle stars, cheers
twinkle(46.3, 1800, 6, 0.2); twinkle(48.2, 2200, 5, 0.18)
# clever part pop
pop(51.4, 700, 0.4); sparkle_up(50.3, 0.7, 0.2)
# library: murals pops 56.9..
for m in range(7): pop(F(1706 + m * 10), 400 + 70 * m, 0.45); sfx.add(bell(500 + 90 * m, 0.7, 0.5), F(1706 + m * 10), 0.18)
# bus stop: wheel rumble, arrival ding
rumble(F(1862), 1.8, 0.28, -0.4); clay(F(1895), 0.3); ding(F(1912) + 0.05, 0.35)
for k in range(5): clay(F(1862) + 0.1 + k * 0.33, 0.2, 0.1)
# relief 64.5-69
# writing: stylus scratches 2092..2190, final word clicks
for k in range(5): scratch(F(2095) + k * 0.33, 0.22, 0.22, -0.1)
for k, tw in enumerate([73.02, 73.3, 73.6, 73.85, 74.05]): clay(tw, 0.45)
sfx.add(drum(60, 0.9, 1.0), 74.2, 0.5)
# gulp (sweat) at the very end

# ---------------- voice + mix ----------------
sr, v = wavfile.read(os.path.join(ROOT, "voice", "voice.wav"))
assert sr == SR
v = v.astype(np.float64) / (32768.0 if v.dtype == np.int16 else 1.0)
voice = np.zeros(N); voice[:min(N, len(v))] = v[:N]
words = json.load(open(os.path.join(ROOT, "voice", "words_p.json")))
speech = np.zeros(N)
for w in words:
    a = max(0, int((w["start"] - 0.08) * SR)); b = min(N, int((w["end"] + 0.12) * SR)); speech[a:b] = 1.0
# merge gaps < 0.3 s
k = int(0.3 * SR)
speech = sg.fftconvolve(speech, np.ones(k) / k, mode="same")
speech = (speech > 0.05).astype(float)
sm = sg.fftconvolve(speech, np.hanning(int(0.35 * SR)) / np.hanning(int(0.35 * SR)).sum(), mode="same")
duck = 10 ** ((-10.0 * np.clip(sm, 0, 1)) / 20)

def rms_db(x): return 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-12)
def active_rms(x, mask): return 20 * np.log10(np.sqrt(np.mean((x ** 2)[mask > 0.5])) + 1e-12)
vgain = db(-20.0 - active_rms(voice, speech))        # voice unchanged in character: just normalised to -20 dBFS RMS while speaking
voice_m = voice * vgain
M = mus.st(); S = sfx.st()
M = np.stack([reverb(M[0], 1.8, 0.22, 3), reverb(M[1], 1.8, 0.22, 4)])
for c in (0, 1): M[c] = hp(M[c], 40, 2)
# music: bed -28 dB active RMS +3 dB (standard mix) ; SFX -6 dB
mgain = db(-27.0 + 3.0 - rms_db(M))
sgain = db(-22.0 + 0.0 - rms_db(S) - 6.0 + 6.0) if False else db(-24.0 - rms_db(S))
M = M * mgain * duck
# fade the music: 2 s fade-in, tail out
fin = np.minimum(np.arange(N) / (1.5 * SR), 1); fout = np.minimum((N - np.arange(N)) / (0.6 * SR), 1)
M = M * fin * fout
S = S * sgain * db(-6.0) * db(6.0)
mix = np.stack([voice_m, voice_m]) + M + S
# soft limiter to -1.5 dBFS
peak = np.max(np.abs(mix))
ceil = db(-1.5)
if peak > ceil:
    th = db(-8.0)
    y = np.sign(mix) * np.where(np.abs(mix) > th, th + (ceil - th) * np.tanh((np.abs(mix) - th) / (ceil - th)), np.abs(mix))
    mix = y
mix = np.clip(mix, -1, 1)
def write(name, x):
    wavfile.write(os.path.join(OUT, name), SR, (np.clip(x.T, -1, 1) * 32767).astype(np.int16))
write("mix.wav", mix); write("music.wav", M); write("sfx.wav", S); write("voice_stem.wav", np.stack([voice_m, voice_m]))
with open(os.path.join(OUT, "cues.md"), "w", encoding="utf8") as f:
    f.write("# The Stars Speak: sound cues\n\n")
    for t, w in sorted(cues): f.write(f"- {t:6.2f} s (f{int(t * FPS)}): {w}\n")
print("length", len(mix[0]) / SR, "peak dB", 20 * np.log10(np.max(np.abs(mix))), "music dB", rms_db(M), "sfx dB", rms_db(S))
