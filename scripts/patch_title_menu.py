#!/usr/bin/env python3
"""Make every Vaniards title-menu option directly selectable by touch/click.

The original title menu can leave the selector focused on Start, which makes the
other entries appear present but not selectable on mobile. This patch keeps the
existing menu intact and adds direct hit-tested handlers for Start/Credits/Exit.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def cond(value: str, params: list[str]) -> dict:
    return {"type": {"value": value}, "parameters": params}


def action(value: str, params: list[str]) -> dict:
    return {"type": {"value": value}, "parameters": params}


def std(conditions=None, actions=None, events=None) -> dict:
    return {
        "type": "BuiltinCommonInstructions::Standard",
        "conditions": conditions or [],
        "actions": actions or [],
        "events": events or [],
    }


def patch(path: Path) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    title = next((s for s in data.get("layouts", []) if s.get("name") == "Title"), None)
    if title is None:
        raise RuntimeError("Title scene not found")

    objects = {o.get("name") for o in title.get("objects", [])}
    required = {"BitmapMenuStart", "BitmapMenuCredits", "BitmapMenuExit"}
    missing = sorted(required - objects)
    if missing:
        raise RuntimeError(f"Title menu objects missing: {', '.join(missing)}")

    marker = "Direct touch/click menu selection"
    if any(e.get("comment") == marker for e in title.get("events", [])):
        print("Title direct menu selection already present")
        return

    started = "StartedTouchOrMouseId(0)"
    def hit(obj: str) -> dict:
        return cond(
            "CollisionPoint",
            [obj, f'TouchX({started}, "GUI", 0)', f'TouchY({started}, "GUI", 0)'],
        )

    title["events"].extend([
        {"type": "BuiltinCommonInstructions::Comment", "comment": marker},
        std(
            [cond("HasAnyTouchOrMouseStarted", [""]), hit("BitmapMenuStart")],
            [action("ChangeScene", ["Stage"])],
        ),
        std(
            [cond("HasAnyTouchOrMouseStarted", [""]), hit("BitmapMenuCredits")],
            [action("ChangeScene", ["Credits"])],
        ),
        std(
            [cond("HasAnyTouchOrMouseStarted", [""]), hit("BitmapMenuExit")],
            [action("QuitGame", [])],
        ),
    ])

    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Patched Title menu: Start/Credits/Exit are directly selectable by touch/click.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: patch_title_menu.py <project.json>")
    patch(Path(sys.argv[1]))
