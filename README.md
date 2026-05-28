# swarm-task-pipeline-skills

## n8n workflows

| File | Description |
|------|-------------|
| [`n8n/workflows/gVKcyQFm6LUH2HQ1.agent-to-linear.workflow.json`](n8n/workflows/gVKcyQFm6LUH2HQ1.agent-to-linear.workflow.json) | n8n 可导入的 workflow 定义（节点、连接、设置） |
| [`n8n/workflows/gVKcyQFm6LUH2HQ1.agent-to-linear.meta.json`](n8n/workflows/gVKcyQFm6LUH2HQ1.agent-to-linear.meta.json) | 导出元数据（Webhook 路径、`triggerInfo` 等） |

Workflow：**本地 Agent 创建 Linear Issue、Blocked By 关系并在飞书原表创建子任务**  
Production webhook: `POST https://wildmaker.app.n8n.cloud/webhook/agent-to-linear`

## Skill usage guide

This repository provides Cursor skills for assigning implementation work to coding agents through Linear and Feishu:

- [`skills/assign-task-to-agent/SKILL.md`](skills/assign-task-to-agent/SKILL.md): create one Linear issue and linked Feishu child task.
- [`skills/dispatch-tasks-to-agent/SKILL.md`](skills/dispatch-tasks-to-agent/SKILL.md): create multiple Linear issues from a prepared task list, including dependency relations.

### Required base branch

Every task created through these skills must explicitly state the base branch in the task description. Put it on a single independent line near the top. Recommended format:

```text
Base branch: release/2026.05
```

Accepted examples:

- `Base branch: develop`
- `Base branch: release/2026.05`
- `基准分支: release/2026.05`
- `- Base branch: hotfix/1.0.3`

Example:

```markdown
## Context
修复登录在 staging 上的回归。
Base branch: release/2026.05

## Acceptance
```

The base branch tells the downstream agent where to branch from and which remote history contains the task context. Do not dispatch a task until the referenced base branch exists on remote and contains the documents needed to complete that task.

### Single task dispatch

Use `assign-task-to-agent` when assigning one independent task. Before creating the task, make sure:

- The task description includes the base branch.
- The referenced base branch has already been pushed to remote.
- Any required PRD, design document, implementation plan, or task-specific context has already been committed and pushed to that base branch.

### Batch task dispatch

Use `dispatch-tasks-to-agent` when assigning multiple tasks in one batch. Before creating the batch, complete this preparation work:

1. Create the shared base branch first, for example a `feature/*` branch.
2. Break the feature into a concrete task list before dispatching.
3. Commit and push the base branch to remote.
4. Commit and push the task list and all complete reference documents needed by the tasks to remote.
5. Mark the dependency relationship between tasks clearly before batch creation.

The central agent executes tasks according to the dependency graph. Tasks without dependencies can start first. A task that depends on another task must wait until all of its predecessors have been created successfully, and the dispatcher will translate those dependencies into Linear `blocked_by` relations.

In the batch spec, use stable local keys and `depends_on` to express dependencies:

```json
{
  "defaults": {
    "base_branch": "feature/login-flow"
  },
  "issues": [
    {
      "key": "auth-schema",
      "title": "Design login schema",
      "description": "Define user table fields and indexes."
    },
    {
      "key": "login-api",
      "title": "Implement login API",
      "description": "Implement the login endpoint based on the schema.",
      "depends_on": ["auth-schema"]
    }
  ]
}
```

Do not batch-dispatch a loose idea list. The feature branch, task list, dependency graph, and full task documentation should all be available in remote before the first Linear issue is created.

## n8n MCP (Cursor)

This project connects to your n8n Cloud **instance-level MCP** endpoint.

### Setup

1. In n8n: **Settings → Instance-level MCP** → enable MCP access.
2. Open **Connection details → Access Token** and copy your personal MCP token (shown once).
3. Copy `.env.example` to `.env` and set `N8N_MCP_TOKEN`.
4. In at least one workflow: **Settings → Available in MCP** (or enable from Instance-level MCP page).
5. Restart Cursor (or reload MCP in **Settings → Tools & MCP**).

Config lives in [`.cursor/mcp.json`](.cursor/mcp.json). Cursor does not reliably resolve `${env:...}` inside HTTP `headers`, so this project uses [`.cursor/scripts/n8n-mcp.sh`](.cursor/scripts/n8n-mcp.sh) (`supergateway` stdio bridge) to load `N8N_MCP_TOKEN` from `.env`. Do not commit `.env`.

### Troubleshooting Cursor `Malformed Bearer token`

If MCP logs show `Malformed Bearer token` or `connected=false`, Cursor likely sent the literal string `${env:N8N_MCP_TOKEN}` instead of your token. Reload MCP after pulling the latest config (stdio bridge script). In **Settings → Tools & MCP**, disable and re-enable `n8n-mcp`, or restart Cursor.

### Verify connectivity

```bash
export N8N_MCP_TOKEN="your-token"
curl -sS -X POST "https://wildmaker.app.n8n.cloud/mcp-server/http" \
  -H "Authorization: Bearer $N8N_MCP_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}'
```

A successful response includes MCP `initialize` result JSON (not `Unauthorized`).

### Docs

- [n8n: Accessing and using n8n MCP server](https://docs.n8n.io/advanced-ai/accessing-n8n-mcp-server/)
