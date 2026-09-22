#!/usr/bin/env python3
"""Bridge the mobile multitouch buttons into Vaniards' hero FSM.

The game uses a custom Hero FSM rather than the PlatformerObject input mapper.
The official SpriteMultitouchJoystick button behaviors therefore need explicit
transitions for jump, attack and dash. This patch keeps the original keyboard
and gamepad controls untouched and adds equivalent independent touch input.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

BUTTON_CONDITION = "SpriteMultitouchJoystick::MultitouchButton::IsPressed"


def condition(value: str, params: list[str], inverted: bool = False) -> dict:
    typ = {"value": value}
    if inverted:
        typ["inverted"] = True
    return {"type": typ, "parameters": params}


def action(value: str, params: list[str]) -> dict:
    return {"type": {"value": value}, "parameters": params}


def standard(conditions: list[dict], actions: list[dict]) -> dict:
    return {
        "type": "BuiltinCommonInstructions::Standard",
        "conditions": conditions,
        "actions": actions,
        "events": [],
    }


def group(name: str, events: list[dict]) -> dict:
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


def button_condition(name: str) -> dict:
    return condition(BUTTON_CONDITION, [name, "MultitouchButton", ""])


def hero_number_condition(variable_name: str, operator: str = "=", value: str = "0") -> dict:
    return condition(
        "NumberObjectVariable",
        ["Hero", variable_name, operator, value],
    )


def patch(project_path: Path) -> None:
    data = json.loads(project_path.read_text(encoding="utf-8"))
    stage = next((s for s in data.get("layouts", []) if s.get("name") == "Stage"), None)
    if stage is None:
        raise RuntimeError("Stage layout not found")

    events = stage.setdefault("events", [])
    marker = "Mobile Action Buttons FSM Bridge"
    events = [e for e in events if e.get("name") != marker]

    # Hero variables: hasJumped, hasAttacked and hasDashed are the original
    # FSM gates. Dash additionally requires heroStam >= global DashCost.
    jump = standard(
        [
            button_condition("TouchJump"),
            hero_number_condition("hasJumped"),
        ],
        [
            action(
                "SetStringVariable",
                ["Hero", "heroFSM", "=", '\"Jump\"'],
            )
        ],
    )
    attack = standard(
        [
            button_condition("TouchAttack"),
            hero_number_condition("hasAttacked"),
        ],
        [
            action(
                "SetStringVariable",
                ["Hero", "heroFSM", "=", '\"Attack\"'],
            )
        ],
    )
    dash = standard(
        [
            button_condition("TouchDash"),
            hero_number_condition("hasDashed"),
            hero_number_condition("heroStam", ">=", "GlobalVariable(DashCost)"),
        ],
        [
            action(
                "SetStringVariable",
                ["Hero", "heroFSM", "=", '\"Dash\"'],
            )
        ],
    )

    events.append(group(marker, [jump, attack, dash]))
    stage["events"] = events
    project_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Mobile action buttons bridged into Hero FSM: jump, attack and dash.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: patch_mobile_action_buttons.py <project.json>")
    patch(Path(sys.argv[1]))
