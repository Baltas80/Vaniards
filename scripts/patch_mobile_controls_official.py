#!/usr/bin/env python3
"""Install robust multitouch controls for the Vaniards platformer."""
from __future__ import annotations
import json
import sys
import uuid
from pathlib import Path

JOYSTICK = "SpriteMultitouchJoystick::SpriteMultitouchJoystick"
BUTTON = "SpriteMultitouchJoystick::MultitouchButton"
MAPPER = "SpriteMultitouchJoystick::PlatformerMultitouchMapper"


def condition(value, params, inverted=False):
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


def _contains_input(node, names):
    if isinstance(node, dict):
        typ = node.get("type")
        if isinstance(typ, dict) and typ.get("value") in names:
            return True
        return any(_contains_input(v, names) for k, v in node.items()
                   if k in ("conditions", "subInstructions", "events"))
    if isinstance(node, list):
        return any(_contains_input(v, names) for v in node)
    return False


def _add_touch_to_condition_list(conditions, names, object_name, inverted=False):
    """Add the matching multitouch button to an existing input condition."""
    if not conditions or not _contains_input(conditions, names):
        return
    touch = condition(
        "SpriteMultitouchJoystick::MultitouchButton::IsPressed",
        [object_name, "MultitouchButton", ""],
        inverted=inverted,
    )
    # Normal action input is usually inside one Or block.
    for c in conditions:
        if isinstance(c, dict):
            typ = c.get("type", {})
            if typ.get("value") == "BuiltinCommonInstructions::Or":
                subs = c.setdefault("subInstructions", [])
                if not _contains_input(subs, {"SpriteMultitouchJoystick::MultitouchButton::IsPressed"}):
                    subs.append(touch)
                return
    # Release gates are represented as separate inverted conditions.
    if not any(
        isinstance(c, dict)
        and c.get("type", {}).get("value") == "SpriteMultitouchJoystick::MultitouchButton::IsPressed"
        for c in conditions
    ):
        conditions.append(touch)


def patch_touch_inputs(node):
    """Patch Vaniards' FSM so touch actions are first-class inputs.

    The original game FSM listens to keyboard/gamepad input. The official
    multitouch mapper is intentionally not used for the character because the
    custom FSM also simulates platformer controls. Instead, the same FSM now
    accepts the independent multitouch buttons, while joystick X movement is
    simulated every frame below.
    """
    if isinstance(node, dict):
        if node.get("type") == "BuiltinCommonInstructions::Standard":
            conditions = node.get("conditions", [])
            _add_touch_to_condition_list(
                conditions, {"Gamepads::C_Button_pressed", "KeyFromTextPressed"},
                "TouchJump", False
            ) if _contains_input(conditions, {"gamepadJump", "keyboardJump"}) else None
            _add_touch_to_condition_list(
                conditions, {"Gamepads::C_Button_pressed", "KeyFromTextPressed"},
                "TouchAttack", False
            ) if _contains_input(conditions, {"gamepadAttack", "keyboardAttack"}) else None
            _add_touch_to_condition_list(
                conditions, {"Gamepads::C_Button_pressed", "KeyFromTextPressed"},
                "TouchDash", False
            ) if _contains_input(conditions, {"gamepadDash", "keyboardDash"}) else None

            # The three release gates must also require the corresponding touch
            # button to be released before the action can be used again.
            if _contains_input(conditions, {"gamepadJump", "keyboardJump"}):
                # Only add an inverted touch condition to a release-style node.
                if any(
                    isinstance(c, dict) and c.get("type", {}).get("inverted")
                    and _contains_input(c, {"Gamepads::C_Button_pressed", "KeyFromTextPressed"})
                    for c in conditions
                ):
                    _add_touch_to_condition_list(
                        conditions, {"gamepadJump", "keyboardJump"}, "TouchJump", True
                    )
            if _contains_input(conditions, {"gamepadAttack", "keyboardAttack"}):
                if any(
                    isinstance(c, dict) and c.get("type", {}).get("inverted")
                    and _contains_input(c, {"Gamepads::C_Button_pressed", "KeyFromTextPressed"})
                    for c in conditions
                ):
                    _add_touch_to_condition_list(
                        conditions, {"gamepadAttack", "keyboardAttack"}, "TouchAttack", True
                    )
            if _contains_input(conditions, {"gamepadDash", "keyboardDash"}):
                if any(
                    isinstance(c, dict) and c.get("type", {}).get("inverted")
                    and _contains_input(c, {"Gamepads::C_Button_pressed", "KeyFromTextPressed"})
                    for c in conditions
                ):
                    _add_touch_to_condition_list(
                        conditions, {"gamepadDash", "keyboardDash"}, "TouchDash", True
                    )
        for v in node.values():
            patch_touch_inputs(v)
    elif isinstance(node, list):
        for v in node:
            patch_touch_inputs(v)


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

    transparent = "assets/vaniards_touch_transparent.png"
    resources = data.setdefault("resources", {}).setdefault("resources", [])
    if not any(r.get("file") == transparent for r in resources):
        resources.append({"file": transparent, "kind": "image", "metadata": "",
                          "name": Path(transparent).name, "smoothed": False,
                          "userAdded": True})
    objects[:] = [o for o in objects if o.get("name") != "MoveJoystick"]
    objects.append(make_joystick())

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
    # Do not use PlatformerMultitouchMapper here. Vaniards has a custom FSM
    # that already simulates platformer controls; mixing two controllers was
    # causing the horizontal input to be cancelled when a second finger jumped.
    hero["behaviors"] = [b for b in hero.get("behaviors", []) if b.get("type") != MAPPER]

    instances = stage.setdefault("instances", [])
    instances[:] = [i for i in instances if i.get("name") != "MoveJoystick"]
    instances.append(instance("MoveJoystick", 110, 500, 210, 210, 101))

    positions = {
        "TouchJump": ("SceneWindowWidth() - 330", "SceneWindowHeight() - 120"),
        "TouchAttack": ("SceneWindowWidth() - 155", "SceneWindowHeight() - 120"),
        "TouchDash": ("SceneWindowWidth() - 245", "SceneWindowHeight() - 285"),
    }
    for inst in instances:
        if inst.get("name") in positions:
            inst.update({"x": 0, "y": 0, "width": 118, "height": 118,
                         "customSize": True, "layer": "GUI", "opacity": 255})

    # Add touch input to the existing FSM and direct joystick movement events.
    for function in data.get("eventsFunctions", []):
        if function.get("associatedLayout") == "Stage" and function.get("name", "").startswith("HeroFSM"):
            patch_touch_inputs(function.get("events", []))

    events = stage.get("events", [])
    events = [e for e in events if e.get("name") not in {
        "Mobile Touch Controls", "Mobile Touch Controls (Official Multitouch)",
        "Mobile Control Layout", "Mobile Joystick Movement"
    }]

    joystick_left = standard(
        [condition("BuiltinCommonInstructions::CompareNumbers", [
            'SpriteMultitouchJoystick::StickForceX(1, "Primary")', '<', '-0.15'
        ])],
        [action("PlatformBehavior::SimulateLeftKey", ["HeroHitbox", "PlatformerObject"])],
    )
    joystick_right = standard(
        [condition("BuiltinCommonInstructions::CompareNumbers", [
            'SpriteMultitouchJoystick::StickForceX(1, "Primary")', '>', '0.15'
        ])],
        [action("PlatformBehavior::SimulateRightKey", ["HeroHitbox", "PlatformerObject"])],
    )
    events.append(group("Mobile Joystick Movement", [joystick_left, joystick_right]))

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
    events.append(group("Mobile Control Layout", layout_events))
    stage["events"] = events

    shared = stage.setdefault("behaviorsSharedData", [])
    names = {b.get("name") for b in shared}
    if "MultitouchButton" not in names:
        shared.append({"name": "MultitouchButton", "type": BUTTON})

    project_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Robust multitouch controls installed: independent joystick movement + touch jump/attack/dash.")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: patch_mobile_controls_official.py <project.json> <reference-project.json>")
    patch(Path(sys.argv[1]), Path(sys.argv[2]))
