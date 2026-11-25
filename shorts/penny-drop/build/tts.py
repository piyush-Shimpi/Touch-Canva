"""Narration with Kokoro (local ONNX). Writes one wav per line + durations json."""
import json, sys, soundfile as sf
from kokoro_onnx import Kokoro
LINES = [
    "What if you dropped a penny from the top of a skyscraper?",
    "Most people think it would hit the ground like a bullet.",
    "But a penny is flat and light, so the air catches it, and it starts to flip and flutter.",
    "It tops out at around forty kilometers per hour.",
    "So if it hit you... it would just sting. A little.",
]
k = Kokoro("/opt/tts/kokoro-v1.0.onnx", "/opt/tts/voices-v1.0.bin")
voice, speed = sys.argv[1] if len(sys.argv) > 1 else "am_michael", float(sys.argv[2]) if len(sys.argv) > 2 else 1.1
out = []
for i, t in enumerate(LINES):
    a, sr = k.create(t, voice=voice, speed=speed, lang="en-us")
    sf.write(f"audio/vo_{i}.wav", a, sr)
    out.append({"i": i, "text": t, "dur": round(len(a) / sr, 2)})
json.dump(out, open("audio/vo.json", "w"), indent=1)
print(out, sum(o["dur"] for o in out))
