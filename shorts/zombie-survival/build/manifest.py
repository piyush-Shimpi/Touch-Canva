"""shot_manifest.json for the QA gate. Subject boxes are hand-measured from the 1080x1920 test frames
(approximate, mid-shot); text boxes come from captions.py."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
texts = json.load(open(os.path.join(HERE, "..", "audio", "text_events.json")))
vo = json.load(open(os.path.join(HERE, "..", "audio", "vo.json")))
at = json.load(open(os.path.join(HERE, "..", "audio", "vo_at.json")))
S = [  # id, out frames, type, beat, subject boxes [x, y, w, h]: faces / key action, measured on the 1080x1920 QA sheet
    ("S01", 1, 39, "LOW", "hook", [[60, 280, 500, 760], [330, 900, 450, 560]]),
    ("S02", 40, 93, "CU", "build", [[300, 480, 560, 700]]),
    ("S03", 94, 153, "TOPDOWN", "build", [[0, 560, 1080, 660]]),
    ("S04", 154, 196, "WIDE", "build", [[0, 640, 1080, 580]]),
    ("S05", 197, 237, "WIDE", "build", [[0, 640, 1080, 600]]),
    ("S06", 238, 285, "WIDE", "build", [[40, 760, 1000, 480]]),
    ("S07", 286, 324, "MEDIUM", "build", [[300, 280, 450, 940]]),
    ("S08", 325, 357, "ECU", "build", [[150, 240, 780, 1000]]),
    ("S09", 358, 402, "ECU", "build", [[150, 300, 780, 900]]),
    ("S10", 403, 450, "MCU", "build", [[300, 500, 420, 740]]),
    ("S11", 451, 498, "WIDE", "build", [[0, 480, 1080, 740]]),
    ("S12", 499, 531, "WIDE", "build", [[480, 760, 260, 470]]),
    ("S13", 532, 576, "WIDE", "peak", [[0, 560, 1080, 660]]),
    ("S14", 577, 600, "OTS", "payoff", [[0, 1150, 640, 600]]),
    ("S15", 601, 627, "LOW", "build", [[220, 450, 640, 1060]]),
    ("S16", 628, 660, "LOW", "loop", [[60, 280, 500, 760], [330, 700, 450, 540]]),
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
