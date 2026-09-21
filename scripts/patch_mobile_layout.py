#!/usr/bin/env python3
"""Reposition Vaniards mobile touch hitboxes for a free joystick layout."""
from __future__ import annotations
import json
import sys
from pathlib import Path


def walk(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


def instances(stage):
    for obj in walk(stage):
        if isinstance(obj, dict) and obj.get("name") in {
            "TouchLeft", "TouchRight", "TouchJump", "TouchAttack", "TouchDash"
        }:
            # Only actual scene instances have a layer/x/y combination. This avoids
            # changing object definitions or event references with the same name.
            if "x" in obj and "y" in obj:
                yield obj


def place(obj, x, y, width=None, height=None, opacity=0):
    obj["x"] = x
    obj["y"] = y
    obj["opacity"] = opacity
    if width is not None:
        obj["width"] = width
        obj["customSize"] = True
    if height is not None:
        obj["height"] = height
        obj["customSize"] = True


def patch(path: Path) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    stage = next(s for s in data.get("layouts", []) if s.get("name") == "Stage")
    found = {obj["name"]: obj for obj in instances(stage)}
    missing = [name for name in ("TouchLeft", "TouchRight", "TouchJump", "TouchAttack", "TouchDash") if name not in found]
    if missing:
        raise RuntimeError(f"Mobile control instances not found: {missing}")

    # 1280x720 game coordinates. Both movement hitboxes overlap deliberately:
    # the first touch captures the movement finger and the multitouch event logic
    # then follows that finger even after it slides outside this area.
    place(found["TouchLeft"], 150, 600, 190, 190, 0)
    place(found["TouchRight"], 150, 600, 190, 190, 0)

    # Independent, widely separated action hitboxes. Visuals are supplied by the
    # HTML overlay so the old arrow/button artwork never appears on mobile.
    place(found["TouchDash"], 1090, 505, 120, 120, 0)
    place(found["TouchJump"], 970, 625, 120, 120, 0)
    place(found["TouchAttack"], 1140, 625, 120, 120, 0)

    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Mobile layout patched: free joystick + separated action buttons.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: patch_mobile_layout.py <project.json>")
    patch(Path(sys.argv[1]))
