#!/usr/bin/env python3
"""Make every Vaniards title-menu option directly selectable by touch/click.

The title menu already has keyboard/gamepad navigation and legacy mouse handlers,
but Android touch can remain focused on Start. This patch adds a direct
hit-tested touch/click path for Start, Credits and Exit using the actual title
scene layer (the menu objects live on the base layer, not the GUI layer).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def cond(value: str, params: list[str], inverted: bool = False) -> dict:
    t = {"value": value}
    if inverted:
        t["inverted"] = True
    return {"type": t, "parameters": params}


def action(value: str, params: list[str]) -> dict:
    return {"type": {"value": value}, "parameters": params}


def std(conditions=None, actions=None, events=None, name: str | None = None) -> dict:
    result = {
        "type": "BuiltinCommonInstructions::Standard",
        "conditions": conditions or [],
        "actions": actions or [],
        "events": events or [],
    }
    if name:
        result["name"] = name
    return result


def is_marker(event: dict) -> bool:
    return event.get("type") == "BuiltinCommonInstructions::Comment" and event.get("comment") == "Direct touch/click menu selection"


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

    # Remove an earlier version of this patch if it exists. This is important
    # because the first implementation incorrectly queried the GUI layer while
    # the title menu objects are on the base layer (layer="").
    events = title.setdefault("events", [])
    cleaned = []
    skip = 0
    for event in events:
        if skip:
            skip -= 1
            continue
        if is_marker(event):
            skip = 3
            continue
        cleaned.append(event)
    title["events"] = cleaned

    started = "StartedTouchOrMouseId(0)"

    def hit(obj: str) -> dict:
        # Title menu objects are on the base layer (""), not GUI.
        return cond(
            "CollisionPoint",
            [obj, f'TouchX({started}, "", 0)', f'TouchY({started}, "", 0)'],
        )

    # HasAnyTouchOrMouseStarted also covers the mouse-start path on desktop,
    # while StartedTouchOrMouseId(0) supplies the identifier for the first input.
    direct_events = [
        {"type": "BuiltinCommonInstructions::Comment", "comment": "Direct touch/click menu selection"},
        std(
            [cond("HasAnyTouchOrMouseStarted", []), hit("BitmapMenuStart"), cond("BuiltinCommonInstructions::Once", [])],
            [action("Scene", ["", '\"Stage\"', "yes"])],
            name="Touch Start Direct",
        ),
        std(
            [cond("HasAnyTouchOrMouseStarted", []), hit("BitmapMenuCredits"), cond("BuiltinCommonInstructions::Once", [])],
            [action("Scene", ["", '\"Credits\"', "yes"])],
            name="Touch Credits Direct",
        ),
        std(
            [cond("HasAnyTouchOrMouseStarted", []), hit("BitmapMenuExit"), cond("BuiltinCommonInstructions::Once", [])],
            [action("Quit", [""])],
            name="Touch Exit Direct",
        ),
    ]
    title["events"].extend(direct_events)

    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Patched Title menu: Start/Credits/Exit use direct touch hit-tests on the base layer.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: patch_title_menu.py <project.json>")
    patch(Path(sys.argv[1]))
