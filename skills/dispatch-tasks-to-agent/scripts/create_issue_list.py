#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


SKILLS_DIR = Path(__file__).resolve().parents[2]
CREATE_ISSUE_SCRIPT = SKILLS_DIR / "assign-task-to-agent" / "scripts" / "create_issue.py"


def parse_args():
    parser = argparse.ArgumentParser(
        description="Create a dependency-aware list of Linear issues via assign-task-to-agent."
    )
    parser.add_argument("--spec", required=True, help="Path to issue list JSON spec.")
    parser.add_argument("--dry-run", action="store_true", help="Print creation plan only.")
    parser.add_argument(
        "--continue-from",
        help="Optional JSON result map from a previous partial run.",
    )
    return parser.parse_args()


def load_json(path):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def normalize_issues(spec):
    issues = spec.get("issues")
    if not isinstance(issues, list) or not issues:
        raise ValueError("spec.issues must be a non-empty array")

    seen = set()
    normalized = []
    for issue in issues:
        key = issue.get("key")
        if not key:
            raise ValueError("each issue must include a unique key")
        if key in seen:
            raise ValueError(f"duplicate issue key: {key}")
        seen.add(key)
        normalized.append(issue)
    return normalized


def build_layers(issues, already_created):
    issue_by_key = {issue["key"]: issue for issue in issues}
    unresolved = {issue["key"] for issue in issues if issue["key"] not in already_created}
    layers = []
    resolved = set(already_created)

    while unresolved:
        ready = []
        for key in sorted(unresolved):
            deps = set(issue_by_key[key].get("depends_on", []))
            missing = deps - set(issue_by_key) - set(already_created)
            if missing:
                raise ValueError(f"{key} depends on unknown issue key(s): {sorted(missing)}")
            if deps <= resolved:
                ready.append(key)

        if not ready:
            cycle_keys = sorted(unresolved)
            raise ValueError(f"dependency cycle or unresolved dependencies: {cycle_keys}")

        layers.append(ready)
        unresolved -= set(ready)
        resolved |= set(ready)

    return layers, issue_by_key


def external_blockers(spec):
    blockers = spec.get("external_blockers", {})
    if not isinstance(blockers, dict):
        raise ValueError("spec.external_blockers must be an object when provided")
    return blockers


def result_id(result):
    return result.get("linear_issue_id") or result.get("data", {}).get("linear_issue_id")


def description_has_base_branch(description):
    for line in str(description).splitlines():
        stripped = line.strip()
        if stripped.startswith("-"):
            stripped = stripped[1:].strip()
        if stripped.lower().startswith(("base branch:", "基准分支:")):
            return True
    return False


def command_for_issue(spec, issue, blocker_ids):
    defaults = spec.get("defaults", {})
    parent_task_url = issue.get("parent_task_url") or spec.get("parent_task_url")
    if not parent_task_url:
        raise ValueError(f"{issue['key']} is missing parent_task_url")

    description = issue.get("description", "")
    if not description:
        raise ValueError(f"{issue['key']} is missing description")

    base_branch = issue.get("base_branch", defaults.get("base_branch", ""))
    if not base_branch and not description_has_base_branch(description):
        raise ValueError(
            f"{issue['key']} is missing base_branch or a standalone "
            "description line such as 'Base branch: release/2026.05'"
        )

    cmd = [
        sys.executable,
        str(CREATE_ISSUE_SCRIPT),
        "--parent-task-url",
        parent_task_url,
        "--title",
        issue["title"],
        "--description",
        description,
        "--priority",
        issue.get("priority", defaults.get("priority", "Medium")),
        "--task-type",
        issue.get("task_type", defaults.get("task_type", "frontend")),
        "--model-label",
        issue.get("model_label", defaults.get("model_label", "use-codex")),
        "--agent-enabled",
        str(issue.get("agent_enabled", defaults.get("agent_enabled", True))).lower(),
    ]

    team_id = issue.get("team_id", defaults.get("team_id"))
    if team_id:
        cmd.extend(["--team-id", team_id])

    repository = issue.get("repository", defaults.get("repository", ""))
    if repository:
        cmd.extend(["--repository", repository])

    if base_branch:
        cmd.extend(["--base-branch", base_branch])

    webhook = issue.get("webhook") or spec.get("webhook")
    if webhook:
        cmd.extend(["--webhook", webhook])

    app_token = issue.get("app_token") or spec.get("feishu", {}).get("app_token")
    if app_token:
        cmd.extend(["--app-token", app_token])

    table_id = issue.get("table_id") or spec.get("feishu", {}).get("table_id")
    if table_id:
        cmd.extend(["--table-id", table_id])

    for blocker_id in blocker_ids:
        cmd.extend(["--blocked-by-issue-id", blocker_id])

    return cmd


def parse_create_output(output):
    lines = output.splitlines()
    json_start = None
    for idx, line in enumerate(lines):
        if line.strip().startswith("{"):
            json_start = idx
            break
    if json_start is None:
        raise ValueError("create_issue.py did not return JSON")

    parsed = json.loads("\n".join(lines[json_start:]))
    data = parsed.get("data") or {}
    if not data.get("linear_issue_id"):
        raise ValueError("response missing data.linear_issue_id")
    return data


def main():
    args = parse_args()
    spec = load_json(args.spec)
    issues = normalize_issues(spec)

    created = {}
    if args.continue_from:
        previous = load_json(args.continue_from)
        created.update(previous.get("created", previous))
    created.update(external_blockers(spec))

    layers, issue_by_key = build_layers(issues, created)

    plan = [
        {
            "layer": idx + 1,
            "issues": [
                {
                    "key": key,
                    "title": issue_by_key[key]["title"],
                    "depends_on": issue_by_key[key].get("depends_on", []),
                }
                for key in layer
            ],
        }
        for idx, layer in enumerate(layers)
    ]

    if args.dry_run:
        print(json.dumps({"plan": plan}, ensure_ascii=False, indent=2))
        return 0

    print(json.dumps({"plan": plan}, ensure_ascii=False, indent=2))

    for layer in layers:
        for key in layer:
            issue = issue_by_key[key]
            blocker_ids = []
            for dep_key in issue.get("depends_on", []):
                blocker_id = result_id(created[dep_key])
                if not blocker_id:
                    raise ValueError(f"created predecessor {dep_key} has no Linear issue ID")
                blocker_ids.append(blocker_id)

            cmd = command_for_issue(spec, issue, blocker_ids)
            env = os.environ.copy()
            completed = subprocess.run(
                cmd,
                env=env,
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            if completed.stdout:
                print(completed.stdout, end="")
            if completed.stderr:
                print(completed.stderr, end="", file=sys.stderr)
            if completed.returncode != 0:
                print(
                    json.dumps({"created": created}, ensure_ascii=False, indent=2),
                    file=sys.stderr,
                )
                return completed.returncode

            created[key] = parse_create_output(completed.stdout)

    print(json.dumps({"created": created}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
