"""Hook test soundtrack (3.3 s): voice line 1 + snap/bass on frame 0 + footsteps + snarl + whoosh + 120 BPM pulse."""
import numpy as np, soundfile as sf, os
SR, DUR = 48000, 99 / 30
N = int(SR * DUR)
rng = np.random.default_rng(7)
t = np.arange(N) / SR
def ta(n): return np.arange(n) / SR
def place(buf, s, at, g=1.0):
    i = int(at * SR); j = min(N, i + len(s))
    if j > i: buf[i:j] += s[: j - i] * g
def lp(x, c):
    a = 1 - np.exp(-2 * np.pi * np.broadcast_to(np.asarray(c, float), x.shape) / SR); y = np.empty_like(x); acc = 0.0
    for i in range(len(x)): acc += a[i] * (x[i] - acc); y[i] = acc
    return y
def hp(x, c): return x - lp(x, c)
def thump(f0, d, g=1.0):
    tt = ta(int(d * SR)); return np.sin(2 * np.pi * np.cumsum(f0 * (1 + 2 * np.exp(-tt * 35))) / SR) * np.exp(-tt * 7) * g
def whoosh(d, f0, f1, g=1.0):
    n = int(d * SR); w = lp(rng.standard_normal(n), np.geomspace(f0, f1, n)) * np.sin(np.linspace(0, np.pi, n)) ** 1.5
    return w / np.abs(w).max() * g
fx = np.zeros(N); mus = np.zeros(N); vo = np.zeros(N)
a, sr = sf.read("audio/hook_vo_1.0.wav"); a = np.interp(np.linspace(0, len(a) - 1, int(len(a) * SR / sr)), np.arange(len(a)), a)
place(vo, a / np.abs(a).max() * 0.9, 0.0)
# frame 0: jaw/hand SNAP (two sharp clicks 40 ms apart) + sub hit
n = int(0.03 * SR); click = hp(rng.standard_normal(n), 2500) * np.exp(-ta(n) * 300)
place(fx, click, 0.0, 1.0); place(fx, click, 0.04, 0.8); place(fx, thump(55, 0.8), 0.0, 1.1)
# footsteps (Remy, ~2.9 steps/s) + heavier zombie steps
for k in range(10):
    st = lp(rng.standard_normal(int(0.06 * SR)), 900) * np.exp(-ta(int(0.06 * SR)) * 60)
    place(fx, st, 0.05 + k * 0.35, 0.5)
    place(fx, st, 0.22 + k * 0.38, 0.35)
# zombie snarl: growly AM noise, 0.1-1.2 s
n = int(1.1 * SR); tt = ta(n)
snarl = lp(rng.standard_normal(n), 700) * (0.6 + 0.4 * np.sin(2 * np.pi * 31 * tt)) * np.sin(np.pi * tt / 1.1) ** 0.6
snarl += 0.3 * np.sin(2 * np.pi * np.cumsum(95 + 25 * np.sin(2 * np.pi * 3 * tt)) / SR) * np.sin(np.pi * tt / 1.1)
place(fx, snarl / np.abs(snarl).max(), 0.1, 0.45)
place(fx, whoosh(0.45, 600, 5000, 0.7), 39 / 30 - 0.2)        # cut to the look-back CU
# 120 BPM tense pulse: kick on beats, low saw-ish bass on 8ths
for k in range(int(DUR * 2) + 1):
    place(mus, thump(48, 0.35, 0.9), k * 0.5)
for k in range(int(DUR * 4) + 1):
    tt = ta(int(0.2 * SR)); b = np.sign(np.sin(2 * np.pi * 55 * tt)) * np.exp(-tt * 14)
    place(mus, lp(b, 400), k * 0.25, 0.35)
def norm(x, p): return x / max(1e-6, np.abs(x).max()) * p
vo, fx, mus = norm(vo, 0.9), norm(fx, 0.6), norm(mus, 0.35)
duck = 1 - 0.6 * np.clip(lp((np.abs(vo) > 0.02).astype(float), 8) * 3, 0, 1)
mix = vo + fx * (0.6 + 0.4 * duck) + mus * duck
mix = np.tanh(mix * 1.2) / np.tanh(1.2)
mix = mix / np.abs(mix).max() * 0.89
sf.write("audio/hook_mix.wav", np.stack([mix, mix], 1).astype(np.float32), SR)
print("ok", mix.shape)
