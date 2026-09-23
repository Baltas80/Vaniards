#!/usr/bin/env python3
"""Connect multitouch action buttons without taking over platform movement.

The official GDevelop PlatformerMultitouchMapper owns movement. Jump therefore
uses the native PlatformBehavior action, so pressing jump cannot replace the
movement input or interrupt the joystick's active touch. Attack and dash keep
using Vaniards' existing FSM because those are game-specific actions.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

BUTTON_CONDITION = "SpriteMultitouchJoystick::MultitouchButton::IsPressed"

def condition(value: str, params: list[str]) -> dict:
    return {"type": {"value": value}, "parameters": params}

def action(value: str, params: list[str]) -> dict:
    return {"type": {"value": value}, "parameters": params}

def standard(conditions: list[dict], actions: list[dict]) -> dict:
    return {"type": "BuiltinCommonInstructions::Standard", "conditions": conditions, "actions": actions, "events": []}

def group(name: str, events: list[dict]) -> dict:
    return {"colorB": 74, "colorG": 176, "colorR": 228, "creationTime": 0,
            "name": name, "source": "", "type": "BuiltinCommonInstructions::Group",
            "events": events, "parameters": []}

def button_condition(name: str) -> dict:
    return condition(BUTTON_CONDITION, [name, "MultitouchButton", ""])

def hero_number_condition(variable_name: str, operator: str = "=", value: str = "0") -> dict:
    return condition("NumberObjectVariable", ["Hero", variable_name, operator, value])

def patch(project_path: Path) -> None:
    data = json.loads(project_path.read_text(encoding="utf-8"))
    stage = next((s for s in data.get("layouts", []) if s.get("name") == "Stage"), None)
    if stage is None:
        raise RuntimeError("Stage layout not found")

    events = [e for e in stage.setdefault("events", []) if e.get("name") != "Mobile Action Buttons FSM Bridge"]

    # IMPORTANT: jump is the native Platform behavior action used by GDevelop's
    # own platformer examples. It does not change Vaniards' hero FSM state, so
    # horizontal movement from the official multitouch mapper continues while
    # the jump finger is held/pressed.
    jump = standard(
        [button_condition("TouchJump")],
        [action("PlatformBehavior::SimulateJumpKey", ["HeroHitbox", "PlatformerObject"])],
    )
    attack = standard(
        [button_condition("TouchAttack"), hero_number_condition("hasAttacked")],
        [action("SetStringVariable", ["Hero", "heroFSM", "=", '\"Attack\"'])],
    )
    dash = standard(
        [button_condition("TouchDash"), hero_number_condition("hasDashed"),
         hero_number_condition("heroStam", ">=", "GlobalVariable(DashCost)")],
        [action("SetStringVariable", ["Hero", "heroFSM", "=", '\"Dash\"'])],
    )

    events.append(group("Mobile Action Buttons FSM Bridge", [jump, attack, dash]))
    stage["events"] = events
    project_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Multitouch jump now uses native PlatformBehavior::SimulateJumpKey; attack/dash remain FSM actions.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: patch_mobile_action_buttons.py <project.json>")
    patch(Path(sys.argv[1]))
