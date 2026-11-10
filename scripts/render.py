#!/usr/bin/env python3
"""Snapshot every kit-gallery scene and a few rune-kit examples, light and dark, to WebP.

usage: render.py <rune checkout> <out dir>
"""
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageChops

RUNE, OUT = Path(sys.argv[1]), Path(sys.argv[2])
BIN = RUNE / "target/release"
SCALE = 2
TALL = 2400  # points; scenes are trimmed to their content afterwards
PAD = 24 * SCALE
# Scenes that fill the window (scrims, regions pinned to an edge): fixed height, no trim.
FIXED = {
    "ui-dialog--basic": 480,
    "rune-dialog--fit": 480,
    "motion-focus-modal": 480,
    "ui-toast--all-examples": 480,
}
# rune-kit examples: (name, scenes or [None] for the default).
EXAMPLES = [
    ("diff", None),
    ("table", [None]),
    ("tree", [None]),
    ("shell", [None]),
    ("tab_strip", None),
    ("shortcut_recorder", [None]),
    ("rich_editor", [None]),
    ("glyphs", [None]),
]


def run(cmd):
    return subprocess.run([str(c) for c in cmd], capture_output=True, text=True, timeout=300)


def scenes(binary):
    r = run([binary, "--list-scenes"])
    return r.stdout.split() if r.returncode == 0 else []


def trim(img):
    """Crops to the content's bottom edge (plus padding); keeps the full width."""
    rgb = img.convert("RGB")
    bg = Image.new("RGB", rgb.size, rgb.getpixel((2, rgb.height - 3)))
    box = ImageChops.difference(rgb, bg).getbbox()
    if not box:
        return img.crop((0, 0, img.width, 200))
    return img.crop((0, 0, img.width, min(img.height, box[3] + PAD)))


def shot(binary, scene, theme, size, dest, crop):
    png = dest.with_suffix(".png")
    cmd = [binary, "--snap", png, "--theme", theme, "--scale", SCALE]
    if scene:
        cmd += ["--scene", scene]
    if size:
        cmd += ["--size", size]
    r = run(cmd)
    if r.returncode != 0 or not png.exists():
        return {"error": (r.stderr or r.stdout)[-600:]}
    img = Image.open(png)
    full = img.height
    if crop:
        img = trim(img)
    img.save(dest, "WEBP", quality=90, method=6)
    png.unlink()
    return {"w": img.width, "h": img.height, "clipped": crop and img.height >= full}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = []
    gallery = BIN / "kit-gallery"
    for kit in ["opencode", "neutral"]:
        for scene in scenes(gallery):
            if scene == "index":
                continue
            # The neutral theme: one overview per scene would double the set; keep a sample.
            if kit == "neutral" and not scene.endswith(("--variants", "--all-states", "--states", "--appearances", "--rich", "--grouped", "--all-examples", "--basic")):
                continue
            for theme in ["light", "dark"]:
                h = FIXED.get(scene)
                dest = OUT / f"{scene}.{kit}.{theme}.webp"
                cmd_extra = [] if kit == "opencode" else ["--kit", "neutral"]
                png = dest.with_suffix(".png")
                cmd = [gallery, "--scene", scene, "--snap", png, "--theme", theme, "--scale", SCALE,
                       "--size", f"720x{h or TALL}"] + cmd_extra
                r = run(cmd)
                entry = {"id": scene, "kit": kit, "theme": theme, "file": dest.name}
                if r.returncode != 0 or not png.exists():
                    entry["error"] = (r.stderr or r.stdout)[-600:]
                else:
                    img = Image.open(png)
                    full = img.height
                    if not h:
                        img = trim(img)
                    img.save(dest, "WEBP", quality=90, method=6)
                    png.unlink()
                    entry.update(w=img.width, h=img.height, clipped=(not h and img.height >= full))
                manifest.append(entry)
                print(entry, flush=True)
    for name, wanted in EXAMPLES:
        binary = BIN / "examples" / name
        if not binary.exists():
            manifest.append({"id": f"example-{name}", "error": "not built"})
            continue
        for scene in (wanted or scenes(binary) or [None]):
            for theme in ["light", "dark"]:
                sid = f"example-{name}" + (f"--{scene}" if scene else "")
                dest = OUT / f"{sid}.opencode.{theme}.webp"
                entry = {"id": sid, "kit": "example", "theme": theme, "file": dest.name}
                entry.update(shot(binary, scene, theme, None, dest, False))
                manifest.append(entry)
                print(entry, flush=True)
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=1))
    bad = [m for m in manifest if "error" in m]
    print(f"{len(manifest) - len(bad)} rendered, {len(bad)} failed")


main()
