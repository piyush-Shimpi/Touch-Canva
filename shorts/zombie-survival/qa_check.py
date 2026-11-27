#!/usr/bin/env python3
"""Qorvex quality gate. Usage: python3 qa_check.py final.mp4 shot_manifest.json outdir
Writes outdir/contact_phone.png (360x640 tiles), outdir/contact_safe.png (with safe-zone
guides), outdir/qa_report.json, and prints a PASS/FAIL table. Claude must still LOOK at
both contact sheets with the Read tool: the numbers catch layout bugs, not ugly art."""
import json, subprocess, sys, os
import numpy as np
from PIL import Image, ImageDraw

W, H = 1080, 1920
SAFE = dict(l=90, r=W - 150, t=230, b=H - 400)        # Shorts UI-free zone
CAPTION_BAND = (1250, 1520)                            # lower third, above UI
HUD_BAND = (230, 520)                                  # clocks, bars, gap labels
MIN_SUBJ = {"ECU": .45, "CU": .45, "MCU": .32, "MEDIUM": .28, "OTS": .28,
            "POV": .20, "LOW": .28, "WIDE": .12, "TOPDOWN": .12, "RACE": .22}

def sh(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)

def probe(v):
    r = json.loads(sh(["ffprobe", "-v", "error", "-show_streams", "-show_format",
                       "-of", "json", v]).stdout)
    vs = [s for s in r["streams"] if s["codec_type"] == "video"][0]
    num, den = map(int, vs["r_frame_rate"].split("/"))
    return dict(w=int(vs["width"]), h=int(vs["height"]), fps=round(num / den, 2),
                dur=float(r["format"]["duration"]), pix=vs.get("pix_fmt"),
                audio=any(s["codec_type"] == "audio" for s in r["streams"]))

def loudness(v):
    err = sh(["ffmpeg", "-hide_banner", "-i", v, "-af",
              "loudnorm=print_format=json", "-f", "null", "-"]).stderr
    try:
        j = json.loads(err[err.rindex("{"):err.rindex("}") + 1])
        return float(j["input_i"]), float(j["input_tp"])
    except Exception:
        return None, None

def frame(v, t):
    out = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", v,
                          "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24",
                          "-s", f"{W}x{H}", "-"], capture_output=True).stdout
    return Image.frombytes("RGB", (W, H), out)

def edge_db(v, t):
    err = sh(["ffmpeg", "-hide_banner", "-ss", f"{t:.3f}", "-t", "0.1", "-i", v,
              "-af", "astats=measure_overall=RMS_level:measure_perchannel=0",
              "-f", "null", "-"]).stderr
    try:
        return float(err.split("RMS level dB:")[-1].split()[0])
    except Exception:
        return -99.0

def overlap(a, b):
    ax, ay, aw, ah = a; bx, by, bw, bh = b
    return ax < bx + bw and bx < ax + aw and ay < by + bh and by < ay + ah

def inside(box, x0, y0, x1, y1):
    x, y, w, h = box
    return x >= x0 and y >= y0 and x + w <= x1 and y + h <= y1

def main(video, manifest, outdir):
    os.makedirs(outdir, exist_ok=True)
    m = json.load(open(manifest))
    shots = m["shots"]
    rep = {"checks": [], "shots": []}
    def chk(name, ok, detail=""):
        rep["checks"].append(dict(check=name, ok=bool(ok), detail=detail))

    p = probe(video)
    chk("size 1080x1920", (p["w"], p["h"]) == (W, H), f'{p["w"]}x{p["h"]}')
    chk("fps 30", abs(p["fps"] - 30) < .05, str(p["fps"]))
    chk("duration 20-22s (max 24)", 20 <= p["dur"] <= 24.05, f'{p["dur"]:.2f}s')
    chk("pix_fmt yuv420p", p["pix"] == "yuv420p", str(p["pix"]))
    chk("audio present", p["audio"])
    if p["audio"]:
        i, tp = loudness(video)
        chk("loudness -15..-13 LUFS", i is not None and -15 <= i <= -13, f"{i} LUFS")
        chk("true peak < -1 dBTP", tp is not None and tp < -1, f"{tp} dBTP")
        h, t = edge_db(video, 0.0), edge_db(video, max(p["dur"] - 0.1, 0))
        chk("sound at frame 0 and at the end (> -40 dB)", h > -40 and t > -40,
            f"start {h:.0f} dB, end {t:.0f} dB")
    nar = m.get("narration")
    if nar:
        gap = nar["first_word_start"] + max(p["dur"] - nar["last_word_end"], 0)
        chk("audio loop pause < 0.1s", gap < 0.1, f"{gap:.2f}s")
    else:
        chk("narration timing in manifest", False, "add narration.first_word_start/last_word_end")

    # pacing
    durs = [s["end"] - s["start"] for s in shots]
    chk("first shot starts at 0.0 and <= 1.5s (hook)",
        shots[0]["start"] == 0 and durs[0] <= 1.5, f"{durs[0]:.2f}s")
    long_ = [s["id"] for s, d in zip(shots, durs) if d > 2.0]
    chk("no shot > 2.0s", not long_, ",".join(long_))
    chk("shot count 10-16", 10 <= len(shots) <= 16, str(len(shots)))
    hook_texts = shots[0].get("texts", [])
    chk("hook shows one text element", len(hook_texts) <= 1, str(len(hook_texts)))
    peaks = [s for s in shots if s.get("beat") == "peak"]
    if peaks:
        pt = peaks[0]["start"] / p["dur"]
        chk("peak at 70-80%", .68 <= pt <= .82, f"{pt:.0%}")
    else:
        chk("peak beat marked", False, "no shot has beat=peak")

    # per-shot layout
    allwords = set()
    for s in shots:
        issues = []
        typ = s.get("type", "MEDIUM").upper()
        subs = s.get("subjects", [])
        if subs:
            big = max(max(b[2] / W, b[3] / H) for b in subs)
            if big < MIN_SUBJ.get(typ, .25):
                issues.append(f"subject too small {big:.0%} < {MIN_SUBJ.get(typ,.25):.0%}")
        texts = s.get("texts", [])
        for t in texts:
            b = t["box"]
            if not inside(b, SAFE["l"], SAFE["t"], SAFE["r"], SAFE["b"]):
                issues.append(f'{t["kind"]} outside safe zone')
            if t["kind"] == "caption" and not inside(b, 0, CAPTION_BAND[0], W, CAPTION_BAND[1]):
                issues.append("caption outside lower-third band")
            if t["kind"] == "caption" and b[3] < 80:
                issues.append("caption text too small (<80px box)")
            words = t.get("text", "").split()
            if t["kind"] in ("caption", "label", "overlay") and len(words) > 3:
                issues.append(f'{t["kind"]} has {len(words)} words (max 3)')
            if "\n" in t.get("text", ""):
                issues.append(f'{t["kind"]} is stacked on several lines')
            allwords.update(w.strip(".,!?:;\"'()").upper() for w in words)
            for sb in subs:
                if overlap(b, sb) and t["kind"] != "label":
                    issues.append(f'{t["kind"]} covers subject')
        for a in range(len(texts)):
            for c in range(a + 1, len(texts)):
                if overlap(texts[a]["box"], texts[c]["box"]):
                    issues.append(f'{texts[a]["kind"]} overlaps {texts[c]["kind"]}')
        rep["shots"].append(dict(id=s["id"], issues=issues))
    rep["onscreen_words"] = sorted(w for w in allwords if w and not w[0].isdigit())
    bad = [s["id"] for s in rep["shots"] if s["issues"]]
    chk("layout: no tiny/cropped/overlapping", not bad, ",".join(bad))

    # frames: hook times + each shot midpoint + last frame
    times = [("hook0.0", 0.0), ("hook0.5", .5), ("hook1.0", 1.0), ("hook2.0", 2.0)]
    times += [(s["id"], (s["start"] + s["end"]) / 2) for s in shots]
    times += [("LAST", max(p["dur"] - 0.05, 0))]
    tiles, lumas = [], {}
    for name, t in times:
        f = frame(video, t)
        lumas[name] = float(np.asarray(f.convert("L")).mean())
        tiles.append((name, f))
    dark = [n for n, l in lumas.items() if l < 75]
    chk("bright scenes (mean luma >= 75)", not dark, ",".join(dark))

    a = np.asarray(tiles[0][1].convert("L").resize((108, 192)), float)
    z = np.asarray(tiles[-1][1].convert("L").resize((108, 192)), float)
    diff = float(np.abs(a - z).mean())
    chk("loop: last frame ~ first frame (diff < 18)", diff < 18, f"{diff:.1f}")

    def sheet(guides):
        tw, th, cols = 360, 640, 4
        rows = -(-len(tiles) // cols)
        S = Image.new("RGB", (cols * tw, rows * (th + 28)), "white")
        d = ImageDraw.Draw(S)
        for k, (name, f) in enumerate(tiles):
            g = f.copy()
            if guides:
                gd = ImageDraw.Draw(g)
                gd.rectangle([SAFE["l"], SAFE["t"], SAFE["r"], SAFE["b"]], outline="red", width=6)
                gd.rectangle([0, CAPTION_BAND[0], W, CAPTION_BAND[1]], outline="yellow", width=6)
                gd.rectangle([0, HUD_BAND[0], W, HUD_BAND[1]], outline="cyan", width=6)
            x, y = (k % cols) * tw, (k // cols) * (th + 28)
            S.paste(g.resize((tw, th)), (x, y + 28))
            d.text((x + 6, y + 6), name, fill="black")
        return S
    sheet(False).save(f"{outdir}/contact_phone.png")
    sheet(True).save(f"{outdir}/contact_safe.png")

    rep["pass"] = all(c["ok"] for c in rep["checks"])
    json.dump(rep, open(f"{outdir}/qa_report.json", "w"), indent=2)
    for c in rep["checks"]:
        print(("PASS " if c["ok"] else "FAIL ") + c["check"] + (f"  [{c['detail']}]" if c["detail"] else ""))
    for s in rep["shots"]:
        for i in s["issues"]:
            print(f"  {s['id']}: {i}")
    print("ON-SCREEN WORDS (proofread):", " ".join(rep["onscreen_words"]))
    print("OVERALL", "PASS" if rep["pass"] else "FAIL")

if __name__ == "__main__":
    main(*sys.argv[1:4])
