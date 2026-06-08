---
name: create-symphony-linear-issue
description: Create Linear issues for Symphony agents using the user's own Linear MCP. Use when asked to create agent-ready Linear tickets, issues, or tasks, route work to Symphony, set branchName, base branch, labels, dependencies, or prepare Linear issue bodies for agent execution.
---

# Create Symphony Linear Issue

## Purpose

Use this skill to create Linear issues that Symphony agents can discover and execute. The issue must be created through the user's own Linear MCP connection, in the Linear team/project currently monitored by Symphony.

## Preflight

Before creating the issue:

- Confirm the user's Linear MCP is configured and authenticated to the intended Linear workspace.
- Read the relevant Linear MCP tool schema before calling it.
- Identify the Symphony-monitored Linear team and project. Do not create the issue in a workspace, team, or project that Symphony does not monitor.
- Confirm the dispatch label Symphony uses, for example `symphony` or the project's agreed scheduling label.
- Confirm whether the task should branch from `main` or another base branch.

## Required Issue Fields

Set these fields whenever the Linear MCP supports them:

- Team/project: the current Symphony-monitored Linear team/project.
- Status: `Todo`. Do not create new work in `Backlog`; the current workflow skips Backlog tasks.
- Title: short, action-oriented, and suitable for branch-name generation. Start with a verb, for example `Fix duplicate workpad comment updates`.
- `branchName`: explicit branch name in the format `<ticket-key-or-scope>/<short-kebab-title>`.
- Labels: include the Symphony dispatch label, for example `symphony`.
- Description: include Goal, Scope, Acceptance Criteria, and Validation.

## Branch Name

If the Linear MCP supports a `branchName` field, set it explicitly.

Recommended format:

```text
<ticket-key-or-scope>/<short-kebab-title>
```

Examples:

```text
sym/fix-workpad-comment-updates
mt-625/fix-linear-ticket-routing
```

Rules:

- Use only lowercase letters, numbers, hyphens, and slashes.
- Do not use spaces, Chinese characters, or special characters.
- If `branchName` is missing, Symphony may not read a clear `SYMPHONY_BRANCH_NAME`, and later hook/PR flow may fall back to default logic.

## Base Branch

If development should not start from `main`, write the base branch as a separate line in the issue description:

```text
Base branch: release/1.2
```

Chinese is also accepted:

```text
基准分支: release/1.2
```

If omitted, Symphony treats the task as based on `main`.

## Labels And Model Selection

- Add the current Symphony dispatch label, for example `symphony` or the project-specific scheduling label.
- To request a model, add one `model-*` label, for example `model-o3-pro`.
- Do not add multiple `model-*` labels. If multiple exist, the system takes the first and records a warning.
- Avoid unrelated labels that may trigger other automation.

## Description Template

Use this structure for the issue body:

```markdown
## Goal
[State the user-visible or engineering outcome.]

## Scope
[List what is in scope and any explicit non-goals.]

## Acceptance Criteria
- [ ] [Observable requirement.]
- [ ] [Observable requirement.]

## Validation
- [ ] [Command, manual check, or review step.]
- [ ] [Command, manual check, or review step.]
```

Include a `Base branch: ...` line near the top when the base is not `main`.

## Dependencies

If the task depends on another ticket, create a Linear relationship such as `blockedBy` or a related issue relation. Do not only mention dependencies in the description. Symphony uses blockers to decide whether a task is executable.

## PR Conventions

- Agent-created GitHub PRs must include the `symphony` label.
- Attach or link the PR URL to the Linear issue through Linear attachment/link fields. Do not only paste the PR URL in a comment.

## Do Not Use Comments For The Plan

Use the issue body to describe requirements. Do not put the implementation plan, progress, or validation results into ordinary Linear comments. The agent maintains execution notes in the `## Codex Workpad` comment.

## Final Check

Before reporting success, verify:

- The issue is in the Symphony-monitored team/project.
- Status is `Todo`, not `Backlog`.
- The title starts with a verb and is short.
- `branchName` is present when the MCP supports it.
- Required Symphony label is present.
- At most one `model-*` label is present.
- Non-main base branch is written on its own line in the description.
- Dependencies are represented with Linear issue relations.
