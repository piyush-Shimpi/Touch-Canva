"""Part-3 soundtrack (855 frames = 28.5 s, seamless loop) -> audio/mix.wav, audio/vo_at.json"""
import json
import numpy as np, soundfile as sf
SR, DUR = 48000, 855 / 30
N = int(SR * DUR)
rng = np.random.default_rng(21)
VO_AT = [0.05, 3.5, 6.95, 10.35, 13.55, 16.3, 19.8, 21.75, 23.9, 25.35]
def T(f): return (f - 1) / 30
def ta(n): return np.arange(n) / SR
def place(buf, s, at, g=1.0):
    s = np.asarray(s); i = int(at * SR) % N
    for k in range(len(s)):  # chunked circular write
        pass
    j = i + len(s)
    if j <= N: buf[i:j] += s * g
    else: buf[i:] += s[:N - i] * g; buf[:j - N] += s[N - i:] * g
def lp(x, c):
    a = 1 - np.exp(-2 * np.pi * np.broadcast_to(np.asarray(c, float), x.shape) / SR); y = np.empty_like(x); acc = 0.0
    for i in range(len(x)): acc += a[i] * (x[i] - acc); y[i] = acc
    return y
def hp(x, c): return x - lp(x, c)
def env(n, att, dec): tt = ta(n); return np.minimum(1, tt / att) * np.exp(-tt * dec)
def noise(d): return rng.standard_normal(int(d * SR))
def scream(d):
    n = int(d * SR); tt = ta(n)
    f = 210 + 90 * np.sin(2 * np.pi * 3.1 * tt) * np.exp(-tt * 1.5)
    tone = np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * 0.4 + np.sin(2 * np.pi * np.cumsum(f * 2.01) / SR) * 0.3
    rasp = hp(lp(rng.standard_normal(n), 3200), 500) * (0.7 + 0.3 * np.sin(2 * np.pi * 37 * tt))
    return lp(tone + rasp, 2600) * np.minimum(1, tt / 0.03) * np.exp(-np.maximum(0, tt - 0.25) * 2.2)
def growl(d):
    n = int(d * SR); tt = ta(n)
    s = lp(rng.standard_normal(n), 600) * (0.6 + 0.4 * np.sin(2 * np.pi * 27 * tt)) + 0.35 * np.sin(2 * np.pi * np.cumsum(85 + 25 * np.sin(2 * np.pi * 2.3 * tt)) / SR)
    return s * np.sin(np.pi * tt / d) ** 0.6 / np.abs(s).max()
def whoosh(d=0.35, f0=500, f1=6000):
    n = int(d * SR); w = lp(rng.standard_normal(n), np.geomspace(f0, f1, n)) * np.sin(np.linspace(0, np.pi, n)) ** 1.5
    return w / np.abs(w).max()
def thump(f0, d, g=1.0):
    tt = ta(int(d * SR)); return np.sin(2 * np.pi * np.cumsum(f0 * (1 + 2 * np.exp(-tt * 35))) / SR) * np.exp(-tt * 7) * g
def heartbeat():
    b = thump(55, 0.3); s = np.zeros(int(0.6 * SR)); s[:len(b)] += b; s[int(0.22 * SR):int(0.22 * SR) + len(b)] += b * 0.7
    return s
def brrr():
    n = int(0.75 * SR); tt = ta(n)
    trill = np.sin(2 * np.pi * np.cumsum(150 + 20 * np.sin(2 * np.pi * 4 * tt)) / SR) * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 28 * tt)))
    chatter = np.zeros(n)
    for k in range(14):
        i = int(k * 0.05 * SR); m = int(0.012 * SR); chatter[i:i + m] += hp(rng.standard_normal(m), 2500) * np.exp(-ta(m) * 300)
    return lp(trill, 1800) * np.sin(np.pi * tt / 0.75) ** 0.5 + chatter * 0.6
def chunk():
    n = int(0.22 * SR); return (lp(rng.standard_normal(n), 900) * 0.8 + hp(rng.standard_normal(n), 3000) * 0.3) * env(n, 0.002, 22) + np.pad(thump(90, 0.2, 0.6), (0, n - int(0.2 * SR)))
def splash(d=0.3):
    n = int(d * SR); return hp(lp(rng.standard_normal(n), 5000), 400) * env(n, 0.004, 9)
def bubbles(d):
    n = int(d * SR); s = np.zeros(n)
    for k in range(int(d * 14)):
        i = int(rng.uniform(0, d - 0.06) * SR); m = int(0.05 * SR); f = rng.uniform(500, 1400)
        s[i:i + m] += np.sin(2 * np.pi * np.cumsum(np.linspace(f, f * 1.8, m)) / SR) * np.exp(-ta(m) * 60)
    return s
def crackle(d):
    n = int(d * SR); s = lp(rng.standard_normal(n), 900) * 0.15
    for k in range(int(d * 18)):
        i = int(rng.uniform(0, d - 0.01) * SR); m = int(0.006 * SR); s[i:i + m] += hp(rng.standard_normal(m), 2000) * rng.uniform(0.3, 1.0)
    return s
def crickets(d):
    n = int(d * SR); tt = ta(n); g = (np.sin(2 * np.pi * 30 * tt) > 0.2) * (np.sin(2 * np.pi * 1.6 * tt) > 0)
    return np.sin(2 * np.pi * 4300 * tt) * g * 0.5
def puff():
    n = int(0.25 * SR); return lp(rng.standard_normal(n), 1200) * env(n, 0.01, 14)
def ring():
    n = int(0.6 * SR); tt = ta(n); return np.sin(2 * np.pi * (180 + 60 * tt) * tt) * env(n, 0.01, 5)

fx, vo, bed, mus = np.zeros(N), np.zeros(N), np.zeros(N), np.zeros(N)
meta = json.load(open("audio/vo.json"))
for m, at in zip(meta, VO_AT):
    a, sr = sf.read(f"audio/vo_{m['i']}.wav"); a = np.interp(np.linspace(0, len(a) - 1, int(len(a) * SR / sr)), np.arange(len(a)), a)
    place(vo, a / np.abs(a).max() * 0.9, at)
# --- shot SFX
place(fx, scream(1.3), 0.0, 1.0)                                   # hook hit (loop seam)
place(fx, whoosh(), T(46) - 0.18, 0.5)
place(fx, growl(1.2), T(104), 0.6)                                  # zombie listening
for i in range(4): place(fx, ring(), T(151 + i * 12), 0.35)          # sound rings
place(fx, splash(0.5), T(206), 0.6); place(fx, brrr(), T(222), 0.9)  # cold pool + BRRR
for k in range(4): place(fx, chunk(), T(268) + k * 0.42, 0.8)       # digging
for k in range(6): place(fx, splash(0.18), T(318) + k * 0.47, 0.45) # stream steps
place(fx, splash(0.4), T(405), 0.5); place(fx, bubbles(1.4), T(408), 0.5)
place(fx, splash(0.5), T(470), 0.6)                                 # climbs out
place(fx, crackle(5.4), T(491), 0.5)
for k in range(5): place(fx, puff(), T(548) + k * 0.3, 0.4)
place(fx, crickets(2.1), T(591), 0.18)
place(fx, growl(1.1), T(656), 0.7)
for k in range(3): place(mus, heartbeat(), T(660) + k * 0.6, 0.9)
place(fx, scream(1.0), T(690), 1.0)                                 # PEAK
place(fx, whoosh(0.5, 3000, 300), T(713) - 0.1, 0.3)
for k in range(5): place(fx, thump(70, 0.15, 0.4), T(716) + k * 0.28)
# riser into the loop seam
n = int(2.2 * SR); r = lp(rng.standard_normal(n), np.geomspace(300, 7000, n)) * np.linspace(0, 1, n) ** 2
place(fx, r / np.abs(r).max(), DUR - 2.2, 0.35)
# --- waterfall bed: muffled in the room shots, quiet at night, fading as it shrinks
t = ta(N)
roar = lp(rng.standard_normal(N), 1800) * 0.7 + hp(lp(rng.standard_normal(N), 7000), 900) * 0.35
muff = lp(roar, 650) * 1.4
inroom = ((t >= T(46)) & (t < T(104))) | ((t >= T(263)) & (t < T(311))) | ((t >= T(491)) & (t < T(541))) | (t >= T(806))
g = np.ones(N); g[(t >= T(757))] = np.clip(1 - (t[(t >= T(757))] - T(757)) / 3.0, 0.35, 1)
bed[:] = np.where(inroom, muff, roar) * g
# --- music: low pulse + drone (seamless: 57 beats of 0.5 s)
for k in range(57): place(mus, thump(46, 0.35, 0.7), k * 0.5)
mus += (np.sin(2 * np.pi * 41 * t) * 0.4 + np.sin(2 * np.pi * 61.5 * t) * 0.2)
pk = (t > T(686)) & (t < T(700)); mus[pk] *= 0.15                   # drop right before the scream
def norm(x, p): return x / max(1e-6, np.abs(x).max()) * p
vo, fx, bed, mus = norm(vo, 0.9), norm(fx, 0.75), norm(bed, 0.26), norm(mus, 0.28)
duck = 1 - 0.55 * np.clip(lp((np.abs(vo) > 0.02).astype(float), 8) * 3, 0, 1)
mix = vo + fx * (0.6 + 0.4 * duck) + (bed + mus) * duck
mix = np.tanh(mix * 1.2) / np.tanh(1.2); mix = mix / np.abs(mix).max() * 0.89
sf.write("audio/mix.wav", np.stack([mix, mix], 1).astype(np.float32), SR)
json.dump(VO_AT, open("audio/vo_at.json", "w"))
print("ok", DUR)
