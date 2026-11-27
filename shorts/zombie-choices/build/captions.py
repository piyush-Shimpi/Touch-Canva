"""Part 2 captions -> audio/captions.ass + audio/text_events.json
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
HOT = {"zombies", "stay", "home?", "three", "days.", "weeks", "weak", "dig", "bunker?", "day", "slow.", "water",
       "first.", "done.", "pick,"}
YEL, WHT, RED, BLU = r"{\c&H00D4FF&}", r"{\c&HFFFFFF&}", r"{\c&H2A2AFF&}", r"{\c&HFFB13A&}"
HOOK_END = 39 / 30
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


# hook label (only text in shot 1), then the three options
add(2, 0.0, HOOK_END, "Top", 510, 300, "YOUR " + YEL + "MOVE?", "YOUR MOVE?", "overlay", 96, 110, pop=False)
add(1, HOOK_END, T(76), "Choice", 510, 255, "STAY · DIG · " + YEL + "?", "STAY · DIG · ?", "hud", 72, 90)
# choice letters (top row of the HUD band)
add(1, T(76), T(259), "Choice", 510, 255, YEL + "A" + WHT + " · STAY HOME", "A · STAY HOME", "hud", 72, 90)
add(1, T(259), T(388), "Choice", 510, 255, YEL + "B" + WHT + " · DIG", "B · DIG", "hud", 72, 90)
add(1, T(388), T(517), "Choice", 510, 255, YEL + "C" + WHT + " · " + BLU + "WATER", "C · WATER", "hud", 72, 90)
# data HUD (second row)
add(1, T(125), T(169), "Hud", 510, 380, "~3 DAYS", "~3 DAYS", "hud", 88, 104)
add(1, T(180), T(217), "Hud", 510, 380, "DAY 21", "DAY 21", "hud", 88, 104)
add(1, T(305), T(337), "Hud", 510, 380, "~1 DAY PER M³", "~1 DAY PER M³", "hud", 88, 104)
add(1, T(440), T(475), "Hud", 510, 380, BLU + "3 DAYS" + WHT + " MAX", "3 DAYS MAX", "hud", 88, 104)
# red ✗ stamps on the wrong choices
for f0, f1 in ((222, 259), (375, 388)):
    add(3, T(f0), T(f1), "Stamp", 540, 880, "✗", "✗", "label", 420, 420, pop=False,
        extra=r"\fscx160\fscy160\t(0,110,\fscx100\fscy100)\frz-8")
# end prompt while the question line plays (it loops straight back into the hook)
add(2, T(617), 22.0, "Top", 510, 300, YEL + "A" + WHT + ", " + YEL + "B" + WHT + " OR " + YEL + "C" + WHT + "?", "A, B OR C?", "overlay", 96, 110)
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
            add(0, t_show, min(end, 22.0), "Cap", 510, 1385, txt, plain, "caption", 84, 104)
        t += d
open(os.path.join(AUD, "captions.ass"), "w").write(head + "\n".join(ev) + "\n")
json.dump(texts, open(os.path.join(AUD, "text_events.json"), "w"), indent=1)
bad = [x for x in texts if x["box"][0] < 90 or x["box"][0] + x["box"][2] > 930]
print(len(ev), "events; too wide:", [(x["text"], x["box"]) for x in bad])
for x in texts:
    print(f"{x['t0']:6.2f}-{x['t1']:6.2f} {x['kind']:8s} {x['text']}")
