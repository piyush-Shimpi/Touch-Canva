"""Zombie short soundtrack -> audio/mix.wav (22.0 s, 48 kHz stereo). Circular buffer = seamless loop.
Run: /opt/ttsvenv/bin/python build/audio.py"""
import json
import os

import numpy as np
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
AUD = os.path.join(HERE, "..", "audio")
SR, DUR = 48000, 22.0
N = int(SR * DUR)
rng = np.random.default_rng(11)
meta = json.load(open(os.path.join(AUD, "vo.json")))
GAP = 0.1
VO_AT = []
t0 = 0.0
for m in meta[:-1]:
    VO_AT.append(t0)
    t0 += m["dur"] + GAP
VO_AT.append(DUR - meta[-1]["dur"])                 # last line ends on the loop point
json.dump(VO_AT, open(os.path.join(AUD, "vo_at.json"), "w"))


def T(out_frame):
    return (out_frame - 1) / 30


def ta(n):
    return np.arange(n) / SR


def place(buf, s, at, g=1.0):
    i = int(round(at * SR)) % N
    s = np.asarray(s) * g
    while len(s):
        j = min(N, i + len(s))
        buf[i:j] += s[: j - i]
        s = s[j - i:]
        i = 0


def lp(x, c):
    c = np.broadcast_to(np.asarray(c, float), x.shape)
    a = 1 - np.exp(-2 * np.pi * c / SR)
    y = np.empty_like(x)
    acc = 0.0
    for i in range(len(x)):
        acc += a[i] * (x[i] - acc)
        y[i] = acc
    return y


def hp(x, c):
    return x - lp(x, c)


def env(n, a=0.005, r=0.05):
    e = np.ones(n)
    na, nr = int(a * SR), int(r * SR)
    if na:
        e[:na] = np.linspace(0, 1, na)
    if nr:
        e[-nr:] *= np.linspace(1, 0, nr)
    return e


def thump(f0, d, g=1.0):
    tt = ta(int(d * SR))
    return np.sin(2 * np.pi * np.cumsum(f0 * (1 + 2 * np.exp(-tt * 35))) / SR) * np.exp(-tt * 7) * env(len(tt), 0.001, 0.02) * g


def whoosh(d, f0, f1, g=1.0, shape=1.5):
    n = int(d * SR)
    w = lp(rng.standard_normal(n), np.geomspace(f0, f1, n)) * np.sin(np.linspace(0, np.pi, n)) ** shape
    return w / np.abs(w).max() * g


def tone(f, d, decay=6.0):
    tt = ta(int(d * SR))
    return np.sin(2 * np.pi * f * tt) * np.exp(-tt * decay) * env(len(tt), 0.002, 0.02)


def step(heavy=False):
    n = int(0.07 * SR)
    s = lp(rng.standard_normal(n), 700 if heavy else 1200) * np.exp(-ta(n) * (45 if heavy else 70))
    return s


def snarl(d):
    n = int(d * SR)
    tt = ta(n)
    s = lp(rng.standard_normal(n), 650) * (0.6 + 0.4 * np.sin(2 * np.pi * 29 * tt))
    s += 0.35 * np.sin(2 * np.pi * np.cumsum(90 + 30 * np.sin(2 * np.pi * 2.5 * tt)) / SR)
    s *= np.sin(np.pi * tt / d) ** 0.6
    return s / np.abs(s).max()


def scream(d):
    n = int(d * SR)
    tt = ta(n)
    f = 260 + 140 * np.sin(np.pi * tt / d) + 25 * np.sin(2 * np.pi * 7 * tt)
    voice = np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * 0.4 + lp(rng.standard_normal(n), 2500) * 0.8
    voice = lp(hp(voice, 300), 3000) * np.sin(np.pi * tt / d) ** 0.4
    return voice / np.abs(voice).max()


def mixs(*sigs):
    n = max(len(x) for x in sigs)
    out = np.zeros(n)
    for x in sigs:
        out[: len(x)] += x
    return out


fx, vo, mus = np.zeros(N), np.zeros(N), np.zeros(N)
for m, at in zip(meta, VO_AT):
    a, sr = sf.read(os.path.join(AUD, f"vo_{m['i']}.wav"))
    a = a if a.ndim == 1 else a.mean(1)
    a = np.interp(np.linspace(0, len(a) - 1, int(len(a) * SR / sr)), np.arange(len(a)), a)
    place(vo, a / np.abs(a).max() * 0.9, at)
t = ta(N)

# S01/S02 hook: frame-0 snap (2 clicks 40 ms apart) + sub hit, footsteps, snarl, whoosh on the cut
n = int(0.03 * SR)
click = hp(rng.standard_normal(n), 2500) * np.exp(-ta(n) * 300)
place(fx, click, 0.0, 1.0)
place(fx, click, 0.04, 0.8)
place(fx, thump(55, 0.8), 0.0, 1.1)
for k in range(9):
    place(fx, step(), 0.05 + k * 0.35, 0.5)
    place(fx, step(True), 0.22 + k * 0.38, 0.35)
place(fx, snarl(1.1), 0.1, 0.45)
place(fx, whoosh(0.45, 600, 5000, 0.7), T(40) - 0.2)
# outdoor/city air bed under the city shots
city = ((t < T(94)) | ((t > T(238)) & (t < T(358))) | (t > T(628))).astype(float)
fx += lp(rng.standard_normal(N), 300) * 0.12 * lp(city, 4.0)
# S03/S04 map: blip in, rising hum, bloom pings as cities light up
place(fx, mixs(tone(1760, 0.25, 18), tone(2640, 0.2, 22) * 0.5), T(94), 0.35)
hum_on = ((t > T(157)) & (t < T(238))).astype(float)
fx += np.sin(2 * np.pi * (110 + 40 * np.clip((t - T(157)) / 2.7, 0, 1)) * t) * lp(hum_on, 6.0) * 0.18
for k, ft in enumerate((175, 186, 196, 205, 214, 222)):
    place(fx, tone(880 * (1 + 0.12 * k), 0.4, 9), T(ft), 0.22)
# S05 crowd: layered groans + shuffle
for k in range(7):
    place(fx, snarl(rng.uniform(0.8, 1.4)), T(238) + rng.uniform(0, 1.0), 0.22)
for k in range(10):
    place(fx, step(True), T(238) + k * 0.16, 0.25)
# S06 escape: fast steps + whoosh past the car; S07 scream
for k in range(4):
    place(fx, step(), T(286) + 0.1 + k * 0.33, 0.55)
place(fx, whoosh(0.4, 400, 3000, 0.6), T(305))
place(fx, scream(0.9), T(325) + 0.05, 0.55)
place(fx, thump(48, 0.6), T(325), 0.7)
# S08 jugs: three plastic thunks
for k in range(3):
    land = T(358) + (3 + 11 * k + 9) / 30
    place(fx, mixs(thump(140, 0.25, 0.8), hp(rng.standard_normal(int(0.25 * SR)), 900) * np.exp(-ta(int(0.25 * SR)) * 40) * 0.4), land, 0.6)
    place(fx, whoosh(0.3, 1200, 400, 0.25), land - 0.3)
# S09 road: wind + steps
wind_on = ((t > T(403)) & (t < T(451))).astype(float)
fx += lp(rng.standard_normal(N), 500) * lp(wind_on, 4.0) * 0.3
for k in range(5):
    place(fx, step(), T(403) + 0.1 + k * 0.36, 0.4)
# S10 route: whoosh in + route draw sweep + pin ping
place(fx, whoosh(0.5, 3000, 300, 0.6), T(451) - 0.2)
place(fx, np.sin(2 * np.pi * np.cumsum(np.geomspace(300, 1200, int(1.1 * SR))) / SR) * np.sin(np.linspace(0, np.pi, int(1.1 * SR))), T(455), 0.15)
place(fx, mixs(tone(1318, 0.8, 4), tone(1976, 0.6, 5) * 0.4), T(490), 0.35)
# S11 gravel steps
for k in range(4):
    place(fx, lp(rng.standard_normal(int(0.09 * SR)), 2500) * np.exp(-ta(int(0.09 * SR)) * 35), T(499) + 0.05 + k * 0.28, 0.4)
# S12 PEAK: riser into the hit (local 318 -> out 550), impact + white flash
PEAK = T(550)
n = int(1.6 * SR)
riser = (np.sin(2 * np.pi * np.cumsum(np.geomspace(120, 900, n)) / SR) * 0.5 + lp(rng.standard_normal(n), np.geomspace(400, 6000, n))) * np.linspace(0, 1, n) ** 2
place(fx, riser / np.abs(riser).max(), PEAK - 1.6, 0.5)
place(fx, thump(42, 1.2, 1.3), PEAK)
place(fx, hp(rng.standard_normal(int(0.4 * SR)), 1500) * np.exp(-ta(int(0.4 * SR)) * 12), PEAK, 0.5)
place(fx, mixs(tone(523, 1.6, 2.2), tone(784, 1.4, 2.4) * 0.6, tone(1046, 1.2, 2.6) * 0.4), PEAK + 0.05, 0.35)
# S13 summit heartbeat, S14 groan, whip pan into the loop
for k in range(3):
    place(fx, thump(52, 0.4, 0.8), T(577) + 0.1 + k * 0.62)
    place(fx, thump(52, 0.4, 0.5), T(577) + 0.27 + k * 0.62)
place(fx, snarl(1.0), T(601) + 0.1, 0.4)
place(fx, whoosh(0.55, 500, 6000, 0.8, 1.0), T(620))
for k in range(4):
    place(fx, step(), T(640) + k * 0.35, 0.45)
place(fx, snarl(0.9), T(640), 0.3)

# music: 120 BPM, 11 bars = 22 s exactly; drops out 0.4 s before the peak and slams back on it
beat = 0.5
drop = (t > PEAK - 0.4) & (t < PEAK)
for k in range(44):
    tb = k * beat
    if not (PEAK - 0.4 < tb < PEAK):
        place(mus, thump(48, 0.35, 0.9), tb)
NOTES = [55, 55, 65.4, 55, 49, 49, 58.3, 49]               # A, C, G, Bb pattern
for k in range(88):
    tb = k * beat / 2
    if PEAK - 0.4 < tb < PEAK:
        continue
    tt = ta(int(0.22 * SR))
    b = np.sign(np.sin(2 * np.pi * NOTES[(k // 2) % 8] * tt)) * np.exp(-tt * 12)
    place(mus, lp(b, 450), tb, 0.33)
build = np.clip((t - 7.9) / 8, 0, 1) * (~drop)
for k in range(176):                                       # 16th hats get stronger towards the peak
    tb = k * beat / 4
    hat = hp(rng.standard_normal(int(0.03 * SR)), 7000) * np.exp(-ta(int(0.03 * SR)) * 160)
    place(mus, hat, tb, 0.12 * build[int(tb * SR) % N] * (1.0 if k % 2 else 0.6))
pad_on = (t > PEAK).astype(float)
mus += (np.sin(2 * np.pi * 220 * t) + 0.6 * np.sin(2 * np.pi * 329.6 * t) + 0.4 * np.sin(2 * np.pi * 261.6 * t)) * lp(pad_on, 3.0) * 0.05


def norm(x, p):
    return x / max(1e-6, np.abs(x).max()) * p


vo, fx, mus = norm(vo, 0.9), norm(fx, 0.6), norm(mus, 0.4)
venv = lp(np.concatenate([np.abs(vo[-SR:]), np.abs(vo)]) > 0.02, 8.0)[SR:]
duck = 1 - 0.65 * np.clip(venv * 3, 0, 1)                 # about -10 dB under the voice
mix = vo + fx * (0.6 + 0.4 * duck) + mus * duck
mix = np.tanh(mix * 1.2) / np.tanh(1.2)
mix = mix / np.abs(mix).max() * 0.89
st = np.stack([mix + 0.05 * np.roll(fx + mus, 240), mix - 0.05 * np.roll(fx + mus, 240)], 1)
st = st / np.abs(st).max() * 0.89
sf.write(os.path.join(AUD, "mix.wav"), st.astype(np.float32), SR)
print("mix", st.shape, "VO_AT", [round(x, 2) for x in VO_AT])
