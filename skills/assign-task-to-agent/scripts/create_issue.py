#!/usr/bin/env python3
import argparse
import json
import os
import sys
import urllib.error
import urllib.request


DEFAULT_WEBHOOK = "https://wildmaker.app.n8n.cloud/webhook/agent-to-linear"
DEFAULT_APP_TOKEN = "EmPebJ3EAatSwusFGzLcDpkOnn0"
DEFAULT_TABLE_ID = "tbleoohWAsivMCQt"
DEFAULT_TEAM_ID = "c9812f44-3c7c-42c8-b29a-5be7e155fe7a"

FIELD_NAMES = {
    "parent_link": "父记录",
    "title": "任务标题",
    "description": "需求描述",
    "linear_issue_id": "Linear Issue ID",
    "linear_url": "Linear URL",
    "agent_status": "Agent 状态",
    "task_type": "任务类型",
    "priority": "优先级",
    "repository": "目标仓库",
}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Create a Linear issue and linked Feishu child record via n8n."
    )
    parser.add_argument("--parent-task-url", required=True, help="Feishu parent record URL.")
    parser.add_argument("--title", required=True, help="Linear issue title.")
    parser.add_argument("--description", required=True, help="Linear issue description.")
    parser.add_argument("--priority", default="Medium", help="Issue priority. Default: Medium.")
    parser.add_argument("--task-type", default="frontend", help="Task type field value.")
    parser.add_argument("--repository", default="", help="Target repository field value.")
    parser.add_argument("--team-id", default=os.getenv("LINEAR_TEAM_ID", DEFAULT_TEAM_ID))
    parser.add_argument("--model-label", default="use-codex")
    parser.add_argument(
        "--blocked-by-issue-id",
        action="append",
        default=[],
        help="Linear issue ID that blocks this issue. Repeat for multiple blockers.",
    )
    parser.add_argument(
        "--agent-enabled",
        default="true",
        choices=["true", "false"],
        help="Whether the downstream agent should be enabled. Default: true.",
    )
    parser.add_argument(
        "--webhook",
        default=os.getenv("N8N_AGENT_TO_LINEAR_WEBHOOK", DEFAULT_WEBHOOK),
        help="n8n webhook URL. Defaults to production endpoint.",
    )
    parser.add_argument(
        "--app-token",
        default=os.getenv("FEISHU_APP_TOKEN", DEFAULT_APP_TOKEN),
        help="Feishu bitable app token.",
    )
    parser.add_argument(
        "--table-id",
        default=os.getenv("FEISHU_TABLE_ID", DEFAULT_TABLE_ID),
        help="Feishu bitable table ID.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print payload without sending.")
    parser.add_argument("--timeout", type=int, default=120, help="Request timeout in seconds.")
    return parser.parse_args()


def build_payload(args):
    issue = {
        "title": args.title,
        "description": args.description,
        "priority": args.priority,
        "task_type": args.task_type,
        "team_id": args.team_id,
        "model_label": args.model_label,
        "agent_enabled": args.agent_enabled == "true",
    }
    if args.repository:
        issue["repository"] = args.repository
    if args.blocked_by_issue_id:
        issue["blocked_by_issue_ids"] = args.blocked_by_issue_id

    return {
        "parent_task_url": args.parent_task_url,
        "feishu": {
            "app_token": args.app_token,
            "table_id": args.table_id,
            "field_names": FIELD_NAMES,
        },
        "issue": issue,
    }


def post_json(url, payload, timeout):
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={"Content-Type": "application/json"},
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8")
            return response.status, body
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        return error.code, body


def main():
    args = parse_args()
    payload = build_payload(args)

    if args.dry_run:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    status, body = post_json(args.webhook, payload, args.timeout)
    print(f"HTTP_STATUS:{status}")
    if body:
        try:
            parsed = json.loads(body)
            print(json.dumps(parsed, ensure_ascii=False, indent=2))
        except json.JSONDecodeError:
            print(body)

    if status < 200 or status >= 300:
        return 1

    if body:
        try:
            parsed = json.loads(body)
            data = parsed.get("data") or {}
            if data.get("feishu_subtask_created") and not data.get("feishu_child_record_id"):
                print(
                    "WARNING: Feishu subtask was reported created, but child record ID is empty.",
                    file=sys.stderr,
                )
        except json.JSONDecodeError:
            pass

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
