---
name: dispatch-tasks-to-agent
description: Dispatch multiple tasks to agents by creating multiple Linear issues and linked Feishu subtasks from an issues list through repeated assign-task-to-agent calls. Use when the user provides a list of tasks, backlog items, dependent issues, or asks to distribute multiple tasks to agents.
---

# Dispatch Tasks To Agent

## Purpose

Use this skill to dispatch multiple tasks to agents from an issues list through repeated `assign-task-to-agent` calls. It must call the n8n workflow once per issue. It creates independent issues first, records their returned `linear_issue_id`, then creates downstream issues with `blocked_by_issue_ids`.

## Dependency Rule

- Issues with no `depends_on` are independent and should be created first.
- Issues with `depends_on` must wait until all predecessor issues have been created successfully.
- For each dependent issue, convert `depends_on` issue keys into predecessor `linear_issue_id` values and send them as `issue.blocked_by_issue_ids`.
- Use `linear_issue_id` for dependency relations. `linear_identifier` such as `INS-123` is only for display and human reporting.
- Stop immediately if any predecessor issue fails, because downstream relation creation would be invalid.

## Spec Format

Create a JSON spec file and pass it to the helper script:

```json
{
  "parent_task_url": "https://yylfzxcmpc.feishu.cn/record/Kq3crfLZBeE5fLccEhtctLQUnYe",
  "defaults": {
    "priority": "Medium",
    "task_type": "frontend",
    "repository": "openclaw/web",
    "team_id": "c9812f44-3c7c-42c8-b29a-5be7e155fe7a",
    "model_label": "use-codex",
    "agent_enabled": true
  },
  "issues": [
    {
      "key": "auth-schema",
      "title": "设计登录数据结构",
      "description": "确认登录接口需要的用户表字段和索引。"
    },
    {
      "key": "login-api",
      "title": "实现登录接口",
      "description": "基于数据库 schema 实现登录接口。",
      "task_type": "backend",
      "depends_on": ["auth-schema"]
    }
  ]
}
```

`key` is local-only and must be unique. Use it to express dependencies. Do not put Linear IDs in `depends_on`; the script resolves them after creation.

## Execute

```bash
python ~/.cursor/skills/dispatch-tasks-to-agent/scripts/create_issue_list.py \
  --spec ./issues.json
```

Dry-run first when converting a new issues list:

```bash
python ~/.cursor/skills/dispatch-tasks-to-agent/scripts/create_issue_list.py \
  --spec ./issues.json \
  --dry-run
```

To use n8n test webhook, set:

```bash
N8N_AGENT_TO_LINEAR_WEBHOOK="https://wildmaker.app.n8n.cloud/webhook-test/agent-to-linear"
```

n8n test webhooks usually accept only one request after **Execute workflow** is clicked. For a full batch, prefer the production webhook. If testing dependency behavior through the test webhook, create one issue per n8n execution and resume with `--continue-from`.

## Output

The script prints a result map:

```json
{
  "created": {
    "auth-schema": {
      "linear_issue_id": "...",
      "linear_identifier": "INS-123",
      "linear_url": "...",
      "feishu_child_record_id": "rec..."
    }
  }
}
```

Keep this map if a later run needs to create more dependent issues from already-created predecessors.

## Safety

- Do not retry a full batch blindly after partial success, or duplicate issues may be created.
- If a run stops midway, use the printed result map to build a smaller follow-up spec containing only not-yet-created issues and use `external_blockers` for already-created predecessors.
- If the user wants all issues created even when one dependency fails, ask before changing this fail-fast behavior.
