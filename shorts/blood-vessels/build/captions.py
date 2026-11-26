"""Word-chunk pop captions (ASS) timed from the narration line starts + durations -> audio/captions.ass"""
import json, os, re
HERE = os.path.dirname(os.path.abspath(__file__))
AUD = os.path.join(HERE, "..", "audio")
HOT = {"slice", "blood", "vessels.", "every", "end.", "line,", "hundred", "thousand", "kilometers!", "earth", "two", "half", "times!", "heart", "you."}
YEL = r"{\c&H3FD2FF&}"   # BGR for #FFD23F
meta = json.load(open(os.path.join(AUD, "vo.json")))
VO_AT, _t = [], 0.7                                   # same placement as audio.py (0.08 s gaps)
for _m in meta:
    VO_AT.append(_t)
    _t += _m["dur"] + 0.08
FPS, END = 30, 657
DUR = END / FPS


def T(f):
    return (f - 1) / FPS


def ts(s):
    h, s = divmod(s, 3600); m, s = divmod(s, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


head = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Inter Display Black,92,&H00FFFFFF,&H00FFFFFF,&H00101010,&H80000000,-1,0,0,0,100,100,0,0,1,9,4,5,60,60,0,1
Style: Badge,Inter Display Black,150,&H003FD2FF,&H00FFFFFF,&H00101010,&H80000000,-1,0,0,0,100,100,0,0,1,12,6,5,40,40,0,1
Style: Top,Inter Display Black,138,&H00FFFFFF,&H00FFFFFF,&H00101010,&H80000000,-1,0,0,0,100,100,2,0,1,11,5,5,40,40,0,1
Style: Small,Inter Display ExtraBold,58,&H00FFFFFF,&H00FFFFFF,&H00101010,&H80000000,-1,0,0,0,100,100,0,0,1,6,3,5,40,40,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
ev = []
POP = r"{\fscx70\fscy70\t(0,90,\fscx108\fscy108)\t(90,160,\fscx100\fscy100)}"
for m, at in zip(meta, VO_AT):
    words = m["text"].replace("...", "…").split()
    weights = [len(re.sub(r"\W", "", w)) + 2 + (6 if w.endswith((",", ".", "…", "?")) else 0) for w in words]
    total, dur = sum(weights), m["dur"] - 0.15
    chunks, cur = [], []
    for w, wt in zip(words, weights):
        cur.append((w, wt))
        if len(cur) == 3 or w.endswith((",", ".", "…", "?")) or (len(cur) == 2 and len(w) > 7):
            chunks.append(cur); cur = []
    if cur:
        chunks.append(cur)
    t = at + 0.05
    for i, ch in enumerate(chunks):
        d = sum(wt for _, wt in ch) / total * dur
        end = t + d if i < len(chunks) - 1 else at + m["dur"] + 0.06
        txt = " ".join((YEL + w.upper() + r"{\c&HFFFFFF&}") if re.sub(r"\W", "", w).lower() in HOT else w.upper()
                       for w, _ in ch)
        ev.append(f"Dialogue: 0,{ts(t)},{ts(end)},Cap,,0,0,0,,{{\\pos(540,1330)}}{POP}{txt}")
        t += d
# top text
TOPPOP = r"{\fscx60\fscy60\t(0,110,\fscx110\fscy110)\t(110,190,\fscx100\fscy100)}"
ev.append(f"Dialogue: 2,{ts(0)},{ts(T(23))},Top,,0,0,0,,{{\\pos(540,330)}}{TOPPOP}INSIDE {YEL}YOU")
ev.append(f"Dialogue: 2,{ts(T(141))},{ts(T(230))},Top,,0,0,0,,{{\\pos(540,330)}}{TOPPOP}HOW {YEL}LONG?")
# km counter while the line races (frames 261-383)
F0, F1 = 261, 383
for f in range(F0, F1 + 1, 2):
    u = (f - F0) / (F1 - F0)
    km = 10 ** (-2 + 7 * u ** 1.25)
    txt = f"{km:,.2f} KM" if km < 10 else f"{km:,.0f} KM"
    if f >= F1 - 3:
        txt = "100,000 KM"
    end = T(f + 2) if f < F1 - 1 else T(F1 + 1)
    ev.append(f"Dialogue: 1,{ts(T(f))},{ts(end)},Badge,,0,0,0,,{{\\pos(540,420)\\fs120}}{txt}")
W0, W1 = 392, 481
def frac(f):
    k = max(0.0, min(1.0, (f - W0) / (W1 - W0)))
    return k * k * (3 - 2 * k) * 0.25 + k * 0.75
marks = []
for target in (0.4, 0.8, 1.0):
    f = W0
    while frac(f) < target - 1e-6 and f < W1:
        f += 0.25
    marks.append(T(f))
OUT = T(606)
for i, (t0, lab) in enumerate(zip(marks, ["×1", "×2", "×2.5"])):
    t1 = marks[i + 1] if i + 1 < len(marks) else OUT
    ev.append(f"Dialogue: 1,{ts(t0)},{ts(t1)},Badge,,0,0,0,,{{\\pos(540,330)\\fscx40\\fscy40\\t(0,140,\\fscx115\\fscy115)\\t(140,240,\\fscx100\\fscy100)}}{lab}")
ev.append(f"Dialogue: 1,{ts(marks[-1] + 0.1)},{ts(OUT)},Small,,0,0,0,,{{\\pos(540,470)\\alpha&HFF&\\t(0,250,\\alpha&H00&)}}AROUND THE EARTH")
open(os.path.join(AUD, "captions.ass"), "w").write(head + "\n".join(ev) + "\n")
print(len(ev), "events")
