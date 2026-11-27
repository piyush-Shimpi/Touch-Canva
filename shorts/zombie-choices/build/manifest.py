"""shot_manifest.json for the QA gate. Subject boxes are hand-measured from the 1080x1920 test frames
(approximate, mid-shot); text boxes come from captions.py."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
texts = json.load(open(os.path.join(HERE, "..", "audio", "text_events.json")))
vo = json.load(open(os.path.join(HERE, "..", "audio", "vo.json")))
at = json.load(open(os.path.join(HERE, "..", "audio", "vo_at.json")))
S = [  # id, out frames, type, beat, subject boxes [x, y, w, h] (faces / key action; re-measured on the QA sheet)
    ("S01", 1, 39, "MEDIUM", "hook", [[420, 640, 420, 700]]),
    ("S02", 40, 75, "MCU", "build", [[260, 380, 600, 700]]),
    ("S03", 76, 118, "MEDIUM", "build", [[60, 420, 700, 900]]),
    ("S04", 119, 168, "CU", "build", [[100, 560, 880, 440]]),
    ("S05", 169, 216, "TOPDOWN", "build", [[250, 480, 450, 660]]),
    ("S06", 217, 258, "CU", "build", [[200, 420, 700, 800]]),
    ("S07", 259, 300, "MEDIUM", "build", [[150, 540, 700, 700]]),
    ("S08", 301, 336, "CU", "build", [[150, 480, 550, 420]]),
    ("S09", 337, 387, "WIDE", "build", [[0, 480, 1080, 700]]),
    ("S10", 388, 432, "CU", "build", [[300, 440, 500, 800]]),
    ("S11", 433, 474, "MCU", "build", [[380, 360, 400, 720]]),
    ("S12", 475, 516, "WIDE", "peak", [[250, 420, 600, 800]]),
    ("S13", 517, 564, "MEDIUM", "build", [[200, 520, 500, 700]]),
    ("S14", 565, 618, "CU", "payoff", [[200, 420, 700, 800]]),
    ("S15", 619, 660, "MEDIUM", "loop", [[380, 500, 500, 700]]),
]
shots = []
for sid, f0, f1, typ, beat, subs in S:
    t0, t1 = (f0 - 1) / 30, f1 / 30
    mid = (t0 + t1) / 2
    tx = [dict(kind=x["kind"], text=x["text"], box=x["box"]) for x in texts if x["t0"] <= mid < x["t1"]]
    shots.append(dict(id=sid, start=round(t0, 3), end=round(t1, 3), type=typ, beat=beat, subjects=subs, texts=tx))
last_end = at[-1] + vo[-1]["dur"]
json.dump({"shots": shots, "narration": {"first_word_start": 0.0, "last_word_end": round(last_end, 3)}},
          open(os.path.join(HERE, "..", "shot_manifest.json"), "w"), indent=1)
print("manifest", len(shots), "shots; last word ends", round(last_end, 3))
