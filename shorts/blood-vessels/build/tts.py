"""Narration with Kokoro (local ONNX), am_michael @ 1.18x. Writes one trimmed wav per line + durations json.
Leading/trailing silence is cut so lines can be butted together with <= 0.08 s gaps."""
import json, sys
import numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
LINES = [
    "If you slice into any part of your body, you'll see tiny blood vessels.",
    "Now imagine stretching every single one end to end.",
    "Laid out in one line, they'd race across the land",
    "for about one hundred thousand kilometers!",
    "That's enough to wrap around the entire Earth",
    "two and a half times!",
    "And your heart pushes blood through every last one of them, around the clock.",
    "All packed inside... you.",
]
k = Kokoro("/opt/tts/kokoro-v1.0.onnx", "/opt/tts/voices-v1.0.bin")
voice = sys.argv[1] if len(sys.argv) > 1 else "am_michael"
speed = float(sys.argv[2]) if len(sys.argv) > 2 else 1.18
out = []
for i, t in enumerate(LINES):
    a, sr = k.create(t, voice=voice, speed=speed, lang="en-us")
    a = np.asarray(a, dtype=np.float32)
    lvl = np.convolve(np.abs(a), np.ones(240) / 240, "same")
    on = np.where(lvl > 0.01 * lvl.max())[0]
    a = a[max(0, on[0] - int(0.015 * sr)): on[-1] + int(0.03 * sr)]
    sf.write(f"audio/vo_{i}.wav", a, sr)
    out.append({"i": i, "text": t, "dur": round(len(a) / sr, 3)})
json.dump(out, open("audio/vo.json", "w"), indent=1)
for o in out:
    print(o["dur"], o["text"])
print("total", round(sum(o["dur"] for o in out), 2))
