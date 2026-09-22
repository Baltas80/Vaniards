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
        # GDevelop stores keyboard/gamepad identifiers in the condition parameters,
        # not in the condition type itself (e.g. KeyFromTextPressed + keyboardJump).
        for key, value in node.items():
            if key == "parameters":
                if isinstance(value, list) and any(isinstance(v, str) and v in names for v in value):
                    return True
            elif key in ("conditions", "subInstructions", "events") and _contains_input(value, names):
                return True
        return False
    if isinstance(node, list):
        return any(_contains_input(v, names) for v in node)
    return False


def _add_touch_condition(conditions, object_name, inverted):
    if any(
        isinstance(c, dict)
        and c.get("type", {}).get("value") == "SpriteMultitouchJoystick::MultitouchButton::IsPressed"
        and c.get("type", {}).get("inverted", False) == inverted
        for c in conditions
    ):
        return
    conditions.append(condition(
        "SpriteMultitouchJoystick::MultitouchButton::IsPressed",
        [object_name, "MultitouchButton", ""],
        inverted=inverted,
    ))


def _add_touch_to_condition_list(conditions, input_names, object_name, inverted):
    if not _contains_input(conditions, input_names):
        return
    touch = condition(
        "SpriteMultitouchJoystick::MultitouchButton::IsPressed",
        [object_name, "MultitouchButton", ""],
        inverted=inverted,
    )
    for c in conditions:
        if isinstance(c, dict) and c.get("type", {}).get("value") == "BuiltinCommonInstructions::Or":
            subs = c.setdefault("subInstructions", [])
            if not any(
                isinstance(s, dict)
                and s.get("type", {}).get("value") == "SpriteMultitouchJoystick::MultitouchButton::IsPressed"
                for s in subs
            ):
                subs.append(touch)
            return
    _add_touch_condition(conditions, object_name, inverted)


def patch_touch_inputs(node):
    """Make the custom FSM accept independent multitouch buttons."""
    if isinstance(node, dict):
        if node.get("type") == "BuiltinCommonInstructions::Standard":
            conditions = node.get("conditions", [])
            targets = [
                ({"gamepadJump", "keyboardJump"}, "TouchJump"),
                ({"gamepadAttack", "keyboardAttack"}, "TouchAttack"),
                ({"gamepadDash", "keyboardDash"}, "TouchDash"),
            ]
            for names, button in targets:
                if not _contains_input(conditions, names):
                    continue
                release_gate = any(
                    isinstance(c, dict)
                    and c.get("type", {}).get("inverted", False)
                    and _contains_input(c, {"Gamepads::C_Button_pressed", "KeyFromTextPressed"})
                    for c in conditions
                )
                _add_touch_to_condition_list(conditions, names, button, release_gate)
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

    # The original game uses a custom Hero FSM, so button behaviors alone are
    # not enough. Add explicit independent touch transitions after the complete
    # joystick patch has been written.
    try:
        from patch_mobile_action_buttons import patch as patch_action_buttons
        patch_action_buttons(project_path)
    except Exception as exc:
        raise RuntimeError(f"Mobile action-button bridge failed: {exc}") from exc

    print("Robust multitouch controls installed: independent joystick movement + touch jump/attack/dash.")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: patch_mobile_controls_official.py <project.json> <reference-project.json>")
    patch(Path(sys.argv[1]), Path(sys.argv[2]))
