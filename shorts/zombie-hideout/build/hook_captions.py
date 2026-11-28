"""Hook-test captions: 'BEHIND THE WATERFALL' label in shot 1 only, narration chunks from shot 2."""
import json, re
meta = json.load(open("audio/vo.json"))
YEL, WHT = r"{\c&H00D4FF&}", r"{\c&HFFFFFF&}"
HOT = {"zombies", "hunting", "hide", "waterfall."}
def ts(s):
    m, s = divmod(max(0.0, s), 60); return f"0:{int(m):02d}:{s:05.2f}"
head = open("../zombie-choices/build/captions.py").read().split('head = """')[1].split('"""')[0]
POP = r"{\fscx70\fscy70\t(0,90,\fscx108\fscy108)\t(90,160,\fscx100\fscy100)}"
ev = [f"Dialogue: 2,{ts(0)},{ts(1.5)},Top,,0,0,0,,{{\\pos(510,300)}}HIDE " + YEL + "HERE?"]
words = meta[0]["text"].split()
wts = [len(re.sub(r"\W", "", w)) + 2 + (5 if w[-1] in ",.!?" else 0) for w in words]
chunks, cur = [], []
for w, wt in zip(words, wts):
    cur.append((w, wt))
    if len(cur) == 3 or w[-1] in ",.!?":
        chunks.append(cur); cur = []
if cur: chunks.append(cur)
t, dur, tot = 0.08, meta[0]["dur"] - 0.1, sum(wts)
for i, ch in enumerate(chunks):
    d = sum(x for _, x in ch) / tot * dur
    t0, t1 = max(t, 1.5), (t + d if i < len(chunks) - 1 else 103 / 30)
    if t1 > t0 + 0.2:
        txt = " ".join((YEL + w.upper() + WHT) if w.lower() in HOT else w.upper() for w, _ in ch).replace(",", "").replace(".", "")
        ev.append(f"Dialogue: 0,{ts(t0)},{ts(t1)},Cap,,0,0,0,,{{\\pos(510,1385)}}{POP}{txt}")
    t += d
open("audio/hook.ass", "w").write(head + "\n".join(ev) + "\n")
print("\n".join(ev))
