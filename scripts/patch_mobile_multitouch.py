#!/usr/bin/env python3
"""Patch Vaniards mobile controls to support independent multi-touch input."""
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

def std(conditions=None, actions=None, events=None) -> dict:
    return {
        "type": "BuiltinCommonInstructions::Standard",
        "conditions": conditions or [],
        "actions": actions or [],
        "events": events or [],
    }

def repeat(expr: str, events: list[dict]) -> dict:
    return {
        "type": "BuiltinCommonInstructions::Repeat",
        "repeatExpression": expr,
        "conditions": [],
        "actions": [],
        "events": events,
    }

def num(name: str, op: str, value: str) -> dict:
    return cond("NumberVariable", [name, op, value])

def point_on(object_name: str, touch_expr: str) -> dict:
    return cond(
        "CollisionPoint",
        [
            object_name,
            f'TouchX({touch_expr}, "GUI", 0)',
            f'TouchY({touch_expr}, "GUI", 0)',
        ],
    )

def touch_x(touch_id: str, op: str, value: str) -> dict:
    return cond("TouchX", ["", touch_id, op, value, "GUI", ""])

def reset_events() -> list[dict]:
    actions = [
        action("SetNumberVariable", ["TouchMoveId", "=", "-1"]),
        action("SetNumberVariable", ["TouchMoveDirection", "=", "0"]),
        action("SetNumberVariable", ["TouchJumpId", "=", "-1"]),
        action("SetNumberVariable", ["TouchAttackId", "=", "-1"]),
        action("SetNumberVariable", ["TouchDashId", "=", "-1"]),
        action("SetNumberVariable", ["TouchInputIndex", "=", "0"]),
    ]
    return [
        std([cond("SceneJustBegins", [""])], actions),
        std([cond("HasGameJustResumed", [""])], actions.copy()),
    ]

def patch(path: Path) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    stage = next((s for s in data.get("layouts", []) if s.get("name") == "Stage"), None)
    if stage is None:
        raise RuntimeError("Stage scene not found")

    existing_names = {v.get("name") for v in stage.get("variables", [])}
    for name, value in [
        ("TouchMoveId", -1),
        ("TouchMoveDirection", 0),
        ("TouchJumpId", -1),
        ("TouchAttackId", -1),
        ("TouchDashId", -1),
        ("TouchInputIndex", 0),
    ]:
        if name not in existing_names:
            stage.setdefault("variables", []).append(
                {"name": name, "type": "number", "value": value}
            )

    mobile_group = next(
        (
            e for e in stage.get("events", [])
            if e.get("type") == "BuiltinCommonInstructions::Group"
            and e.get("name") == "Mobile Touch Controls"
        ),
        None,
    )
    if mobile_group is None:
        raise RuntimeError("Mobile Touch Controls group not found")

    old_events = mobile_group.get("events", [])
    if len(old_events) < 2:
        raise RuntimeError("Unexpected Mobile Touch Controls group structure")

    # Preserve the existing touch-control layout positioning exactly.
    events = old_events[:2]
    events[0]["comment"] = (
        "Mobile touch controls. Hold one finger on LEFT/RIGHT to move, then use "
        "other fingers independently for JUMP, ATK and DASH. The movement finger "
        "can slide left/right without being released."
    )
    events.extend(reset_events())

    # Release the specific finger that currently owns each control.
    events.extend([
        std(
            [num("TouchMoveId", "!=", "-1"),
             cond("HasTouchEnded", ["", "TouchMoveId"])],
            [
                action("SetNumberVariable", ["TouchMoveId", "=", "-1"]),
                action("SetNumberVariable", ["TouchMoveDirection", "=", "0"]),
            ],
        ),
        std(
            [num("TouchJumpId", "!=", "-1"),
             cond("HasTouchEnded", ["", "TouchJumpId"])],
            [action("SetNumberVariable", ["TouchJumpId", "=", "-1"])],
        ),
        std(
            [num("TouchAttackId", "!=", "-1"),
             cond("HasTouchEnded", ["", "TouchAttackId"])],
            [action("SetNumberVariable", ["TouchAttackId", "=", "-1"])],
        ),
        std(
            [num("TouchDashId", "!=", "-1"),
             cond("HasTouchEnded", ["", "TouchDashId"])],
            [action("SetNumberVariable", ["TouchDashId", "=", "-1"])],
        ),
    ])

    started_id = "StartedTouchOrMouseId(TouchInputIndex)"

    # Each newly-started finger is processed independently.
    capture = [
        std(
            [num("TouchMoveId", "=", "-1"), point_on("TouchLeft", started_id)],
            [
                action("SetNumberVariable", ["TouchMoveId", "=", started_id]),
                action("SetNumberVariable", ["TouchMoveDirection", "=", "-1"]),
            ],
        ),
        std(
            [num("TouchMoveId", "=", "-1"), point_on("TouchRight", started_id)],
            [
                action("SetNumberVariable", ["TouchMoveId", "=", started_id]),
                action("SetNumberVariable", ["TouchMoveDirection", "=", "1"]),
            ],
        ),
        std(
            [
                num("TouchJumpId", "=", "-1"),
                point_on("TouchJump", started_id),
                cond("NumberObjectVariable", ["Hero", "hasJumped", "=", "0"]),
                cond("PlatformBehavior::IsOnFloor", ["HeroHitbox", "PlatformerObject"]),
            ],
            [
                action("SetNumberVariable", ["TouchJumpId", "=", started_id]),
                action("PlatformBehavior::SetCanJump", ["HeroHitbox", "PlatformerObject"]),
                action("PlatformBehavior::SimulateJumpKey", ["HeroHitbox", "PlatformerObject"]),
                action("SetStringObjectVariable", ["Hero", "heroFSM", "=", "\"Jump\""]),
            ],
        ),
        std(
            [
                num("TouchAttackId", "=", "-1"),
                point_on("TouchAttack", started_id),
                cond("NumberObjectVariable", ["Hero", "hasAttacked", "=", "0"]),
                cond("PlatformBehavior::IsOnFloor", ["HeroHitbox", "PlatformerObject"]),
            ],
            [
                action("SetNumberVariable", ["TouchAttackId", "=", started_id]),
                action("SetStringObjectVariable", ["Hero", "heroFSM", "=", "\"Attack\""]),
            ],
        ),
        std(
            [
                num("TouchDashId", "=", "-1"),
                point_on("TouchDash", started_id),
                cond("NumberObjectVariable", ["Hero", "hasDashed", "=", "0"]),
                cond("NumberObjectVariable", ["Hero", "heroStam", ">=", "DashCost"]),
                cond("PlatformBehavior::IsOnFloor", ["HeroHitbox", "PlatformerObject"]),
            ],
            [
                action("SetNumberVariable", ["TouchDashId", "=", started_id]),
                action("SetStringObjectVariable", ["Hero", "heroFSM", "=", "\"Dash\""]),
            ],
        ),
        std([], [action("SetNumberVariable", ["TouchInputIndex", "+", "1"])]),
    ]

    events.append(
        std(
            [cond("HasAnyTouchOrMouseStarted", [""])],
            [action("SetNumberVariable", ["TouchInputIndex", "=", "0"])],
            [repeat("StartedTouchOrMouseCount()", capture)],
        )
    )

    mid = "(TouchLeft.CenterX()+TouchRight.CenterX())/2"
    # Movement remains bound to the first movement finger until that finger ends.
    events.extend([
        std(
            [num("TouchMoveId", "!=", "-1"),
             touch_x("TouchMoveId", "<", f"{mid}-18")],
            [
                action("PlatformBehavior::SimulateLeftKey", ["HeroHitbox", "PlatformerObject"]),
                action("SetNumberVariable", ["TouchMoveDirection", "=", "-1"]),
            ],
        ),
        std(
            [num("TouchMoveId", "!=", "-1"),
             touch_x("TouchMoveId", ">", f"{mid}+18")],
            [
                action("PlatformBehavior::SimulateRightKey", ["HeroHitbox", "PlatformerObject"]),
                action("SetNumberVariable", ["TouchMoveDirection", "=", "1"]),
            ],
        ),
        std(
            [
                num("TouchMoveId", "!=", "-1"),
                touch_x("TouchMoveId", ">=", f"{mid}-18"),
                touch_x("TouchMoveId", "<=", f"{mid}+18"),
            ],
            [action("SetNumberVariable", ["TouchMoveDirection", "=", "0"])],
        ),
    ])

    # Preserve the original Run/Idle animation-state rules.
    for direction in ["-1", "1"]:
        events.append(
            std(
                [
                    num("TouchMoveDirection", "=", direction),
                    cond("PlatformBehavior::IsOnFloor", ["HeroHitbox", "PlatformerObject"]),
                    cond("StringObjectVariable", ["Hero", "heroFSM", "!=", "\"Attack\""]),
                    cond("StringObjectVariable", ["Hero", "heroFSM", "!=", "\"Dash\""]),
                ],
                [action("SetStringObjectVariable", ["Hero", "heroFSM", "=", "\"Run\""])],
            )
        )
    events.append(
        std(
            [
                num("TouchMoveDirection", "=", "0"),
                cond("PlatformBehavior::IsOnFloor", ["HeroHitbox", "PlatformerObject"]),
                cond("StringObjectVariable", ["Hero", "heroFSM", "!=", "\"Attack\""]),
                cond("StringObjectVariable", ["Hero", "heroFSM", "!=", "\"Dash\""]),
            ],
            [action("SetStringObjectVariable", ["Hero", "heroFSM", "=", "\"Idle\""])],
        )
    )

    mobile_group["events"] = events
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Patched multi-touch controls: {path}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: patch_mobile_multitouch.py <project.json>")
    patch(Path(sys.argv[1]))
