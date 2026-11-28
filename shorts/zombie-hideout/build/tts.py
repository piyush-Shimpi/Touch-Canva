"""Kokoro narration for part 3 (hideout), one trimmed wav per line -> audio/vo_<i>.wav + audio/vo.json"""
import json, sys
import numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
LINES = [
    "Zombies are hunting you, so you hide behind a waterfall.",
    "They hunt by sound, but the roar drowns out every noise.",
    "The water's freezing, so you dig a dry room into the rock.",
    "They follow footprints, so you only walk in the stream.",
    "They smell you, but the falls wash your scent away.",
    "Your fire makes smoke, so you vent it into the falling water.",
    "At night, the water hides the glow.",
    "Then the horde reaches the pool,",
    "and walks right past.",
    "But summer's coming, and the waterfall is shrinking.",
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
