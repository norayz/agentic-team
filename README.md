# Agentic Team — From Thought to Production

An autonomous AI software team that turns a one-line prompt into a fully implemented, tested, and deployed project — entirely through GitHub Issues.

## How it works

1. **You open a GitHub Issue** — the title is your task; the body is optional context.
2. **The PM agent** triages the issue, breaks it into subtasks, and labels it for routing.
3. **The Team Lead agent** assigns subtasks to the appropriate specialist agents.
4. **The Architect agent** designs the solution and posts a design doc as an issue comment.
5. **The Backend agent** implements the code in an E2B sandbox, opens a PR from its own branch.
6. **The Code Reviewer agent** reviews the PR, leaves inline comments, requests changes or approves.
7. **The QA and DevOps agents** run tests and deploy — closing the issue when the task is Done.

Every step is tracked as GitHub Issue comments and labels. The full history is your audit trail.

## The Team

| Agent | Role |
|---|---|
| **PM** | Triages issues, writes acceptance criteria, tracks progress |
| **Team Lead** | Decomposes tasks, assigns work, unblocks the team |
| **Architect** | Designs systems, picks tech, posts design docs |
| **Backend** | Writes and runs code inside E2B sandboxes |
| **Code Reviewer** | Reviews PRs for correctness, security, and style |
| **QA** | Writes and runs tests, reports failures |
| **DevOps** | Provisions infra, builds images, deploys services |

## Setup

### Prerequisites

- Docker and Docker Compose
- [Anthropic API key](https://console.anthropic.com)
- [E2B API key](https://e2b.dev)
- [GitHub personal access token](https://github.com/settings/tokens) with `repo`, `issues`, and `pull_requests` scopes

### Install

```bash
git clone https://github.com/ylavi_tenb/agentic-team
cd agentic-team
cp .env.example .env   # fill in your 3 API keys
docker compose up
```

## Start a task

Open a GitHub Issue in this repo:
- **Title** = your task (e.g., `Build a REST API for a todo app`)
- **Body** = any additional context or constraints (optional)

The agents will pick it up automatically and get to work.

## Architecture

- **GitHub Issues = the board** — every task, subtask, decision, and status update lives as an issue or comment. Agents communicate exclusively through the GitHub API.
- **Git branches = workspaces** — each agent works on its own named branch (`agent/backend/issue-42`), keeping work isolated until review.
- **E2B = the sandbox** — code execution happens in ephemeral E2B cloud sandboxes, not on your machine. Safe, reproducible, and disposable.
- **Orchestrator** — a FastAPI service that receives GitHub webhook events and routes them to the correct agent container via HTTP.

## Tech stack

| Technology | Purpose |
|---|---|
| Python 3.12 | Agent runtime |
| FastAPI | Orchestrator webhook server |
| Anthropic SDK | Claude LLM backbone for all agents |
| E2B | Secure cloud code execution sandboxes |
| GitPython | Git branch and commit operations |
| PyGithub | GitHub Issues / PRs / Comments API |
| rich | Pretty terminal output |
| Docker Compose | Multi-container local orchestration |
