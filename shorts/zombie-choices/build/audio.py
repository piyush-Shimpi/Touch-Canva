"""Part 2 soundtrack -> audio/mix.wav (22.0 s, 48 kHz stereo). Circular buffer = seamless loop.
Run: /opt/ttsvenv/bin/python build/audio.py"""
import json
import os

import numpy as np
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
AUD = os.path.join(HERE, "..", "audio")
SR, DUR = 48000, 22.0
N = int(SR * DUR)
rng = np.random.default_rng(17)
meta = json.load(open(os.path.join(AUD, "vo.json")))
GAP = 0.1
VO_AT, t0 = [], 0.0
for m in meta[:-1]:
    VO_AT.append(round(t0, 3))
    t0 += m["dur"] + GAP
VO_AT.append(DUR - meta[-1]["dur"])                       # the question line ends on the loop point
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


def env(n, a=0.003, r=0.03):
    e = np.ones(n)
    na, nr = int(a * SR), int(r * SR)
    if na:
        e[:na] = np.linspace(0, 1, na)
    if nr:
        e[-nr:] *= np.linspace(1, 0, nr)
    return e


def mixs(*sigs):
    n = max(len(x) for x in sigs)
    out = np.zeros(n)
    for x in sigs:
        out[: len(x)] += x
    return out


def thump(f0, d, g=1.0):
    tt = ta(int(d * SR))
    return np.sin(2 * np.pi * np.cumsum(f0 * (1 + 2 * np.exp(-tt * 35))) / SR) * np.exp(-tt * 7) * env(len(tt)) * g


def whoosh(d, f0, f1, g=1.0, shape=1.5):
    n = int(d * SR)
    w = lp(rng.standard_normal(n), np.geomspace(f0, f1, n)) * np.sin(np.linspace(0, np.pi, n)) ** shape
    return w / np.abs(w).max() * g


def tone(f, d, decay=6.0):
    tt = ta(int(d * SR))
    return np.sin(2 * np.pi * f * tt) * np.exp(-tt * decay) * env(len(tt))


def bang(g=1.0):
    n = int(0.6 * SR)
    tt = ta(n)
    return (thump(62, 0.6) + hp(rng.standard_normal(n), 1800) * np.exp(-tt * 55) * 0.9
            + lp(rng.standard_normal(n), 900) * np.exp(-tt * 18) * 0.7) * g


def knock(g=1.0):
    n = int(0.18 * SR)
    tt = ta(n)
    return (thump(90, 0.18) * 0.7 + lp(rng.standard_normal(n), 1500) * np.exp(-tt * 60)) * g


def rattle(d=0.45, lo=2800, hi=4600):
    n = int(d * SR)
    s = np.zeros(n)
    for k in range(9):
        t0 = int(rng.uniform(0, d * 0.8) * SR)
        m = int(0.04 * SR)
        tt = ta(m)
        s[t0:t0 + m] += (np.sin(2 * np.pi * rng.uniform(lo, hi) * tt) + 0.5 * np.sin(2 * np.pi * rng.uniform(5200, 7200) * tt)) * np.exp(-tt * 90)
    return s


def snarl(d):
    n = int(d * SR)
    tt = ta(n)
    s = lp(rng.standard_normal(n), 650) * (0.6 + 0.4 * np.sin(2 * np.pi * 29 * tt)) + 0.35 * np.sin(2 * np.pi * np.cumsum(88 + 30 * np.sin(2 * np.pi * 2.5 * tt)) / SR)
    s *= np.sin(np.pi * tt / d) ** 0.6
    return s / np.abs(s).max()


def clank():
    tt = ta(int(0.5 * SR))
    s = sum(a * np.sin(2 * np.pi * f * tt) * np.exp(-tt * d) for f, a, d in ((1380, 1, 9), (2710, 0.6, 12), (4130, 0.35, 16)))
    return s + lp(rng.standard_normal(len(tt)), 2500) * np.exp(-tt * 40) * 0.8


def stamp():
    return mixs(thump(55, 0.6, 1.2), hp(rng.standard_normal(int(0.25 * SR)), 1200) * np.exp(-ta(int(0.25 * SR)) * 30) * 0.5,
                np.sign(np.sin(2 * np.pi * 110 * ta(int(0.35 * SR)))) * np.exp(-ta(int(0.35 * SR)) * 8) * 0.25)


fx, vo, mus = np.zeros(N), np.zeros(N), np.zeros(N)
for m, at in zip(meta, VO_AT):
    a, sr = sf.read(os.path.join(AUD, f"vo_{m['i']}.wav"))
    a = a if a.ndim == 1 else a.mean(1)
    a = np.interp(np.linspace(0, len(a) - 1, int(len(a) * SR / sr)), np.arange(len(a)), a)
    place(vo, a / np.abs(a).max() * 0.9, at)
t = ta(N)
# S01/S02 hook: bang on frame 0 + slams on the chain, snarls, whoosh on the cut
for f, g in ((1, 1.2), (22, 0.9), (44, 0.8), (63, 0.75)):
    place(fx, bang(g), T(f))
    place(fx, rattle(), T(f) + 0.02, 0.35)
place(fx, snarl(1.2), 0.08, 0.5)
place(fx, snarl(0.9), 1.6, 0.35)
place(fx, whoosh(0.45, 600, 5000, 0.6), T(40) - 0.2)
# S03 barricade: whip whoosh, fridge scrape, thud
place(fx, whoosh(0.35, 500, 4000, 0.5), T(76) - 0.1)
n = int(0.75 * SR)
place(fx, lp(rng.standard_normal(n), 400 + 300 * np.sin(np.linspace(0, 18, n)) ** 2) * env(n, 0.05, 0.1), T(78), 0.5)
place(fx, thump(70, 0.5, 0.9), T(99))
for f in (100, 112):
    place(fx, knock(0.5), T(f))
# S04 time-lapse: ticks speeding up
tick = hp(rng.standard_normal(int(0.012 * SR)), 3000) * np.exp(-ta(int(0.012 * SR)) * 400)
tt_ = T(119)
for k in range(26):
    place(fx, tick, tt_, 0.5)
    tt_ += 0.12 * (1 - 0.6 * k / 26)
# S05/S06: stomach growl, muffled bangs, ✗ stamp, whoosh to the yard
n = int(1.4 * SR)
growl = lp(rng.standard_normal(n), 160) * (0.5 + 0.5 * np.sin(2 * np.pi * 6 * ta(n))) * np.sin(np.linspace(0, np.pi, n))
place(fx, growl / np.abs(growl).max(), T(172), 0.45)
for f in (180, 200):
    place(fx, lp(bang(0.6), 500), T(f))
place(fx, stamp(), T(222), 0.9)
place(fx, whoosh(0.4, 3000, 400, 0.6), T(259) - 0.2)
# S07-S09 yard: shovel chunks, clank on hard dirt, fence rattles + groans, ✗ "too slow"
for at in (T(262), T(279), T(296)):
    place(fx, lp(rng.standard_normal(int(0.2 * SR)), 900) * np.exp(-ta(int(0.2 * SR)) * 20), at, 0.45)
place(fx, clank(), T(317), 0.8)
for k in range(5):
    place(fx, rattle(0.5, 1800, 3200), T(337) + k * 0.33, 0.35)
place(fx, snarl(1.2), T(340), 0.35)
place(fx, stamp(), T(375), 0.9)
# S10 crash zoom + jug SLAM, S11 pouring water
place(fx, whoosh(0.3, 400, 5000, 0.7, 1.0), T(388))
place(fx, mixs(thump(120, 0.3, 1.0), hp(rng.standard_normal(int(0.3 * SR)), 700) * np.exp(-ta(int(0.3 * SR)) * 30) * 0.5), T(396), 0.9)
n = int(1.45 * SR)
pour = lp(hp(rng.standard_normal(n), 400), 2600 + 800 * np.linspace(0, 1, n)) * env(n, 0.08, 0.15)
place(fx, pour / np.abs(pour).max(), T(433), 0.4)
# S12 PEAK (out 475): riser, music drop, door explosion, horde
PEAK = T(475)
n = int(1.4 * SR)
riser = (np.sin(2 * np.pi * np.cumsum(np.geomspace(120, 900, n)) / SR) * 0.5 + lp(rng.standard_normal(n), np.geomspace(400, 6000, n))) * np.linspace(0, 1, n) ** 2
place(fx, riser / np.abs(riser).max(), PEAK - 1.4, 0.45)
place(fx, bang(1.6), PEAK)
place(fx, thump(42, 1.2, 1.2), PEAK)
place(fx, rattle(0.6), PEAK, 0.6)
for k in range(4):
    place(fx, snarl(rng.uniform(0.8, 1.2)), PEAK + 0.15 + k * 0.2, 0.3)
# S13/S14 escape: running steps, breathing, heartbeat
for k in range(9):
    n = int(0.07 * SR)
    place(fx, lp(rng.standard_normal(n), 1200) * np.exp(-ta(n) * 70), T(517) + 0.05 + k * 0.34, 0.45)
for k in range(5):
    n = int(0.35 * SR)
    br = lp(hp(rng.standard_normal(n), 500), 2500) * np.sin(np.linspace(0, np.pi, n)) ** 2
    place(fx, br / np.abs(br).max(), T(520) + k * 0.62, 0.18)
for k in range(3):
    place(fx, thump(52, 0.4, 0.7), T(565) + 0.1 + k * 0.6)
    place(fx, thump(52, 0.4, 0.45), T(565) + 0.27 + k * 0.6)
# S15 whip back to the door: whoosh + knocks building to the frame-0 BANG
place(fx, whoosh(0.5, 500, 6000, 0.8, 1.0), T(619) - 0.1)
for f, g in ((632, 0.5), (642, 0.6), (650, 0.75), (656, 0.85)):
    place(fx, knock(g), T(f))

# music: 120 BPM, 11 bars; drops out 0.4 s before the peak, slams back on it
beat = 0.5
for k in range(44):
    tb = k * beat
    if not (PEAK - 0.4 < tb < PEAK):
        place(mus, thump(48, 0.35, 0.9), tb)
NOTES = [55, 55, 65.4, 55, 49, 49, 58.3, 49]
for k in range(88):
    tb = k * beat / 2
    if PEAK - 0.4 < tb < PEAK:
        continue
    tt = ta(int(0.22 * SR))
    place(mus, lp(np.sign(np.sin(2 * np.pi * NOTES[(k // 2) % 8] * tt)) * np.exp(-tt * 12), 450), tb, 0.33)
drop = (t > PEAK - 0.4) & (t < PEAK)
build = np.clip((t - 8.6) / 7.2, 0, 1) * (~drop)
for k in range(176):
    tb = k * beat / 4
    hat = hp(rng.standard_normal(int(0.03 * SR)), 7000) * np.exp(-ta(int(0.03 * SR)) * 160)
    place(mus, hat, tb, 0.12 * build[int(tb * SR) % N] * (1.0 if k % 2 else 0.6))


def norm(x, p):
    return x / max(1e-6, np.abs(x).max()) * p


vo, fx, mus = norm(vo, 0.9), norm(fx, 0.6), norm(mus, 0.4)
venv = lp(np.concatenate([np.abs(vo[-SR:]), np.abs(vo)]) > 0.02, 8.0)[SR:]
duck = 1 - 0.65 * np.clip(venv * 3, 0, 1)
mix = vo + fx * (0.6 + 0.4 * duck) + mus * duck
mix = np.tanh(mix * 1.2) / np.tanh(1.2)
mix = mix / np.abs(mix).max() * 0.89
st = np.stack([mix + 0.05 * np.roll(fx + mus, 240), mix - 0.05 * np.roll(fx + mus, 240)], 1)
st = st / np.abs(st).max() * 0.89
sf.write(os.path.join(AUD, "mix.wav"), st.astype(np.float32), SR)
print("mix", st.shape, "VO_AT", [round(x, 2) for x in VO_AT])
