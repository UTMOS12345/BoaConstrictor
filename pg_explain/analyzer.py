from __future__ import annotations

from pg_explain.models import Issue, PlanNode
from pg_explain.rules import ALL_RULES, DEFAULT_RULES


def analyze(
    root: PlanNode,
    rules: list[str] | None = None,
) -> list[Issue]:
    if rules is None:
        rules = DEFAULT_RULES

    active_rules = []
    for rule_id in rules:
        fn = ALL_RULES.get(rule_id)
        if fn:
            active_rules.append((rule_id, fn))

    all_issues: list[Issue] = []
    _walk(root, root, active_rules, all_issues)

    all_issues.sort(
        key=lambda i: (
            {"critical": 0, "warning": 1, "info": 2}[i.severity],
            i.rule_id,
        )
    )

    return _dedup(all_issues)


def _walk(
    node: PlanNode,
    root: PlanNode,
    rules: list[tuple[str, callable]],
    out: list[Issue],
) -> None:
    for rule_id, fn in rules:
        try:
            issues = fn(node, root)
            out.extend(issues)
        except Exception:
            pass

    for child in node.children:
        _walk(child, root, rules, out)


def _dedup(issues: list[Issue]) -> list[Issue]:
    seen: set[tuple[str, str | None, str]] = set()
    result: list[Issue] = []
    for issue in issues:
        rel = issue.node.relation_name if issue.node else None
        key = (issue.rule_id, rel, issue.severity)
        if key not in seen:
            seen.add(key)
            result.append(issue)
    return result