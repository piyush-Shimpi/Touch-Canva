"""Kokoro narration, one trimmed wav per line -> audio/vo_<i>.wav + audio/vo.json"""
import json, sys
import numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
LINES = [
    "A zombie outbreak, according to real scientists.",
    "Cornell researchers simulated one across 307 million Americans.",
    "Big cities fell in days.",
    "Step one: get out. Don't hide downtown.",
    "Step two: pack a gallon of water per person, per day.",
    "Step three: head for the hills.",
    "Zombies took months to reach the northern Rockies.",
    "That's how you'd last longest in",
]
speed = float(sys.argv[1]) if len(sys.argv) > 1 else 1.1
k = Kokoro("/opt/tts/kokoro-v1.0.onnx", "/opt/tts/voices-v1.0.bin")
out = []
for i, t in enumerate(LINES):
    a, sr = k.create(t, voice="am_michael", speed=speed, lang="en-us")
    a = np.asarray(a, np.float32)
    lvl = np.convolve(np.abs(a), np.ones(240) / 240, "same")
    on = np.where(lvl > 0.01 * lvl.max())[0]
    a = a[max(0, on[0] - int(0.012 * sr)): on[-1] + int(0.02 * sr)]
    sf.write(f"audio/vo_{i}.wav", a, sr)
    out.append({"i": i, "text": t, "dur": round(len(a) / sr, 3)})
json.dump(out, open("audio/vo.json", "w"), indent=1)
for o in out:
    print(o["dur"], o["text"])
print("total", round(sum(o["dur"] for o in out), 2))
