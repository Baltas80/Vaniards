#!/usr/bin/env python3
"""Install GDevelop's proven multitouch platformer controls.

Vaniards uses a custom hero FSM, but horizontal platformer input is delegated to
GDevelop's official PlatformerMultitouchMapper. This avoids manually translating
touch coordinates into keyboard simulation and, importantly, keeps the joystick
finger independent from the jump/attack/dash fingers.
"""
from __future__ import annotations
import json
import sys
import uuid
from pathlib import Path

JOYSTICK = "SpriteMultitouchJoystick::SpriteMultitouchJoystick"
BUTTON = "SpriteMultitouchJoystick::MultitouchButton"
MAPPER = "SpriteMultitouchJoystick::PlatformerMultitouchMapper"


def button_behavior(identifier):
    return {
        "name": "MultitouchButton", "type": BUTTON,
        "ControllerIdentifier": 1, "ButtonIdentifier": identifier,
        "TouchId": 0, "TouchIndex": 0, "IsReleased": False,
        "IsJustPressed": False, "Radius": 0,
    }


def mapper_behavior():
    return {
        "name": "PlatformerMultitouchMapper",
        "type": MAPPER,
        "ControllerIdentifier": 1,
        "JoystickIdentifier": "Primary",
    }


def make_joystick():
    transparent = "assets/vaniards_touch_transparent.png"
    sprite = {
        "hasCustomCollisionMask": False, "image": transparent, "points": [],
        "originPoint": {"name": "origine", "x": 0, "y": 0},
        "centerPoint": {"automatic": True, "name": "centre", "x": 0, "y": 0},
        "customCollisionMask": [],
    }
    animation = {"name": "Idle", "useMultipleDirections": False,
                 "directions": [{"looping": False, "timeBetweenFrames": 0.08,
                                  "sprites": [sprite]}]}
    child = {"adaptCollisionMaskAutomatically": False,
             "updateIfNotVisible": False, "animations": [animation]}
    return {
        "assetStoreId": "", "name": "MoveJoystick", "type": JOYSTICK,
        "variant": "", "variables": [], "effects": [], "behaviors": [],
        "content": {"DeadZoneRadius": 0.10, "ControllerIdentifier": 1,
                     "JoystickIdentifier": "Primary"},
        "childrenContent": {"Border": child, "Thumb": child.copy()},
    }


def instance(name, x, y, width=118, height=118, z=101):
    return {
        "angle": 0, "customSize": True, "height": height, "keepRatio": True,
        "layer": "GUI", "locked": False, "name": name,
        "persistentUuid": str(uuid.uuid4()), "width": width, "x": x, "y": y,
        "zOrder": z, "numberProperties": [], "stringProperties": [],
        "initialVariables": [],
    }


def standard(conditions=None, actions=None):
    return {
        "type": "BuiltinCommonInstructions::Standard",
        "conditions": conditions or [], "actions": actions or [], "events": []
    }


def condition(value, params, inverted=False):
    typ = {"value": value}
    if inverted:
        typ["inverted"] = True
    return {"type": typ, "parameters": params}


def action(value, params):
    return {"type": {"value": value}, "parameters": params}


def group(name, events):
    return {"colorB": 74, "colorG": 176, "colorR": 228, "creationTime": 0,
            "name": name, "source": "", "type": "BuiltinCommonInstructions::Group",
            "events": events, "parameters": []}


def patch(project_path: Path, reference_path: Path):
    data = json.loads(project_path.read_text(encoding="utf-8"))
    ref = json.loads(reference_path.read_text(encoding="utf-8"))
    extension = next((e for e in ref.get("eventsFunctionsExtensions", [])
                      if e.get("name") == "SpriteMultitouchJoystick"), None)
    if extension is None:
        raise RuntimeError("Official SpriteMultitouchJoystick extension not found")
    data["eventsFunctionsExtensions"] = [
        e for e in data.get("eventsFunctionsExtensions", [])
        if e.get("name") != "SpriteMultitouchJoystick"
    ] + [extension]

    stage = next((s for s in data.get("layouts", []) if s.get("name") == "Stage"), None)
    if stage is None:
        raise RuntimeError("Stage layout not found")
    objects = stage.setdefault("objects", [])
    objects[:] = [o for o in objects if o.get("name") != "MoveJoystick"]
    objects.append(make_joystick())

    by_name = {o.get("name"): o for o in objects}
    for name, identifier in {"TouchJump": "A", "TouchAttack": "B", "TouchDash": "C"}.items():
        obj = by_name.get(name)
        if obj is None:
            raise RuntimeError(f"Missing object: {name}")
        obj["behaviors"] = [b for b in obj.get("behaviors", []) if b.get("type") != BUTTON]
        obj["behaviors"].append(button_behavior(identifier))
        obj["opacity"] = 255

    hero = by_name.get("HeroHitbox")
    if hero is None:
        raise RuntimeError("HeroHitbox not found")
    hero["behaviors"] = [b for b in hero.get("behaviors", []) if b.get("type") != MAPPER]
    hero["behaviors"].append(mapper_behavior())

    resources = data.setdefault("resources", {}).setdefault("resources", [])
    transparent = "assets/vaniards_touch_transparent.png"
    if not any(r.get("file") == transparent for r in resources):
        resources.append({"file": transparent, "kind": "image", "metadata": "",
                          "name": Path(transparent).name, "smoothed": False, "userAdded": True})

    instances = stage.setdefault("instances", [])
    instances[:] = [i for i in instances if i.get("name") != "MoveJoystick"]
    # Visual controls remain separate and large enough for phone use.
    instances.append(instance("MoveJoystick", 120, 0, 210, 210, 101))
    positions = {
        "TouchJump": ("SceneWindowWidth() - 330", "SceneWindowHeight() - 120"),
        "TouchAttack": ("SceneWindowWidth() - 155", "SceneWindowHeight() - 120"),
        "TouchDash": ("SceneWindowWidth() - 245", "SceneWindowHeight() - 285"),
    }
    for inst in instances:
        if inst.get("name") in positions:
            inst["x"], inst["y"] = 0, 0
            inst["width"], inst["height"] = 118, 118
            inst["customSize"] = True
            inst["layer"] = "GUI"
            inst["opacity"] = 255

    # Remove all previous hand-written joystick movement groups. The official
    # mapper now owns horizontal input, exactly as in GDevelop's examples.
    stage["events"] = [e for e in stage.get("events", []) if e.get("name") not in {
        "Mobile Joystick Movement", "Mobile Control Layout", "Mobile Touch Controls",
        "Mobile Touch Controls (Official Multitouch)"
    }]

    # Only position the action buttons; their input remains independent of the joystick.
    layout_events = []
    for name, (x, y) in positions.items():
        layout_events.append(standard([], [
            action("SetX", [name, "", "=", x]),
            action("SetY", [name, "", "=", y]),
        ]))
    layout_events.append(standard([], [
        action("SetX", ["MoveJoystick", "", "=", "120"]),
        action("SetY", ["MoveJoystick", "", "=", "SceneWindowHeight() - 120"]),
    ]))
    stage["events"].append(group("Mobile Control Layout", layout_events))

    project_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Official GDevelop PlatformerMultitouchMapper installed: joystick owns movement; action buttons remain independent.")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: patch_mobile_controls_official.py <project.json> <reference-project.json>")
    patch(Path(sys.argv[1]), Path(sys.argv[2]))
