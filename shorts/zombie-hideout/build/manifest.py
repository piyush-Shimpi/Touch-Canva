"""shot_manifest.json for the QA gate. Subject boxes are hand-measured from the 1080x1920 test frames
(approximate, mid-shot); text boxes come from captions.py."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
texts = json.load(open(os.path.join(HERE, "..", "audio", "text_events.json")))
vo = json.load(open(os.path.join(HERE, "..", "audio", "vo.json")))
at = json.load(open(os.path.join(HERE, "..", "audio", "vo_at.json")))
S = [  # id, out frames, type, beat, subject boxes [x, y, w, h] (approx; re-measured on the QA sheet)
    ("S01", 1, 45, "WIDE", "hook", [[620, 660, 300, 300]]),
    ("S02", 46, 103, "MEDIUM", "build", [[200, 450, 650, 1050]]),
    ("S03", 104, 150, "CU", "build", [[300, 500, 450, 900]]),
    ("S04", 151, 205, "WIDE", "build", [[600, 650, 300, 350]]),
    ("S05", 206, 262, "MEDIUM", "build", [[150, 600, 700, 500]]),
    ("S06", 263, 310, "MEDIUM", "build", [[150, 600, 600, 700]]),
    ("S07", 311, 360, "MEDIUM", "build", [[250, 500, 500, 750]]),
    ("S08", 361, 404, "CU", "build", [[150, 480, 750, 900]]),
    ("S09", 405, 450, "MEDIUM", "build", [[100, 800, 700, 400]]),
    ("S10", 451, 490, "MEDIUM", "build", [[500, 450, 450, 700]]),
    ("S11", 491, 540, "MEDIUM", "build", [[350, 800, 500, 500]]),
    ("S12", 541, 590, "CU", "build", [[100, 500, 600, 500]]),
    ("S13", 591, 655, "WIDE", "build", [[550, 700, 300, 300]]),
    ("S14", 656, 712, "MEDIUM", "peak", [[0, 500, 650, 1000]]),
    ("S15", 713, 756, "WIDE", "build", [[0, 650, 450, 350]]),
    ("S16", 757, 805, "WIDE", "payoff", [[450, 500, 400, 600]]),
    ("S17", 806, 855, "MEDIUM", "loop", [[250, 450, 650, 1050]]),
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
