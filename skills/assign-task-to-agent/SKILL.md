---
name: assign-task-to-agent
description: Assign one task to an agent by creating a Linear issue and linked Feishu subtask through the user's n8n agent-to-linear webhook. Use when the user asks to give one task to an agent, create one Linear issue, create one child task, or trigger the single-task n8n workflow.
---

# Assign Task To Agent

## Purpose

Use this skill to give one task to an agent by creating a Linear issue and a linked child record in the Feishu bitable through the n8n `agent-to-linear` webhook.

Default production webhook:

```text
https://wildmaker.app.n8n.cloud/webhook/agent-to-linear
```

Only use the test webhook when the user explicitly asks for a test request and has clicked **Execute workflow** in n8n:

```text
https://wildmaker.app.n8n.cloud/webhook-test/agent-to-linear
```

## Required Inputs

Before calling the webhook, ensure these values are known:

- `parent_task_url`: Feishu parent record URL.
- `issue.title`: Linear issue title.
- `issue.description`: Linear issue description or implementation brief. It must include the base branch on its own line.

## Base Branch In Description

Every created issue must include the target base branch in `issue.description`. Prefer a single independent line near the top:

```text
Base branch: release/2026.05
```

Accepted forms include `Base branch: develop`, `Base branch: release/2026.05`, `基准分支: release/2026.05`, and list items such as `- Base branch: hotfix/1.0.3`. Use `:` as the separator.

Use these defaults unless the user provides overrides:

- `feishu.app_token`: `EmPebJ3EAatSwusFGzLcDpkOnn0`
- `feishu.table_id`: `tbleoohWAsivMCQt`
- `issue.team_id`: `c9812f44-3c7c-42c8-b29a-5be7e155fe7a`
- `issue.priority`: `Medium`
- `issue.model_label`: `use-codex`
- `issue.agent_enabled`: `true`

## Feishu Field Names

Use the real table field names below. Do not send the older names `父任务`, `任务名称`, or `任务描述`.

```json
{
  "parent_link": "父记录",
  "title": "任务标题",
  "description": "需求描述",
  "linear_issue_id": "Linear Issue ID",
  "linear_url": "Linear URL",
  "agent_status": "Agent 状态",
  "task_type": "任务类型",
  "priority": "优先级",
  "repository": "目标仓库",
  "base_branch": "Base Branch"
}
```

## Preferred Execution

Use the helper script:

```bash
python ~/.cursor/skills/assign-task-to-agent/scripts/create_issue.py \
  --parent-task-url "https://yylfzxcmpc.feishu.cn/record/..." \
  --title "实现用户登录页" \
  --description "根据 PRD 完成登录页前端开发和接口联调。" \
  --base-branch "release/2026.05" \
  --task-type frontend \
  --repository "openclaw/web"
```

To call the test webhook instead:

```bash
N8N_AGENT_TO_LINEAR_WEBHOOK="https://wildmaker.app.n8n.cloud/webhook-test/agent-to-linear" \
python ~/.cursor/skills/assign-task-to-agent/scripts/create_issue.py \
  --parent-task-url "https://yylfzxcmpc.feishu.cn/record/..." \
  --title "测试 issue" \
  --description "webhook-test 联调请求。"
```

## Manual Payload

If not using the helper script, send this JSON shape:

```json
{
  "parent_task_url": "https://yylfzxcmpc.feishu.cn/record/Kq3crfLZBeE5fLccEhtctLQUnYe",
  "feishu": {
    "app_token": "EmPebJ3EAatSwusFGzLcDpkOnn0",
    "table_id": "tbleoohWAsivMCQt",
    "field_names": {
      "parent_link": "父记录",
      "title": "任务标题",
      "description": "需求描述",
      "linear_issue_id": "Linear Issue ID",
      "linear_url": "Linear URL",
      "agent_status": "Agent 状态",
      "task_type": "任务类型",
      "priority": "优先级",
      "repository": "目标仓库",
      "base_branch": "Base Branch"
    }
  },
  "issue": {
    "title": "实现用户登录页",
    "description": "根据 PRD 完成登录页前端开发和接口联调。\n\nBase branch: release/2026.05",
    "priority": "Medium",
    "task_type": "frontend",
    "repository": "openclaw/web",
    "team_id": "c9812f44-3c7c-42c8-b29a-5be7e155fe7a",
    "model_label": "use-codex",
    "agent_enabled": true
  }
}
```

## Success Criteria

Treat the request as successful when the response has:

- HTTP status `200`
- `data.ok: true`
- `data.linear_identifier` or `data.linear_issue_id`
- `data.feishu_subtask_created: true`
- `data.feishu_child_record_id` is non-empty

If `feishu_child_record_id` is `null`, report that Linear creation may have succeeded but Feishu child record ID was not confirmed.
