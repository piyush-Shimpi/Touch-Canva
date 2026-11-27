"""Captions (ASS) for the zombie short -> audio/captions.ass + audio/text_events.json (for the QA manifest)
Rules: hook shot shows only the top label; captions 1-3 words, one line, lower third (y 1385), key words yellow;
HUD band y 300-420."""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
AUD = os.path.join(HERE, "..", "audio")
meta = json.load(open(os.path.join(AUD, "vo.json")))
VO_AT = json.load(open(os.path.join(AUD, "vo_at.json")))
HOT = {"zombie", "real", "cornell", "307", "million", "cities", "days.", "get", "out.", "gallon", "hills.", "months",
       "rockies.", "longest"}
YEL, WHT = r"{\c&H00D4FF&}", r"{\c&HFFFFFF&}"
HOOK_END = 39 / 30


def ts(s):
    s = max(0.0, s)
    h, s = divmod(s, 3600)
    m, s = divmod(s, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


head = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Top,Inter Display Black,108,&H00FFFFFF,&H00FFFFFF,&H00101010,&H80000000,-1,0,0,0,100,100,2,0,1,11,5,5,40,40,0,1
Style: Cap,Inter Display Black,92,&H00FFFFFF,&H00FFFFFF,&H00101010,&H80000000,-1,0,0,0,100,100,0,0,1,9,4,5,60,60,0,1
Style: Hud,Inter Display Black,104,&H0000D4FF,&H00FFFFFF,&H00101010,&H80000000,-1,0,0,0,100,100,1,0,1,10,5,5,40,40,0,1
Style: Label,Inter Display Black,80,&H006AFF2B,&H00FFFFFF,&H00101010,&H80000000,-1,0,0,0,100,100,1,0,1,9,4,5,40,40,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
POP = r"{\fscx70\fscy70\t(0,90,\fscx108\fscy108)\t(90,160,\fscx100\fscy100)}"
ev, texts = [], []


def add(layer, t0, t1, style, x, y, txt, plain, kind, w, h, pop=True):
    ev.append(f"Dialogue: {layer},{ts(t0)},{ts(t1)},{style},,0,0,0,,{{\\pos({x},{y})}}{POP if pop else ''}{txt}")
    texts.append(dict(t0=t0, t1=t1, kind=kind, text=plain, box=[x - w // 2, y - h // 2, w, h]))


def width(txt, size):
    return int(len(txt) * size * 0.62)


# hook label (the only text in shot 1)
add(2, 0.0, HOOK_END, "Top", 510, 250, "ZOMBIE " + YEL + "OUTBREAK", "ZOMBIE OUTBREAK", "overlay", width("ZOMBIE OUTBREAK", 108), 120, pop=False)
# narration captions
for m, at in zip(meta, VO_AT):
    words = m["text"].split()
    wts = [len(re.sub(r"\W", "", w)) + 2 + (5 if w.endswith((",", ".", ":", "!")) else 0) for w in words]
    chunks, cur = [], []
    for w, wt in zip(words, wts):
        cur.append((w, wt))
        if len(cur) == 3 or w.endswith((",", ".", ":", "!")) or (len(cur) == 2 and len(w) > 8):
            chunks.append(cur)
            cur = []
    if cur:
        chunks.append(cur)
    total, dur = sum(wts), m["dur"] - 0.1
    t = at + 0.03
    for i, ch in enumerate(chunks):
        d = sum(wt for _, wt in ch) / total * dur
        end = t + d if i < len(chunks) - 1 else at + m["dur"] + 0.08
        t_show = max(t, HOOK_END) if at < HOOK_END else t
        if end > t_show + 0.05:
            plain = " ".join(w.upper().strip(",.:!") for w, _ in ch)
            txt = " ".join((YEL + w.upper() + WHT) if w.lower() in HOT else w.upper() for w, _ in ch)
            add(0, t_show, min(end, 22.0), "Cap", 510, 1385, txt, plain, "caption", width(plain, 92), 110)
        t += d


def T(f):
    return (f - 1) / 30


# HUD band
add(1, T(94), T(238), "Hud", 510, 360, "CORNELL SIM", "CORNELL SIM", "hud", width("CORNELL SIM", 104), 120)
add(1, T(250), T(286), "Hud", 510, 360, "DAY 3", "DAY 3", "hud", width("DAY 3", 104), 120)
add(1, T(366), T(403), "Hud", 510, 360, "1 GALLON/DAY", "1 GALLON/DAY", "hud", width("1 GALLON/DAY", 104), 120)
add(1, T(550), T(577), "Hud", 510, 360, "MONTH 4 (EST.)", "MONTH 4 (EST.)", "hud", width("MONTH 4 (EST.)", 104), 120)
add(1, T(553), T(577), "Label", 510, 820, "SAFEST", "SAFEST", "label", width("SAFEST", 80), 96)
open(os.path.join(AUD, "captions.ass"), "w").write(head + "\n".join(ev) + "\n")
json.dump(texts, open(os.path.join(AUD, "text_events.json"), "w"), indent=1)
print(len(ev), "events")
for x in texts:
    print(f"{x['t0']:6.2f}-{x['t1']:6.2f} {x['kind']:8s} {x['text']}")
