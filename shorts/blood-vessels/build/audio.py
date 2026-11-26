"""Soundtrack: narration + synthesized SFX + a light pluck music bed -> audio/mix.wav (48 kHz stereo, 25 s).
Run with the TTS venv (numpy + soundfile):  /opt/ttsvenv/bin/python build/audio.py
"""
import json
import os

import numpy as np
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
AUD = os.path.join(HERE, "..", "audio")
SR, DUR = 48000, 28.0
N = int(SR * DUR)
rng = np.random.default_rng(3)
FPS = 30
VO_AT = [0.4, 4.3, 11.5, 15.2, 20.4, 25.0]
S2T, S3T, S4T, S5T, S6T = 121 / FPS, 256 / FPS, 342 / FPS, 451 / FPS, 601 / FPS
W0, W1 = 641, 801


def wrap_frac(f):
    k = max(0.0, min(1.0, (f - W0) / (W1 - W0)))
    return k * k * (3 - 2 * k) * 0.25 + k * 0.75


LOOP_T = []
for target in (0.4, 0.8, 1.0):
    f = W0
    while wrap_frac(f) < target - 1e-6 and f < W1:
        f += 0.25
    LOOP_T.append(f / FPS)



def t_axis(n):
    return np.arange(n) / SR


def place(buf, sig, at, gain=1.0):
    i = int(at * SR)
    j = min(N, i + len(sig))
    if j > i:
        buf[i:j] += sig[: j - i] * gain


def env(n, a=0.005, r=0.1):
    e = np.ones(n)
    na, nr = int(a * SR), int(r * SR)
    if na:
        e[:na] = np.linspace(0, 1, na)
    if nr:
        e[-nr:] *= np.linspace(1, 0, nr)
    return e


def lowpass(x, cutoff):
    """one-pole low-pass, cutoff may be an array (Hz)"""
    c = np.broadcast_to(np.asarray(cutoff, float), x.shape)
    a = 1 - np.exp(-2 * np.pi * c / SR)
    y = np.empty_like(x)
    acc = 0.0
    for i in range(len(x)):
        acc += a[i] * (x[i] - acc)
        y[i] = acc
    return y


def noise(n):
    return rng.standard_normal(n)


def resample(x, sr_in):
    if sr_in == SR:
        return x
    n_out = int(len(x) * SR / sr_in)
    return np.interp(np.linspace(0, len(x) - 1, n_out), np.arange(len(x)), x)


fx = np.zeros(N)
vo = np.zeros(N)
mus = np.zeros(N)
meta = json.load(open(os.path.join(AUD, "vo.json")))
for m, at in zip(meta, VO_AT):
    a, sr = sf.read(os.path.join(AUD, f"vo_{m['i']}.wav"))
    a = a if a.ndim == 1 else a.mean(1)
    a = resample(a, sr)
    a /= max(1e-6, np.abs(a).max())
    place(vo, a * 0.9, at)
t = t_axis(N)
# outdoor ambience + birds (shots 1-4)
outdoor = np.clip((S5T - t) / 0.3, 0, 1)
fx += lowpass(noise(N), 350) * 0.25 * outdoor
for k in range(9):
    bt = random_t = 0.6 + k * 1.37
    if bt > S5T - 0.5:
        break
    tt = t_axis(int(0.12 * SR))
    f0 = 3200 + 900 * ((k * 7) % 3)
    chirp = np.sin(2 * np.pi * np.cumsum(f0 + 1800 * np.sin(np.pi * tt / 0.12)) / SR) * np.sin(np.pi * tt / 0.12)
    place(fx, chirp, bt, 0.05)
    place(fx, chirp, bt + 0.16, 0.035)


def whoosh(dur=0.7, f0=300, f1=3000, gain=1.0):
    n = int(dur * SR)
    cut = np.geomspace(f0, f1, n)
    w = lowpass(noise(n), cut) * np.sin(np.linspace(0, np.pi, n)) ** 1.5
    return w / np.abs(w).max() * gain


def tone(f, dur, decay=4.0):
    tt = t_axis(int(dur * SR))
    return np.sin(2 * np.pi * f * tt) * np.exp(-tt * decay)


# x-ray shimmer (frames 55-95)
tt = t_axis(int(1.6 * SR))
shim = sum(np.sin(2 * np.pi * f * (1 + 0.5 * tt / 1.6) * tt) for f in (660, 990, 1320)) * (0.5 + 0.5 * np.sin(2 * np.pi * 9 * tt))
place(fx, shim * np.sin(np.pi * tt / 1.6) * 0.12, 55 / FPS)
# vessels slide out: wet wobble + low whomp (frames ~150-215)
n = int(2.2 * SR)
wob = lowpass(noise(n), 500 + 400 * np.sin(np.linspace(0, 22, n)) ** 2) * np.sin(np.linspace(0, np.pi, n))
place(fx, wob / np.abs(wob).max() * 0.5, 151 / FPS)
place(fx, tone(70, 0.6, 6) * 0.8, 152 / FPS)
# reaction impact
place(fx, tone(55, 0.9, 4) * 1.0 + 0, S3T)
place(fx, whoosh(0.5, 2500, 300, 0.6), S3T - 0.1)
# tangle collapse: twisting rubber, then the line zips out
n = int(1.7 * SR)
tw = lowpass(noise(n), np.geomspace(2500, 300, n)) * np.sin(np.linspace(0, np.pi, n))
place(fx, tw / np.abs(tw).max() * 0.45, (S4T + 0.1))
n = int(1.0 * SR)
zip_ = np.sin(2 * np.pi * np.cumsum(np.geomspace(300, 2400, n)) / SR) * np.sin(np.linspace(0, np.pi, n)) ** 0.5
place(fx, zip_ * 0.18 + whoosh(1.0, 400, 5000, 0.5), 397 / FPS)
# racing wind (shot 5), rising with speed
u = np.clip((t - S5T) / (S6T - S5T), 0, 1)
race = lowpass(noise(N), 300 + 5000 * u ** 1.5) * (u > 0) * (0.3 + 0.9 * u) * np.clip((S6T - t) / 0.15, 0, 1)
fx += race * 0.8
for k in range(40):                                  # counter ticks
    place(fx, tone(2400, 0.03, 80) * 0.25, S5T + 0.1 + k * (4.8 / 40) * (1 - 0.3 * k / 40))
place(fx, whoosh(0.9, 3000, 200, 0.7), S6T - 0.3)    # out into space
# space drone + loop chimes
sp = (np.sin(2 * np.pi * 55 * t) + 0.5 * np.sin(2 * np.pi * 82.5 * t)) * (t > S6T) * np.clip((t - S6T) / 1.0, 0, 1)
fx += sp * 0.12 + lowpass(noise(N), 120) * (t > S6T) * 0.15
for i, lt in enumerate(LOOP_T):
    for h, a in ((1, 1), (2, 0.4), (3, 0.2)):
        place(fx, tone((880 if i < 2 else 1046.5) * h, 1.4, 2.5) * a * (0.35 if i < 2 else 0.5), lt)
# ---------------- music: curious pizzicato loop (Karplus-Strong), 104 bpm
def pluck(freq, dur=0.6):
    n = int(dur * SR)
    p = max(2, int(SR / freq))
    buf = rng.uniform(-1, 1, p)
    out = np.empty(n)
    for i in range(n):
        out[i] = buf[i % p]
        buf[i % p] = 0.5 * (buf[i % p] + buf[(i + 1) % p]) * 0.996
    return out * env(n, 0.002, 0.05)


NOTE = {n: 440 * 2 ** ((i - 9) / 12) for i, n in enumerate("C C# D D# E F F# G G# A A# B".split())}


def hz(name, octv):
    return NOTE[name] * 2 ** (octv - 4)


beat = 60 / 112
pattern = [("C", 4), ("G", 4), ("E", 5), ("G", 4), ("A", 3), ("E", 4), ("C", 5), ("E", 4),
           ("F", 3), ("C", 4), ("A", 4), ("C", 4), ("G", 3), ("D", 4), ("B", 4), ("D", 4)]
cache = {}
i, tt0 = 0, 0.0
while tt0 < DUR:
    nm = pattern[i % len(pattern)]
    if nm not in cache:
        cache[nm] = pluck(hz(*nm))
    on = True
    if on:
        place(mus, cache[nm], tt0, 0.9 if i % 4 == 0 else 0.6)
    if i % 4 == 0 and on:
        place(mus, pluck(hz(nm[0], 2), 1.2), tt0, 0.7)     # bass
    i += 1
    tt0 += beat / 2
mus = lowpass(mus, 3500)

# ---------------- mix with simple ducking under the voice
def norm(x, peak):
    return x / max(1e-6, np.abs(x).max()) * peak


vo, fx, mus = norm(vo, 0.9), norm(fx, 0.55), norm(mus, 0.22)
vo_env = lowpass(np.abs(vo) > 0.02, 6.0)
duck = 1 - 0.55 * np.clip(vo_env * 3, 0, 1)
mix = vo + fx * (0.55 + 0.45 * duck) + mus * duck
mix = np.tanh(mix * 1.1) / np.tanh(1.1)
fade = np.ones(N)
fade[-int(0.6 * SR):] = np.linspace(1, 0, int(0.6 * SR))
mix *= fade
st = np.stack([mix, mix], 1)
# slight stereo width on fx/music only
st[:, 0] += 0.06 * np.roll(fx + mus, 300)
st[:, 1] -= 0.06 * np.roll(fx + mus, 300)
st = st / np.abs(st).max() * 0.95
sf.write(os.path.join(AUD, "mix.wav"), st.astype(np.float32), SR)
print("mix.wav", st.shape, "peak", float(np.abs(st).max()))
