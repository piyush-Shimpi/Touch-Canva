"""Hook-test soundtrack (103 frames = 3.43 s): zombie scream hit on frame 0, waterfall roar bed, heartbeat, VO line 0."""
import numpy as np, soundfile as sf
SR, DUR = 48000, 103 / 30
N = int(SR * DUR)
rng = np.random.default_rng(11)
def ta(n): return np.arange(n) / SR
def place(buf, s, at, g=1.0):
    i = int(at * SR); j = min(N, i + len(s))
    if j > i: buf[i:j] += np.asarray(s)[: j - i] * g
def lp(x, c):
    a = 1 - np.exp(-2 * np.pi * np.broadcast_to(np.asarray(c, float), x.shape) / SR); y = np.empty_like(x); acc = 0.0
    for i in range(len(x)): acc += a[i] * (x[i] - acc); y[i] = acc
    return y
def hp(x, c): return x - lp(x, c)
def scream(d):
    n = int(d * SR); tt = ta(n)
    f = 210 + 90 * np.sin(2 * np.pi * 3.1 * tt) * np.exp(-tt * 1.5) + 60 * rng.standard_normal(n).cumsum() / np.sqrt(np.arange(1, n + 1)) * 0.02
    tone = np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * 0.4 + np.sin(2 * np.pi * np.cumsum(f * 2.01) / SR) * 0.3
    rasp = hp(lp(rng.standard_normal(n), 3200), 500) * (0.7 + 0.3 * np.sin(2 * np.pi * 37 * tt))
    env = np.minimum(1, tt / 0.03) * np.exp(-np.maximum(0, tt - 0.25) * 2.2)
    return lp(tone + rasp, 2600) * env
def heartbeat():
    n = int(0.35 * SR); tt = ta(n)
    b = np.sin(2 * np.pi * np.cumsum(55 * (1 + np.exp(-tt * 30))) / SR) * np.exp(-tt * 14)
    s = np.zeros(int(0.6 * SR)); s[:n] += b; s[int(0.22 * SR):int(0.22 * SR) + n] += b * 0.7
    return s
fx, vo, bed, mus = np.zeros(N), np.zeros(N), np.zeros(N), np.zeros(N)
a, sr = sf.read("audio/vo_0.wav"); a = np.interp(np.linspace(0, len(a) - 1, int(len(a) * SR / sr)), np.arange(len(a)), a)
place(vo, a / np.abs(a).max() * 0.9, 0.05)
place(fx, scream(1.3), 0.0, 1.0)
# whoosh into the room cut
n = int(0.35 * SR); w = lp(rng.standard_normal(n), np.geomspace(500, 6000, n)) * np.sin(np.linspace(0, np.pi, n)) ** 1.5
place(fx, w / np.abs(w).max() * 0.5, 45 / 30 - 0.18)
# waterfall: brown+pink noise roar; louder (and duller, through rock) in the room shot
roar = lp(rng.standard_normal(N), 1800) * 0.7 + hp(lp(rng.standard_normal(N), 7000), 900) * 0.35
t = ta(N); inroom = t > 45 / 30
roar_room = lp(roar, 700) * 1.4
bed[:] = np.where(inroom, roar_room, roar)
for k in range(int(DUR / 0.6) + 1): place(mus, heartbeat(), k * 0.6, 0.8)
dr = np.sin(2 * np.pi * 41 * t) * 0.5 + np.sin(2 * np.pi * 61.5 * t) * 0.25
mus += dr * np.minimum(1, t / 0.4)
def norm(x, p): return x / max(1e-6, np.abs(x).max()) * p
vo, fx, bed, mus = norm(vo, 0.9), norm(fx, 0.75), norm(bed, 0.28), norm(mus, 0.3)
duck = 1 - 0.55 * np.clip(lp((np.abs(vo) > 0.02).astype(float), 8) * 3, 0, 1)
mix = vo + fx * (0.6 + 0.4 * duck) + (bed + mus) * duck
mix = np.tanh(mix * 1.2) / np.tanh(1.2); mix = mix / np.abs(mix).max() * 0.89
sf.write("audio/hook_mix.wav", np.stack([mix, mix], 1).astype(np.float32), SR)
print("ok")
