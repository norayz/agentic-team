# Agentic Team — From Thought to Production

An autonomous AI software team that turns a one-line prompt into a fully implemented, tested, and deployed project — entirely through GitHub Issues.

## How it works

1. **You open a GitHub Issue** — the title is your task; the body is optional context.
2. **The PM agent** asks clarifying questions, writes a full spec, and routes it for review.
3. **The Team Lead agent** reviews the spec, assigns models to each agent, and approves.
4. **The Architect agent** designs the solution and commits an SDD to its own branch.
5. **The Backend agent** implements the code in an E2B sandbox and opens a PR.
6. **The Code Reviewer agent** reviews the PR, leaves comments, approves or requests changes.
7. **The QA and DevOps agents** run tests and set up infra in parallel — TL merges when all green.

Every step is tracked as GitHub Issue comments and labels. The full conversation is your audit trail.

## The Team

| Agent | Model | Role |
|---|---|---|
| **PM** | Opus | Triages issues, asks clarifying questions, writes specs |
| **Team Lead** | Opus | Reviews every stage, assigns models, routes work, merges PRs |
| **Architect** | Sonnet | Designs systems, picks tech, commits SDD |
| **Backend** | Haiku | Writes and runs code in E2B sandboxes |
| **Code Reviewer** | Sonnet | Reviews PRs for correctness, security, and style |
| **QA** | Haiku | Writes and runs tests, reports results |
| **DevOps** | Haiku | Builds Dockerfiles, writes CI/CD config |

## Setup

### Prerequisites

- Docker and Docker Compose V2 (`docker compose version`)
- [Anthropic API key](https://console.anthropic.com)
- [E2B API key](https://e2b.dev)
- [GitHub personal access token](https://github.com/settings/tokens) with `repo` scope
- [ngrok](https://ngrok.com) (for local webhook delivery)

### 1. Clone and configure

```bash
git clone https://github.com/ylavi-tenb/agentic-team
cd agentic-team
cp .env.example .env
```

Edit `.env` and fill in:

```
ANTHROPIC_API_KEY=sk-ant-...
E2B_API_KEY=e2b_...
GITHUB_TOKEN=ghp_...
GITHUB_REPO=your-org/your-repo      # the repo where issues are created
GITHUB_WEBHOOK_SECRET=your-secret   # any random string — must match webhook config below
```

### 2. Start the services

```bash
docker compose up
```

The orchestrator starts on **port 8000**. You should see all 7 agent containers start and log `[agent] started, polling [...]`.

### 3. Expose the webhook endpoint

In a separate terminal:

```bash
ngrok http 8000
```

Copy the `https://....ngrok-free.app` URL from the ngrok output.

### 4. Configure the GitHub webhook

Go to your GitHub repo → **Settings → Webhooks → Add webhook**:

| Field | Value |
|---|---|
| Payload URL | `https://....ngrok-free.app/webhook` |
| Content type | `application/json` |
| Secret | the value you set for `GITHUB_WEBHOOK_SECRET` |
| Which events | **Issues** only |

Click **Add webhook**. GitHub will send a ping — the orchestrator will log `Webhook received`.

## Start a task

Open a GitHub Issue in your repo:
- **Title** = your task (e.g., `Build a REST API for a todo app`)
- **Body** = any additional context or constraints (optional)
- **Label** = leave blank — the orchestrator sets `new` automatically on creation

**What you'll see within ~30 seconds:**
1. The issue label changes to `pm-drafting`
2. The rich terminal panel shows `PM: Issue #N — pm-drafting`
3. Within 1–2 minutes the PM posts a comment with clarifying questions and sets the label to `waiting-for-human`
4. You reply in the issue comments — PM resumes and writes the full spec
5. Label advances through: `tl-pm-review` → `approved-for-architect` → `in-dev` → `cr-review` → `in-qa` → `tl-final-review` → `done`

## Architecture

- **GitHub Issues = the board** — every task, decision, and status update lives as an issue or comment. Agents communicate exclusively through the GitHub API.
- **Git branches = workspaces** — each agent works on its own named branch (`backend/issue-42`), keeping work isolated until review.
- **E2B = the sandbox** — code execution happens in ephemeral E2B cloud sandboxes, never on your machine.
- **Orchestrator** — a FastAPI service (port 8000) that receives GitHub webhook events and updates the rich terminal display.

## Model overrides

By default each agent uses the model in the table above. To override:

```
PM_MODEL=claude-opus-4-8
TEAM_LEAD_MODEL=claude-opus-4-8
ARCHITECT_MODEL=claude-sonnet-4-6
BACKEND_MODEL=claude-haiku-4-5-20251001
CODE_REVIEWER_MODEL=claude-sonnet-4-6
QA_MODEL=claude-haiku-4-5-20251001
DEVOPS_MODEL=claude-haiku-4-5-20251001
```

## Tech stack

| Technology | Purpose |
|---|---|
| Python 3.12 | Agent runtime |
| FastAPI | Orchestrator webhook server (port 8000) |
| Anthropic SDK | Claude LLM backbone for all agents |
| E2B | Secure cloud code execution sandboxes |
| PyGithub | GitHub Issues / PRs / Comments API |
| rich | Live terminal panel showing agent activity |
| Docker Compose | Multi-container local orchestration |
