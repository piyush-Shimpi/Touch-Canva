"""Soundtrack v2: narration + synthesized SFX + pluck bed -> audio/mix.wav (48 kHz stereo, 21.9 s).
Everything is placed on a circular buffer (tails wrap to the start) so the short loops seamlessly.
Run with the TTS venv (numpy + soundfile):  /opt/ttsvenv/bin/python build/audio.py
"""
import json
import os

import numpy as np
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
AUD = os.path.join(HERE, "..", "audio")
FPS = 30
END = 657
SR, DUR = 48000, END / FPS
N = int(round(SR * DUR))
rng = np.random.default_rng(3)
meta = json.load(open(os.path.join(AUD, "vo.json")))
VO_AT, t0 = [], 0.7
for m in meta:
    VO_AT.append(round(t0, 3))
    t0 += m["dur"] + 0.08
def T(f):
    return (f - 1) / FPS
A0, B0, C0, D0, E0, F0, G0, H0 = (T(x) for x in (1, 22, 91, 139, 230, 261, 384, 618))
X0, L0 = T(149), T(236)
W0, W1 = 392, 481


def wrap_frac(f):
    k = max(0.0, min(1.0, (f - W0) / (W1 - W0)))
    return k * k * (3 - 2 * k) * 0.25 + k * 0.75


LOOP_T = []
for target in (0.4, 0.8, 1.0):
    f = W0
    while wrap_frac(f) < target - 1e-6 and f < W1:
        f += 0.25
    LOOP_T.append(T(f))


def t_axis(n):
    return np.arange(n) / SR


def place(buf, sig, at, gain=1.0):
    """circular: anything past the end wraps to the start"""
    i = int(round(at * SR)) % N
    sig = np.asarray(sig) * gain
    while len(sig):
        j = min(N, i + len(sig))
        buf[i:j] += sig[: j - i]
        sig = sig[j - i:]
        i = 0


def env(n, a=0.005, r=0.1):
    e = np.ones(n)
    na, nr = int(a * SR), int(r * SR)
    if na:
        e[:na] = np.linspace(0, 1, na)
    if nr:
        e[-nr:] *= np.linspace(1, 0, nr)
    return e


def lowpass(x, cutoff):
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


def whoosh(dur=0.7, f0=300, f1=3000, gain=1.0, shape=1.5):
    n = int(dur * SR)
    w = lowpass(noise(n), np.geomspace(f0, f1, n)) * np.sin(np.linspace(0, np.pi, n)) ** shape
    return w / np.abs(w).max() * gain


def tone(f, dur, decay=4.0):
    tt = t_axis(int(dur * SR))
    return np.sin(2 * np.pi * f * tt) * np.exp(-tt * decay)


def thump(f0=60, dur=0.7, gain=1.0):
    tt = t_axis(int(dur * SR))
    s = np.sin(2 * np.pi * np.cumsum(f0 * (1 + 1.5 * np.exp(-tt * 30))) / SR) * np.exp(-tt * 6)
    return s * env(len(tt), 0.002, 0.05) * gain


fx = np.zeros(N)
vo = np.zeros(N)
mus = np.zeros(N)
for m, at in zip(meta, VO_AT):
    a, sr = sf.read(os.path.join(AUD, f"vo_{m['i']}.wav"))
    a = a if a.ndim == 1 else a.mean(1)
    a = resample(a, sr)
    a /= max(1e-6, np.abs(a).max())
    place(vo, a * 0.9, at)
t = t_axis(N)
# outdoor ambience whenever we're on the grass
outdoor = ((t < G0) | (t > H0)).astype(float)
fx += lowpass(noise(N), 350) * 0.22 * lowpass(outdoor, 3.0)
# 0.0 s: whip-zoom whoosh starts on the very first sample (its lead-in is the end of the loop)
place(fx, whoosh(0.75, 500, 6000, 0.9, 1.0), -0.12)
# laser slice: bright sizzle sweep + sub thump
n = int(0.38 * SR)
tt = t_axis(n)
zap = np.sin(2 * np.pi * np.cumsum(np.geomspace(5200, 1800, n)) / SR) * 0.4 + lowpass(noise(n), 7000) * 0.6
place(fx, zap * np.exp(-tt * 5) * env(n, 0.003, 0.08) * 0.55, B0)
place(fx, thump(48, 0.9, 1.0), B0)
place(fx, whoosh(0.35, 2500, 600, 0.35), T(31))            # skin peels open
# heartbeat under the close-ups and the globe outro
def heartbeat_track(t_from, t_to, gain):
    """lub-dub at 72 bpm, in phase with the emission pulse in build_scene.heartbeat()"""
    for k in range(int(t_to * 1.2) + 1):
        for off, g in ((0.042, 1.0), (0.21, 0.6)):
            tb = k / 1.2 + off
            if t_from <= tb < t_to:
                place(fx, thump(52, 0.45, g * gain), tb)


heartbeat_track(B0 + 0.3, D0, 0.75)
heartbeat_track(T(W1), H0 - 0.4, 0.6)
# dive in, whip out
place(fx, whoosh(1.2, 300, 1800, 0.55, 2.2), C0)
place(fx, whoosh(0.5, 4000, 400, 0.8), D0 - 0.05)
# extraction: wet wobble + low whomp, then the HOW LONG hit
n = int(1.8 * SR)
wob = lowpass(noise(n), 500 + 400 * np.sin(np.linspace(0, 22, n)) ** 2) * np.sin(np.linspace(0, np.pi, n))
place(fx, wob / np.abs(wob).max() * 0.5, X0)
place(fx, thump(42, 1.0, 0.9), D0 + 0.12)
# ball-up twist, then the line zips out
n = int(0.9 * SR)
tw = lowpass(noise(n), np.geomspace(2500, 300, n)) * np.sin(np.linspace(0, np.pi, n))
place(fx, tw / np.abs(tw).max() * 0.45, E0)
n = int(0.9 * SR)
zip_ = np.sin(2 * np.pi * np.cumsum(np.geomspace(300, 2400, n)) / SR) * np.sin(np.linspace(0, np.pi, n)) ** 0.5
place(fx, zip_ * 0.18 + whoosh(0.9, 400, 5000, 0.5), L0)
# racing wind, rising with speed + counter ticks
u = np.clip((t - F0) / (G0 - F0), 0, 1)
race = lowpass(noise(N), 300 + 5000 * u ** 1.5) * (u > 0) * (0.3 + 0.9 * u) * np.clip((G0 - t) / 0.12, 0, 1)
fx += race * 0.8
for k in range(34):
    place(fx, tone(2400, 0.03, 80) * 0.25, F0 + 0.1 + k * (3.9 / 34) * (1 - 0.3 * k / 34))
place(fx, whoosh(0.8, 3000, 200, 0.75), G0 - 0.25)         # out into space
sp_ = (np.sin(2 * np.pi * 55 * t) + 0.5 * np.sin(2 * np.pi * 82.5 * t)) * ((t > G0) & (t < H0))
fx += lowpass(sp_, 40.0) * 0.12 + lowpass(noise(N), 120) * ((t > G0) & (t < H0)) * 0.15
for i, lt in enumerate(LOOP_T):
    for h, a in ((1, 1), (2, 0.4), (3, 0.2)):
        place(fx, tone((880 if i < 2 else 1046.5) * h, 1.4, 2.5) * a * (0.35 if i < 2 else 0.5), lt)
# rush into the planet, then the sky dive back to Remy, rising into the loop point
place(fx, whoosh(0.5, 400, 3500, 0.7, 2.5), T(606))
place(fx, whoosh(1.5, 250, 3000, 0.6, 3.0), H0 - 0.05)
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


beat = 2 * DUR / 80                                        # exactly 80 eighth notes per loop
pattern = [("C", 4), ("G", 4), ("E", 5), ("G", 4), ("A", 3), ("E", 4), ("C", 5), ("E", 4),
           ("F", 3), ("C", 4), ("A", 4), ("C", 4), ("G", 3), ("D", 4), ("B", 4), ("D", 4)]
cache = {}
for i in range(80):
    nm = pattern[i % len(pattern)]
    if nm not in cache:
        cache[nm] = pluck(hz(*nm))
    place(mus, cache[nm], i * beat / 2, 0.9 if i % 4 == 0 else 0.6)
    if i % 4 == 0:
        place(mus, pluck(hz(nm[0], 2), 1.2), i * beat / 2, 0.7)
mus = lowpass(np.concatenate([mus[-SR:], mus]), 3500)[SR:]   # warm-up so the filter is loop-continuous

# ---------------- mix with simple ducking under the voice
def norm(x, peak):
    return x / max(1e-6, np.abs(x).max()) * peak


vo, fx, mus = norm(vo, 0.9), norm(fx, 0.55), norm(mus, 0.22)
vo_env = lowpass(np.concatenate([np.abs(vo[-SR:]) > 0.02, np.abs(vo) > 0.02]).astype(float), 6.0)[SR:]
duck = 1 - 0.55 * np.clip(vo_env * 3, 0, 1)
mix = vo + fx * (0.55 + 0.45 * duck) + mus * duck
mix = np.tanh(mix * 1.1) / np.tanh(1.1)
st = np.stack([mix, mix], 1)
# slight stereo width on fx/music only
st[:, 0] += 0.06 * np.roll(fx + mus, 300)
st[:, 1] -= 0.06 * np.roll(fx + mus, 300)
st = st / np.abs(st).max() * 0.95
sf.write(os.path.join(AUD, "mix.wav"), st.astype(np.float32), SR)
print("mix.wav", st.shape, "peak", float(np.abs(st).max()))
