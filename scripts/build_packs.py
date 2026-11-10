#!/usr/bin/env python3
"""Bundles the renders into one JSON pack per component (file -> base64 WebP) and a thumbnail
pack for the home grid.   usage: build_packs.py <site dir>   (needs ImageMagick's `magick`)"""
import base64
import json
import subprocess
import sys
from pathlib import Path

SITE = Path(sys.argv[1])
data = json.loads((SITE / "data.json").read_text())
(SITE / "packs").mkdir(exist_ok=True)
thumbs = {}
for c in data["components"]:
    pack = {}
    for s in c["scenes"]:
        for kit in s["shots"].values():
            for f, _, _ in kit.values():
                pack[f] = base64.b64encode((SITE / "shots" / f).read_bytes()).decode()
    if pack:
        (SITE / "packs" / f"{c['slug']}.json").write_text(json.dumps(pack, separators=(",", ":")))
    first = next((s["shots"]["opencode"] for s in c["scenes"] if "opencode" in s["shots"]), None)
    if first:
        thumbs[c["slug"]] = {}
        for mode, (f, _, _) in first.items():
            out = subprocess.run(["magick", str(SITE / "shots" / f), "-resize", "560x", "-gravity", "NorthWest",
                                  "-crop", "560x300+0+0", "+repage", "-quality", "82", "webp:-"], capture_output=True, check=True).stdout
            thumbs[c["slug"]][mode] = base64.b64encode(out).decode()
(SITE / "thumbs.json").write_text(json.dumps(thumbs, separators=(",", ":")))
sizes = sorted(((p.stat().st_size // 1024, p.name) for p in (SITE / "packs").glob("*.json")), reverse=True)
print(len(sizes), "packs; largest:", sizes[:4], "; thumbs", (SITE / "thumbs.json").stat().st_size // 1024, "KB")
