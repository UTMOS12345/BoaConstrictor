from __future__ import annotations

import json
from typing import Any

from pg_explain.models import PlanNode


def parse_plan(data: str | dict[str, Any]) -> tuple[PlanNode, dict]:
    if isinstance(data, str):
        data = json.loads(data)

    if isinstance(data, list):
        data = data[0] if data else {}

    plan_data = data.get("Plan", data)
    root = PlanNode.from_dict(plan_data)

    metadata = {
        "Planning Time": data.get("Planning Time"),
        "Execution Time": data.get("Execution Time"),
        "Triggers": data.get("Triggers", []),
    }

    return root, metadata


def plan_from_explain_text(text: str) -> tuple[PlanNode, dict]:
    start = text.find("[")
    if start == -1:
        raise ValueError("No JSON array found in EXPLAIN output")
    end = text.rfind("]") + 1
    json_str = text[start:end]
    return parse_plan(json_str)