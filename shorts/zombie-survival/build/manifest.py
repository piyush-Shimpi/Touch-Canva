"""shot_manifest.json for the QA gate. Subject boxes are hand-measured from the 1080x1920 test frames
(approximate, mid-shot); text boxes come from captions.py."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
texts = json.load(open(os.path.join(HERE, "..", "audio", "text_events.json")))
vo = json.load(open(os.path.join(HERE, "..", "audio", "vo.json")))
at = json.load(open(os.path.join(HERE, "..", "audio", "vo_at.json")))
S = [  # id, out frames, type, beat, subject boxes [x, y, w, h] at mid-shot
    ("S01", 1, 39, "LOW", "hook", [[60, 520, 560, 1300], [430, 1000, 460, 800]]),
    ("S02", 40, 93, "CU", "build", [[180, 760, 880, 1160]]),
    ("S03", 94, 156, "TOPDOWN", "build", [[0, 520, 1080, 900]]),
    ("S04", 157, 237, "WIDE", "build", [[0, 700, 1080, 700]]),
    ("S05", 238, 285, "WIDE", "build", [[60, 920, 1000, 560]]),
    ("S06", 286, 324, "MEDIUM", "build", [[280, 460, 520, 1150]]),
    ("S07", 325, 357, "ECU", "build", [[0, 0, 1080, 1920]]),
    ("S08", 358, 402, "ECU", "build", [[60, 300, 960, 1250]]),
    ("S09", 403, 450, "MCU", "build", [[240, 520, 520, 1250]]),
    ("S10", 451, 498, "WIDE", "build", [[0, 780, 1080, 900]]),
    ("S11", 499, 531, "WIDE", "build", [[600, 820, 260, 640]]),
    ("S12", 532, 576, "WIDE", "peak", [[0, 980, 1080, 940]]),
    ("S13", 577, 600, "OTS", "payoff", [[0, 1000, 640, 920]]),
    ("S14", 601, 627, "LOW", "build", [[220, 520, 640, 1300]]),
    ("S15", 628, 660, "LOW", "loop", [[60, 520, 560, 1300]]),
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
