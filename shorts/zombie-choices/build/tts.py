"""Kokoro narration for part 2, one trimmed wav per line -> audio/vo_<i>.wav + audio/vo.json"""
import json, sys
import numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
LINES = [
    "Zombies outside your door. What do you do?",
    "Stay home? Most homes have food for about three days.",
    "After three weeks without food, you're too weak to run.",
    "Dig a bunker? Hard soil takes about a day per cubic meter.",
    "Too slow.",
    "Real answer: water first. Three days without it, and you're done.",
    "Which one would you pick, when you hear",
]
speed = float(sys.argv[1]) if len(sys.argv) > 1 else 1.12
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
