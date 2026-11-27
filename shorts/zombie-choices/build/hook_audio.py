"""Part-2 hook test soundtrack (2.7 s): door bangs on each slam (frames 1, 22, 44, 63), chain rattle, snarl, voice, pulse."""
import json, os
import numpy as np, soundfile as sf
SR, DUR = 48000, 81 / 30
N = int(SR * DUR)
rng = np.random.default_rng(5)
def ta(n): return np.arange(n) / SR
def place(buf, s, at, g=1.0):
    i = int(at * SR); j = min(N, i + len(s))
    if j > i: buf[i:j] += np.asarray(s)[: j - i] * g
def lp(x, c):
    a = 1 - np.exp(-2 * np.pi * np.broadcast_to(np.asarray(c, float), x.shape) / SR); y = np.empty_like(x); acc = 0.0
    for i in range(len(x)): acc += a[i] * (x[i] - acc); y[i] = acc
    return y
def hp(x, c): return x - lp(x, c)
def thump(f0, d, g=1.0):
    tt = ta(int(d * SR)); return np.sin(2 * np.pi * np.cumsum(f0 * (1 + 2 * np.exp(-tt * 35))) / SR) * np.exp(-tt * 7) * g
def bang(g=1.0):
    n = int(0.6 * SR); tt = ta(n)
    body = thump(62, 0.6, 1.0)
    crack = hp(rng.standard_normal(n), 1800) * np.exp(-tt * 55) * 0.9
    wood = lp(rng.standard_normal(n), 900) * np.exp(-tt * 18) * 0.7
    return (body + crack + wood) * g
def rattle(d=0.45):
    n = int(d * SR); s = np.zeros(n)
    for k in range(9):
        t0 = int(rng.uniform(0, d * 0.8) * SR); m = int(0.04 * SR)
        tt = ta(m); s[t0:t0 + m] += (np.sin(2 * np.pi * rng.uniform(2800, 4600) * tt) + 0.5 * np.sin(2 * np.pi * rng.uniform(5200, 7200) * tt)) * np.exp(-tt * 90)
    return s
def snarl(d):
    n = int(d * SR); tt = ta(n)
    s = lp(rng.standard_normal(n), 650) * (0.6 + 0.4 * np.sin(2 * np.pi * 29 * tt)) + 0.35 * np.sin(2 * np.pi * np.cumsum(88 + 30 * np.sin(2 * np.pi * 2.5 * tt)) / SR)
    return s * np.sin(np.pi * tt / d) ** 0.6 / np.abs(s).max()
fx, vo, mus = np.zeros(N), np.zeros(N), np.zeros(N)
a, sr = sf.read("audio/vo_0.wav"); a = np.interp(np.linspace(0, len(a) - 1, int(len(a) * SR / sr)), np.arange(len(a)), a)
place(vo, a / np.abs(a).max() * 0.9, 0.0)
for f, g in ((1, 1.2), (22, 0.9), (44, 0.8), (63, 0.75)):
    place(fx, bang(g), (f - 1) / 30); place(fx, rattle(), (f - 1) / 30 + 0.02, 0.35)
place(fx, snarl(1.2), 0.08, 0.5); place(fx, snarl(0.9), 1.6, 0.35)
n = int(0.45 * SR); w = lp(rng.standard_normal(n), np.geomspace(600, 5000, n)) * np.sin(np.linspace(0, np.pi, n)) ** 1.5
place(fx, w / np.abs(w).max() * 0.6, 39 / 30 - 0.2)
for k in range(int(DUR * 2) + 1): place(mus, thump(48, 0.35, 0.9), k * 0.5)
for k in range(int(DUR * 4) + 1):
    tt = ta(int(0.2 * SR)); b = np.sign(np.sin(2 * np.pi * 55 * tt)) * np.exp(-tt * 14); place(mus, lp(b, 400), k * 0.25, 0.35)
def norm(x, p): return x / max(1e-6, np.abs(x).max()) * p
vo, fx, mus = norm(vo, 0.9), norm(fx, 0.65), norm(mus, 0.3)
duck = 1 - 0.6 * np.clip(lp((np.abs(vo) > 0.02).astype(float), 8) * 3, 0, 1)
mix = vo + fx * (0.6 + 0.4 * duck) + mus * duck
mix = np.tanh(mix * 1.2) / np.tanh(1.2); mix = mix / np.abs(mix).max() * 0.89
sf.write("audio/hook_mix.wav", np.stack([mix, mix], 1).astype(np.float32), SR)
print("ok")
