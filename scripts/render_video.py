#!/usr/bin/env python3
"""Records Rune's motion: the showreel scenes, scripted kit interactions, the effects lab and a
few example apps, headlessly, then shrinks each clip for the web.

usage: render_video.py <rune checkout> <out dir>
"""
import json
import subprocess
import sys
import time
from pathlib import Path

RUNE, OUT = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
BIN = RUNE / "target/release"
EX = RUNE / "examples"

# (id, group, binary, args, seconds or "auto")
CLIPS = []
for s in ["word", "card", "type", "deploy", "pricing", "ask", "tabs", "keys", "glass", "fire", "shock"]:
    CLIPS.append((f"showreel-{s}", "showreel", "showreel", ["--scene", s, "--size", "960x540", "--scale", "2"], 6))
G = EX / "kit-gallery/scripts"
for script, scene, size in [
    ("combobox", "rune-combobox--searchable", "720x440"),
    ("combobox-animated-filter", "rune-combobox--animated-filter", "720x440"),
    ("help-tooltip", "rune-text--selectable-help", "720x320"),
    ("selectable-text", "rune-text--selectable-help", "720x320"),
    ("motion-focus-modal", "motion-focus-modal", "720x480"),
    ("motion-stagger-list", "motion-stagger-list", "720x480"),
]:
    CLIPS.append((f"kit-{script}", "kit", "kit-gallery", ["--scene", scene, "--script", G / f"{script}.json", "--size", size,
                                                          "--scale", "2", "--theme", "dark", "--pointer"], "auto"))
L = EX / "lab/scripts"
for s in ["lamp", "flashlight", "keys", "pulses", "electric", "motion", "lens"]:
    CLIPS.append((f"lab-{s}", "lab", "lab", ["--scene", s, "--script", L / f"{s}.json", "--scale", "1", "--pointer"], "auto"))
for s in ["gi", "godrays", "glow", "fire"]:
    CLIPS.append((f"lab-{s}", "lab", "lab", ["--scene", s, "--scale", "1"], 5))
S = EX / "settings/scripts"
for s, extra in [("demo", ["--pointer"]), ("toggle", ["--pointer"]), ("slider", ["--pointer"]), ("keycaps", ["--pointer", "--keys"])]:
    CLIPS.append((f"settings-{s}", "apps", "settings", ["--script", S / f"{s}.json", "--scale", "2", "--theme", "dark"] + extra, "auto"))
CLIPS.append(("matched-zoom", "apps", "matched", ["--script", EX / "matched/scripts/zoom.json", "--scale", "2", "--pointer"], "auto"))
CLIPS.append(("cursed-settings", "apps", "cursed-settings", ["--script", EX / "cursed-settings/scripts/showcase.json", "--scale", "2", "--pointer"], "auto"))
CLIPS.append(("motion-bento", "apps", "motion-bento", ["--seed", "7", "--duration", "8", "--scale", "1"], None))


def run(cmd, timeout):
    try:
        return subprocess.run([str(c) for c in cmd], capture_output=True, text=True, timeout=timeout, cwd=RUNE)
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(cmd, 124, "", "timed out")


def probe(path):
    r = run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height:format=duration",
             "-of", "json", path], 60)
    j = json.loads(r.stdout)
    return j["streams"][0]["width"], j["streams"][0]["height"], float(j["format"]["duration"])


def shrink(raw, dest, audio=False):
    """H.264 at most 1280 wide, web-playable, plus a poster frame."""
    vf = "scale='min(1280,iw)':-2:flags=lanczos,format=yuv420p"
    a = ["-c:a", "aac", "-b:a", "96k"] if audio else ["-an"]
    r = run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-vf", vf, "-c:v", "libx264", "-preset", "slow", "-crf", "27",
             "-movflags", "+faststart"] + a + [dest], 900)
    if r.returncode != 0:
        return {"error": r.stderr[-400:]}
    w, h, d = probe(dest)
    run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{d * 0.55:.2f}", "-i", dest, "-frames:v", "1", "-q:v", "70",
         dest.with_suffix(".webp")], 120)
    return {"w": w, "h": h, "dur": round(d, 2), "kb": dest.stat().st_size // 1024}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = []
    reel = RUNE / "demo/rune.mp4"
    if reel.exists():
        e = {"id": "rune-reel", "group": "reel", "file": "rune-reel.mp4"}
        e.update(shrink(reel, OUT / "rune-reel.mp4", audio=True))
        manifest.append(e)
        print(e, flush=True)
    for cid, group, binary, args, dur in CLIPS:
        raw = OUT / f"{cid}.raw.mp4"
        cmd = [BIN / binary] + args + ["--video", raw, "--fps", "60"]
        if dur is not None:
            cmd += ["--duration", dur]
        t = time.time()
        r = run(cmd, 900)
        e = {"id": cid, "group": group, "file": f"{cid}.mp4", "cmd": " ".join(str(c).replace(str(RUNE) + "/", "") for c in cmd[1:-4])}
        if r.returncode != 0 or not raw.exists():
            e["error"] = (r.stderr or r.stdout)[-600:]
        else:
            e.update(shrink(raw, OUT / f"{cid}.mp4"))
        raw.unlink(missing_ok=True)
        e["secs"] = round(time.time() - t)
        manifest.append(e)
        print(e, flush=True)
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=1))
    print(sum("error" not in m for m in manifest), "clips,", sum("error" in m for m in manifest), "failed")


main()
