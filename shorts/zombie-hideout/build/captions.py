"""Part 3 captions -> audio/captions.ass + audio/text_events.json
Hook shows only "YOUR MOVE?". Choice letters A/B/C sit at the top of the HUD band so the end prompt
"A, B OR C?" makes sense in the comments. Widths are measured with the real font."""
import json
import os
import re

from PIL import ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
AUD = os.path.join(HERE, "..", "audio")
meta = json.load(open(os.path.join(AUD, "vo.json")))
VO_AT = json.load(open(os.path.join(AUD, "vo_at.json")))
HOT = {"zombies", "hunting", "waterfall.", "sound,", "roar", "freezing,", "dig", "footprints,", "stream.", "smell",
       "scent", "smoke,", "glow.", "horde", "past.", "summer's", "shrinking."}
YEL, WHT, RED, BLU = r"{\c&H00D4FF&}", r"{\c&HFFFFFF&}", r"{\c&H2A2AFF&}", r"{\c&HFFB13A&}"
HOOK_END = 45 / 30
_F = {}


def width(txt, size):
    if size not in _F:
        _F[size] = ImageFont.truetype("/usr/share/fonts/opentype/inter/InterDisplay-Black.otf", size)
    return int(_F[size].getlength(txt)) + 22


def ts(s):
    s = max(0.0, s)
    h, s = divmod(s, 3600)
    m, s = divmod(s, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def T(f):
    return (f - 1) / 30


head = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Top,Inter Display Black,96,&H00FFFFFF,&H00FFFFFF,&H00101010,&H80000000,-1,0,0,0,100,100,2,0,1,11,5,5,40,40,0,1
Style: Cap,Inter Display Black,84,&H00FFFFFF,&H00FFFFFF,&H00101010,&H80000000,-1,0,0,0,100,100,0,0,1,9,4,5,60,60,0,1
Style: Choice,Inter Display Black,72,&H00FFFFFF,&H00FFFFFF,&H00101010,&H80000000,-1,0,0,0,100,100,1,0,1,9,4,5,40,40,0,1
Style: Hud,Inter Display Black,88,&H0000D4FF,&H00FFFFFF,&H00101010,&H80000000,-1,0,0,0,100,100,1,0,1,10,5,5,40,40,0,1
Style: Label,Inter Display Black,70,&H00101010,&H00FFFFFF,&H0000D4FF,&H0000D4FF,-1,0,0,0,100,100,1,0,3,14,0,5,40,40,0,1
Style: Burst,Inter Display Black,130,&H0000E1FF,&H00FFFFFF,&H00101010,&H80000000,-1,0,0,0,100,100,2,0,1,12,6,5,40,40,0,1
Style: Stamp,Inter Display Black,420,&H002A2AFF,&H00FFFFFF,&H00FFFFFF,&H80000000,-1,0,0,0,100,100,0,0,1,14,0,5,40,40,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
POP = r"{\fscx70\fscy70\t(0,90,\fscx108\fscy108)\t(90,160,\fscx100\fscy100)}"
ev, texts = [], []


def add(layer, t0, t1, style, x, y, txt, plain, kind, size, h, pop=True, extra=""):
    ev.append(f"Dialogue: {layer},{ts(t0)},{ts(t1)},{style},,0,0,0,,{{\\pos({x},{y}){extra}}}{POP if pop else ''}{txt}")
    w = width(plain, size)
    texts.append(dict(t0=t0, t1=t1, kind=kind, text=plain, box=[x - w // 2, y - h // 2, w, h]))


# hook label (only text in shot 1)
add(2, 0.0, HOOK_END, "Top", 510, 300, "HIDE " + YEL + "HERE?", "HIDE HERE?", "overlay", 96, 110, pop=False)
# yellow build labels (like blueprint tags), one per trick
for f0, f1, txt in ((151, 206, "NOISE SHIELD"), (263, 311, "DRY ROOM"), (311, 405, "NO TRACKS"), (405, 491, "SCENT WASHED"),
                    (491, 591, "SMOKE TRAP"), (591, 656, "GLOW HIDDEN")):
    add(1, T(f0), T(f1), "Label", 510, 400, txt, txt, "hud", 70, 96)
# comic bursts
add(3, T(222), T(250), "Burst", 640, 760, "BRRR!", "BRRR!", "label", 130, 150, pop=False,
    extra=r"\fscx150\fscy150\t(0,120,\fscx100\fscy100)\frz-10")
add(3, T(690), T(712), "Burst", 380, 620, "RAAWR!", "RAAWR!", "label", 130, 150, pop=False,
    extra=r"\fscx150\fscy150\t(0,120,\fscx100\fscy100)\frz8")
# cliffhanger tag over the shrinking falls
add(2, T(757), T(856), "Top", 510, 300, "PART " + YEL + "4?", "PART 4?", "overlay", 96, 110)
# narration captions (not during the hook shot)
for m, at in zip(meta, VO_AT):
    words = m["text"].split()
    wts = [len(re.sub(r"\W", "", w)) + 2 + (5 if w.endswith((",", ".", ":", "!", "?")) else 0) for w in words]
    chunks, cur = [], []
    for w, wt in zip(words, wts):
        if cur and width(" ".join([x for x, _ in cur] + [w]).upper().strip(",.:!?"), 84) > 820:
            chunks.append(cur)
            cur = []
        cur.append((w, wt))
        if len(cur) == 3 or w.endswith((",", ".", ":", "!", "?")):
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
        if end > t_show + 0.2:
            plain = " ".join(w.upper().strip(",.:!") for w, _ in ch)
            txt = " ".join((YEL + w.upper() + WHT) if w.lower() in HOT else w.upper() for w, _ in ch)
            add(0, t_show, min(end, 28.5), "Cap", 510, 1385, txt, plain, "caption", 84, 104)
        t += d
open(os.path.join(AUD, "captions.ass"), "w").write(head + "\n".join(ev) + "\n")
json.dump(texts, open(os.path.join(AUD, "text_events.json"), "w"), indent=1)
bad = [x for x in texts if x["box"][0] < 90 or x["box"][0] + x["box"][2] > 930]
print(len(ev), "events; too wide:", [(x["text"], x["box"]) for x in bad])
for x in texts:
    print(f"{x['t0']:6.2f}-{x['t1']:6.2f} {x['kind']:8s} {x['text']}")
