"""Word-chunk pop captions (ASS) timed from the narration line starts + durations -> audio/captions.ass"""
import json, os, re
HERE = os.path.dirname(os.path.abspath(__file__))
AUD = os.path.join(HERE, "..", "audio")
VO_AT = [0.35, 3.6, 8.2, 14.7, 19.3]
HOT = {"penny", "skyscraper", "bullet", "flat", "light", "flip", "flutter", "forty", "kilometers", "sting"}
YEL = r"{\c&H3FD2FF&}"   # BGR for #FFD23F
meta = json.load(open(os.path.join(AUD, "vo.json")))


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
        end = t + d if i < len(chunks) - 1 else at + m["dur"] + 0.25
        txt = " ".join((YEL + w.upper() + r"{\c&HFFFFFF&}") if re.sub(r"\W", "", w).lower() in HOT else w.upper()
                       for w, _ in ch)
        ev.append(f"Dialogue: 0,{ts(t)},{ts(end)},Cap,,0,0,0,,{{\\pos(540,1330)}}{POP}{txt}")
        t += d
# speed badge during the wide drift shot
ev.append(r"Dialogue: 1,0:00:15.20,0:00:18.90,Badge,,0,0,0,,{\pos(540,420)\fscx40\fscy40\t(0,140,\fscx110\fscy110)\t(140,240,\fscx100\fscy100)}≈ 40 KM/H")
ev.append(r"Dialogue: 1,0:00:15.45,0:00:18.90,Small,,0,0,0,,{\pos(540,560)\alpha&HFF&\t(0,200,\alpha&H00&)}TERMINAL VELOCITY")
open(os.path.join(AUD, "captions.ass"), "w").write(head + "\n".join(ev) + "\n")
print(len(ev), "events")
