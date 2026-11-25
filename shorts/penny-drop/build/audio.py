"""Soundtrack: narration + synthesized SFX + a light pluck music bed -> audio/mix.wav (48 kHz stereo, 25 s).
Run with the TTS venv (numpy + soundfile):  /opt/ttsvenv/bin/python build/audio.py
"""
import json
import os

import numpy as np
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
AUD = os.path.join(HERE, "..", "audio")
SR, DUR = 48000, 25.0
N = int(SR * DUR)
rng = np.random.default_rng(3)
FPS = 30
VO_AT = [0.35, 3.6, 8.2, 14.7, 19.3]      # seconds, one per narration line
HIT_T = 618 / FPS                          # penny bonks the guy's head
LAND_T = HIT_T + 0.94                      # penny lands on the sidewalk
SHOT2, SHOT3, SHOT5 = 99 / FPS, 241 / FPS, 571 / FPS


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

# ---------------- narration
meta = json.load(open(os.path.join(AUD, "vo.json")))
for m, at in zip(meta, VO_AT):
    a, sr = sf.read(os.path.join(AUD, f"vo_{m['i']}.wav"))
    a = a if a.ndim == 1 else a.mean(1)
    a = resample(a, sr)
    a /= max(1e-6, np.abs(a).max())
    place(vo, a * 0.9, at)

# ---------------- ambience / wind
t = t_axis(N)
roof_wind = lowpass(noise(N), 400) * 0.5
roof_env = np.clip((SHOT2 - t) / 0.3, 0, 1) * (0.25 + 0.05 * np.sin(t * 1.3))
fx += roof_wind * roof_env
# the big "bullet" rush: bright, rising wind during shot 2
rush_cut = np.where((t > SHOT2) & (t < SHOT3), 600 + 3000 * np.clip((t - SHOT2) / 4.5, 0, 1), 300)
rush = lowpass(noise(N), rush_cut)
rush_env = np.clip((t - SHOT2) / 0.15, 0, 1) * np.clip((SHOT3 - t) / 0.25, 0, 1)
fx += rush * rush_env * 0.9
# flutter: wind pulsing with the penny's flips (shots 3-4)
flut_env = np.clip((t - SHOT3) / 0.3, 0, 1) * np.clip((SHOT5 - t) / 0.4, 0, 1)
flutter = lowpass(noise(N), 900) * (0.55 + 0.45 * np.sin(2 * np.pi * 1.2 * t) ** 2)
fx += flutter * flut_env * 0.55
# street: low traffic rumble + distant horn
street = lowpass(noise(N), 180) * 0.8
fx += street * np.clip((t - SHOT5) / 0.3, 0, 1) * 0.35
horn_t = t_axis(int(0.5 * SR))
horn = (np.sin(2 * np.pi * 392 * horn_t) + 0.6 * np.sin(2 * np.pi * 494 * horn_t)) * env(len(horn_t), 0.02, 0.15)
place(fx, horn, SHOT5 + 0.6, 0.05)


# ---------------- one-shots
def whoosh(dur=0.7, f0=300, f1=3000, gain=1.0):
    n = int(dur * SR)
    cut = np.geomspace(f0, f1, n)
    w = lowpass(noise(n), cut) * np.sin(np.linspace(0, np.pi, n)) ** 1.5
    return w / np.abs(w).max() * gain


def tink(f=2900, dur=0.35, gain=1.0):
    tt = t_axis(int(dur * SR))
    s = sum(a * np.sin(2 * np.pi * f * k * tt) * np.exp(-tt * d) for k, a, d in
            ((1, 1, 14), (2.76, 0.5, 20), (5.4, 0.25, 30), (8.9, 0.12, 40)))
    return s * gain


def bonk():
    tt = t_axis(int(0.45 * SR))
    thump = np.sin(2 * np.pi * (180 * tt - 120 * tt * tt)) * np.exp(-tt * 9)
    knock = lowpass(noise(len(tt)), 1800) * np.exp(-tt * 40) * 2
    return thump + knock + tink(3400, 0.45, 0.35)[: len(tt)]


def boing(dur=0.7):
    tt = t_axis(int(dur * SR))
    f = 220 + 200 * np.exp(-tt * 3) + 25 * np.sin(2 * np.pi * 11 * tt) * np.exp(-tt * 2)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-tt * 3.2) * env(len(tt), 0.005, 0.05)


def twinkle(f=1600):
    tt = t_axis(int(0.18 * SR))
    return np.sin(2 * np.pi * f * tt) * np.exp(-tt * 18)


place(fx, lowpass(noise(int(0.5 * SR)), 2500) * env(int(0.5 * SR), 0.05, 0.2) * 0.15, 55 / FPS)  # finger slides coin
place(fx, tink(3100, 0.3, 0.35), 76 / FPS)                 # coin tips off the ledge
place(fx, whoosh(0.6, 400, 4000, 0.8), SHOT2 - 0.2)        # into the bullet shot
place(fx, whoosh(0.8, 2500, 400, 0.6), SHOT3 - 0.2)        # slows down
for k in range(5):                                         # little flips
    place(fx, whoosh(0.25, 800, 2500, 0.25), SHOT3 + 0.6 + k * 0.83)
place(fx, whoosh(0.5, 600, 3000, 0.5), SHOT5 + 1.2)        # penny drops into frame
place(fx, bonk(), HIT_T, 1.0)
place(fx, boing(), HIT_T + 0.05, 0.45)
place(fx, tink(2600, 0.5, 0.6), LAND_T)
place(fx, tink(2750, 0.3, 0.3), LAND_T + 0.22)
place(fx, tink(2900, 0.2, 0.15), LAND_T + 0.36)
for k in range(7):                                         # dizzy stars
    place(fx, twinkle(1500 + 300 * (k % 3)), HIT_T + 0.35 + k * 0.42, 0.18)

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


beat = 60 / 104
pattern = [("A", 3), ("E", 4), ("C", 5), ("E", 4), ("F", 3), ("C", 4), ("A", 4), ("C", 4),
           ("D", 3), ("A", 3), ("F", 4), ("A", 3), ("E", 3), ("B", 3), ("G#", 4), ("B", 3)]
cache = {}
i, tt0 = 0, 0.0
while tt0 < DUR:
    nm = pattern[i % len(pattern)]
    if nm not in cache:
        cache[nm] = pluck(hz(*nm))
    on = not (HIT_T - 0.05 < tt0 < HIT_T + 1.0)            # music drops out for the bonk
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
