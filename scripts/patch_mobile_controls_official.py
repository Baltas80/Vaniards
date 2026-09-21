#!/usr/bin/env python3
"""Install GDevelop's official multitouch joystick/buttons and mobile layout."""
from __future__ import annotations
import json
import sys
import uuid
from pathlib import Path

JOYSTICK = "SpriteMultitouchJoystick::SpriteMultitouchJoystick"
BUTTON = "SpriteMultitouchJoystick::MultitouchButton"
MAPPER = "SpriteMultitouchJoystick::PlatformerMultitouchMapper"


def condition(value, params):
    return {"type": {"value": value}, "parameters": params}


def action(value, params):
    return {"type": {"value": value}, "parameters": params}


def standard(conditions=None, actions=None, events=None):
    return {
        "type": "BuiltinCommonInstructions::Standard",
        "conditions": conditions or [],
        "actions": actions or [],
        "events": events or [],
    }


def group(name, events):
    return {
        "colorB": 74, "colorG": 176, "colorR": 228,
        "creationTime": 0, "name": name, "source": "",
        "type": "BuiltinCommonInstructions::Group", "events": events,
        "parameters": [],
    }


def button_behavior(identifier):
    return {
        "name": "MultitouchButton", "type": BUTTON,
        "ControllerIdentifier": 1, "ButtonIdentifier": identifier,
        "TouchId": 0, "TouchIndex": 0, "IsReleased": False,
        "IsJustPressed": False, "Radius": 0,
    }


def make_joystick():
    # Completely transparent visual object: the joystick remains a touch control,
    # but no arrows/circle are drawn over the game.
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


def instance(name, x=0, y=0, width=120, height=120, z=101):
    return {
        "angle": 0, "customSize": True, "height": height, "keepRatio": True,
        "layer": "GUI", "locked": False, "name": name,
        "persistentUuid": str(uuid.uuid4()), "width": width, "x": x, "y": y,
        "zOrder": z, "numberProperties": [], "stringProperties": [],
        "initialVariables": [],
    }


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
    by_name = {o.get("name"): o for o in objects}

    # Transparent joystick. Input remains active; only its artwork is invisible.
    transparent = "assets/vaniards_touch_transparent.png"
    resources = data.setdefault("resources", {}).setdefault("resources", [])
    if not any(r.get("file") == transparent for r in resources):
        resources.append({"file": transparent, "kind": "image", "metadata": "",
                          "name": Path(transparent).name, "smoothed": False,
                          "userAdded": True})
    objects[:] = [o for o in objects if o.get("name") != "MoveJoystick"]
    objects.append(make_joystick())

    # Real multitouch buttons. Do NOT hide them: their artwork is the visible
    # action-button layer and their hit areas are independent from the joystick.
    mapping = {"TouchJump": "A", "TouchAttack": "B", "TouchDash": "C"}
    for name, identifier in mapping.items():
        obj = by_name.get(name)
        if obj is None:
            raise RuntimeError(f"Missing object: {name}")
        obj["behaviors"] = [b for b in obj.get("behaviors", []) if b.get("type") != BUTTON]
        obj["behaviors"].append(button_behavior(identifier))
        obj["opacity"] = 255

    hero = next((o for o in objects if o.get("name") == "HeroHitbox"), None)
    if hero is None:
        raise RuntimeError("HeroHitbox not found")
    hero["behaviors"] = [b for b in hero.get("behaviors", []) if b.get("type") != MAPPER]
    hero["behaviors"].append({
        "isFolded": True, "name": "PlatformerMultitouchMapper", "type": MAPPER,
        "Property": "PlatformerObject", "ControllerIdentifier": 1,
        "JoystickIdentifier": "Primary", "JumpButton": "A",
    })

    instances = stage.setdefault("instances", [])
    instances[:] = [i for i in instances if i.get("name") != "MoveJoystick"]
    instances.append(instance("MoveJoystick", 110, 500, 210, 210, 101))

    # Large separation between right-side buttons. Positions are also recalculated
    # every frame from the actual game window, so different phone aspect ratios work.
    positions = {
        "TouchJump": ("SceneWindowWidth() - 330", "SceneWindowHeight() - 120"),
        "TouchAttack": ("SceneWindowWidth() - 155", "SceneWindowHeight() - 120"),
        "TouchDash": ("SceneWindowWidth() - 245", "SceneWindowHeight() - 285"),
    }
    for inst in instances:
        if inst.get("name") in positions:
            x, y = positions[inst["name"]]
            inst.update({"x": 0, "y": 0, "width": 118, "height": 118,
                         "customSize": True, "layer": "GUI", "opacity": 255})

    events = stage.get("events", [])
    events = [e for e in events if e.get("name") not in {
        "Mobile Touch Controls", "Mobile Touch Controls (Official Multitouch)",
        "Mobile Control Layout"
    }]

    # Use the extension's own IsPressed condition for attack/dash. This is important:
    # ordinary cursor/touch conditions can lose the second finger while the joystick
    # finger is held. The official extension tracks each touch independently.
    mobile = [
        standard(
            [condition("SpriteMultitouchJoystick::MultitouchButton::IsPressed",
                       ["TouchAttack", "MultitouchButton", ""])],
            [action("SetStringObjectVariable", ["Hero", "heroFSM", "=", "\"Attack\""])],
        ),
        standard(
            [condition("SpriteMultitouchJoystick::MultitouchButton::IsPressed",
                       ["TouchDash", "MultitouchButton", ""]),
             condition("NumberObjectVariable", ["Hero", "hasDashed", "=", "0"]),
             condition("NumberObjectVariable", ["Hero", "heroStam", ">=", "DashCost"]),
             condition("PlatformBehavior::IsOnFloor", ["HeroHitbox", "PlatformerObject"])],
            [action("SetStringObjectVariable", ["Hero", "heroFSM", "=", "\"Dash\""])],
        ),
    ]
    events.append(group("Mobile Touch Controls (Official Multitouch)", mobile))

    # Layout is tied to the actual window. Keep controls in GUI, never in world space.
    layout_events = []
    for name, (x, y) in positions.items():
        layout_events.append(standard([], [
            action("SetX", [name, "", "=", x]),
            action("SetY", [name, "", "=", y]),
        ]))
    # Joystick is deliberately transparent and stays in the lower-left safe zone.
    layout_events.append(standard([], [
        action("SetX", ["MoveJoystick", "", "=", "120"]),
        action("SetY", ["MoveJoystick", "", "=", "SceneWindowHeight() - 120"]),
    ]))
    events.append(group("Mobile Control Layout", layout_events))
    stage["events"] = events

    shared = stage.setdefault("behaviorsSharedData", [])
    names = {b.get("name") for b in shared}
    if "MultitouchButton" not in names:
        shared.append({"name": "MultitouchButton", "type": BUTTON})
    if "PlatformerMultitouchMapper" not in names:
        shared.append({"name": "PlatformerMultitouchMapper", "type": MAPPER})

    project_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Official multitouch controls installed: transparent joystick, separated buttons, dynamic GUI layout.")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: patch_mobile_controls_official.py <project.json> <reference-project.json>")
    patch(Path(sys.argv[1]), Path(sys.argv[2]))
