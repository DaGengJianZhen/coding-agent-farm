# Swarm Task Pipeline Skills

Cursor skills for dispatching agent work through an n8n workflow:

- `assign-task-to-agent`: create one Linear issue and linked Feishu child task.
- `dispatch-tasks-to-agent`: create multiple issues in dependency order, passing predecessor `linear_issue_id` values as `blocked_by_issue_ids`.

## Install

Copy the skills into your Cursor skills directory:

```bash
cp -R skills/assign-task-to-agent ~/.cursor/skills/
cp -R skills/dispatch-tasks-to-agent ~/.cursor/skills/
```

## Single Task

```bash
python skills/assign-task-to-agent/scripts/create_issue.py \
  --parent-task-url "https://yylfzxcmpc.feishu.cn/record/..." \
  --title "实现登录接口" \
  --description "基于数据库 schema 实现登录接口。" \
  --task-type backend \
  --repository "openclaw/web"
```

## Multiple Tasks

```bash
python skills/dispatch-tasks-to-agent/scripts/create_issue_list.py \
  --spec skills/dispatch-tasks-to-agent/example-spec.json \
  --dry-run
```

Remove `--dry-run` to create the issues.
