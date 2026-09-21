#!/usr/bin/env python3
"""Use GDevelop's current SpriteMultitouchJoystick extension for Vaniards."""
from __future__ import annotations
import json
import sys
import uuid
from pathlib import Path

JOYSTICK_TYPE = "SpriteMultitouchJoystick::SpriteMultitouchJoystick"
MULTITOUCH_BUTTON = "SpriteMultitouchJoystick::MultitouchButton"
PLATFORMER_MAPPER = "SpriteMultitouchJoystick::PlatformerMultitouchMapper"

def cond(value, params, inverted=False):
    t = {"value": value}
    if inverted:
        t["inverted"] = True
    return {"type": t, "parameters": params}

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
        "colorB": 74,
        "colorG": 176,
        "colorR": 228,
        "creationTime": 0,
        "name": name,
        "source": "",
        "type": "BuiltinCommonInstructions::Group",
        "events": events,
        "parameters": [],
    }

def behavior_button(identifier):
    return {
        "name": "MultitouchButton",
        "type": MULTITOUCH_BUTTON,
        "ControllerIdentifier": 1,
        "ButtonIdentifier": identifier,
        "TouchId": 0,
        "TouchIndex": 0,
        "IsReleased": False,
        "IsJustPressed": False,
        "Radius": 0,
    }

def ensure_button_behavior(obj, identifier):
    behaviors = obj.setdefault("behaviors", [])
    behaviors[:] = [b for b in behaviors if b.get("type") != MULTITOUCH_BUTTON]
    behaviors.append(behavior_button(identifier))

def set_hidden(instance):
    instance["opacity"] = 0

def ensure_resource(data, filename):
    resources = data.setdefault("resources", {}).setdefault("resources", [])
    if not any(r.get("file") == filename for r in resources):
        resources.append({
            "file": filename,
            "kind": "image",
            "metadata": "",
            "name": Path(filename).name,
            "smoothed": False,
            "userAdded": True,
        })

def make_joystick_object(transparent_file):
    return {
        "assetStoreId": "",
        "name": "MoveJoystick",
        "type": JOYSTICK_TYPE,
        "variant": "",
        "variables": [],
        "effects": [],
        "behaviors": [],
        "content": {"DeadZoneRadius": 0.12},
        "childrenContent": {
            "Border": {
                "adaptCollisionMaskAutomatically": False,
                "updateIfNotVisible": False,
                "animations": [{
                    "name": "Idle",
                    "useMultipleDirections": False,
                    "directions": [{
                        "looping": False,
                        "timeBetweenFrames": 0.08,
                        "sprites": [{
                            "hasCustomCollisionMask": False,
                            "image": transparent_file,
                            "points": [],
                            "originPoint": {"name": "origine", "x": 0, "y": 0},
                            "centerPoint": {"automatic": True, "name": "centre", "x": 0, "y": 0},
                            "customCollisionMask": [],
                        }]
                    }]
                }]
            },
            "Thumb": {
                "adaptCollisionMaskAutomatically": False,
                "updateIfNotVisible": False,
                "animations": [{
                    "name": "Idle",
                    "useMultipleDirections": False,
                    "directions": [{
                        "looping": False,
                        "timeBetweenFrames": 0.08,
                        "sprites": [{
                            "hasCustomCollisionMask": False,
                            "image": transparent_file,
                            "points": [],
                            "originPoint": {"name": "origine", "x": 0, "y": 0},
                            "centerPoint": {"automatic": True, "name": "centre", "x": 0, "y": 0},
                            "customCollisionMask": [],
                        }]
                    }]
                }]
            }
        }
    }

def make_instance(name, x, y, width, height, z):
    return {
        "angle": 0,
        "customSize": True,
        "height": height,
        "keepRatio": True,
        "layer": "GUI",
        "locked": True,
        "name": name,
        "persistentUuid": str(uuid.uuid4()),
        "width": width,
        "x": x,
        "y": y,
        "zOrder": z,
        "numberProperties": [],
        "stringProperties": [],
        "initialVariables": [],
    }

def patch(path, extension_path):
    data = json.loads(path.read_text(encoding="utf-8"))
    ext_project = json.loads(extension_path.read_text(encoding="utf-8"))
    extension = next(
        (e for e in ext_project.get("eventsFunctionsExtensions", [])
         if e.get("name") == "SpriteMultitouchJoystick"),
        None,
    )
    if extension is None:
        raise RuntimeError("SpriteMultitouchJoystick extension not found in reference project")

    # Replace any older copy with the current extension used by the official GDevelop examples.
    data["eventsFunctionsExtensions"] = [
        e for e in data.get("eventsFunctionsExtensions", [])
        if e.get("name") != "SpriteMultitouchJoystick"
    ] + [extension]

    stage = next((s for s in data.get("layouts", []) if s.get("name") == "Stage"), None)
    if stage is None:
        raise RuntimeError("Stage layout not found")

    objects = stage.setdefault("objects", [])
    by_name = {o.get("name"): o for o in objects}

    # Create the real multitouch joystick object. Its child sprites are transparent;
    # the visible joystick is supplied by the pointer-transparent HTML overlay.
    transparent_file = "assets/vaniards_touch_transparent.png"
    ensure_resource(data, transparent_file)
    objects[:] = [o for o in objects if o.get("name") != "MoveJoystick"]
    joystick_obj = make_joystick_object(transparent_file)
    objects.append(joystick_obj)

    # Turn the existing touch buttons into true per-finger multitouch buttons.
    mapping = {"TouchJump": "A", "TouchAttack": "B", "TouchDash": "C"}
    for name, identifier in mapping.items():
        obj = by_name.get(name)
        if obj is None:
            raise RuntimeError(f"Missing touch button object: {name}")
        ensure_button_behavior(obj, identifier)
        obj["opacity"] = 0

    # Disable/hide legacy movement pads and labels; they are no longer the input path.
    for obj in objects:
        if obj.get("name") in {"TouchLeft", "TouchRight", "TouchJumpLabel", "TouchRightLabel",
                               "TouchLeftLabel", "TouchAttackLabel", "TouchDashLabel", "TouchJumpLabel"}:
            obj["opacity"] = 0

    # Remove any previous mapper and attach the official mapper to the platformer hitbox.
    hero_hitbox = next((o for o in objects if o.get("name") == "HeroHitbox"), None)
    if hero_hitbox is None:
        raise RuntimeError("HeroHitbox not found")
    hero_hitbox["behaviors"] = [
        b for b in hero_hitbox.get("behaviors", [])
        if b.get("type") != PLATFORMER_MAPPER
    ]
    hero_hitbox["behaviors"].append({
        "isFolded": True,
        "name": "PlatformerMultitouchMapper",
        "type": PLATFORMER_MAPPER,
        "Property": "PlatformerObject",
        "ControllerIdentifier": 1,
        "JoystickIdentifier": "Primary",
        "JumpButton": "A",
    })

    # Add the joystick instance.
    instances = stage.setdefault("instances", [])
    instances[:] = [i for i in instances if i.get("name") != "MoveJoystick"]
    instances.append(make_instance("MoveJoystick", 150, 600, 190, 190, 101))

    # Position the hidden action hitboxes to match the visible right-side controls.
    positions = {
        "TouchJump": (970, 625, 120, 120),
        "TouchAttack": (1140, 625, 120, 120),
        "TouchDash": (1090, 505, 120, 120),
    }
    for inst in instances:
        if inst.get("name") in positions:
            x, y, w, h = positions[inst["name"]]
            inst.update({"x": x, "y": y, "width": w, "height": h, "customSize": True, "opacity": 0, "layer": "GUI"})

    # Replace the legacy touch-control event group with the official controller path.
    events = stage.get("events", [])
    keep = [e for e in events if e.get("name") != "Mobile Touch Controls"]

    mobile_events = [
        {"type": "BuiltinCommonInstructions::Comment",
         "color": {"b": 109, "g": 230, "r": 255, "textB": 0, "textG": 0, "textR": 0},
         "comment": "Official GDevelop SpriteMultitouchJoystick extension. Movement uses a fixed free joystick; jump, attack and dash use independent touch IDs so multiple fingers can be used simultaneously.",
         "comment2": ""},
        standard(
            [cond("SpriteMultitouchJoystick::MultitouchButton::IsJustPressed", ["TouchAttack", "MultitouchButton", ""])],
            [
                action("SetStringObjectVariable", ["Hero", "heroFSM", "=", "\"Attack\""]),
            ],
        ),
        standard(
            [
                cond("SpriteMultitouchJoystick::MultitouchButton::IsJustPressed", ["TouchDash", "MultitouchButton", ""]),
                cond("NumberObjectVariable", ["Hero", "hasDashed", "=", "0"]),
                cond("NumberObjectVariable", ["Hero", "heroStam", ">=", "DashCost"]),
                cond("PlatformBehavior::IsOnFloor", ["HeroHitbox", "PlatformerObject"]),
            ],
            [
                action("SetStringObjectVariable", ["Hero", "heroFSM", "=", "\"Dash\""]),
            ],
        ),
    ]
    keep.append(group("Mobile Touch Controls (Official Multitouch)", mobile_events))
    stage["events"] = keep

    # Shared behavior data for editor compatibility.
    shared = stage.setdefault("behaviorsSharedData", [])
    existing_shared = {b.get("name"): b for b in shared}
    if "MultitouchButton" not in existing_shared:
        shared.append({"name": "MultitouchButton", "type": MULTITOUCH_BUTTON})
    if "PlatformerMultitouchMapper" not in existing_shared:
        shared.append({"name": "PlatformerMultitouchMapper", "type": PLATFORMER_MAPPER})

    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Official SpriteMultitouchJoystick controls installed.")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: patch_mobile_controls_official.py <project.json> <reference-project.json>")
    patch(Path(sys.argv[1]), Path(sys.argv[2]))
