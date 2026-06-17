"""Shared tool schemas, executors, poll loop, and agent service harness."""
import os
import time
import logging
from pathlib import Path
from typing import Callable

logger = logging.getLogger(__name__)

# ── Issue tool schemas ─────────────────────────────────────────────────────────

TOOL_GET_ISSUE: dict = {
    "name": "get_issue",
    "description": "Fetch issue title, body, labels, and state",
    "input_schema": {
        "type": "object",
        "properties": {"issue_number": {"type": "integer"}},
        "required": ["issue_number"],
    },
}

TOOL_GET_COMMENTS: dict = {
    "name": "get_comments",
    "description": "Fetch all comments on an issue in chronological order",
    "input_schema": {
        "type": "object",
        "properties": {"issue_number": {"type": "integer"}},
        "required": ["issue_number"],
    },
}

TOOL_POST_COMMENT: dict = {
    "name": "post_comment",
    "description": "Post a comment on an issue",
    "input_schema": {
        "type": "object",
        "properties": {
            "issue_number": {"type": "integer"},
            "message": {"type": "string"},
        },
        "required": ["issue_number", "message"],
    },
}

TOOL_UPDATE_LABEL: dict = {
    "name": "update_label",
    "description": "Replace the current status label on an issue to advance the workflow",
    "input_schema": {
        "type": "object",
        "properties": {
            "issue_number": {"type": "integer"},
            "new_label": {"type": "string"},
        },
        "required": ["issue_number", "new_label"],
    },
}

TOOL_UPDATE_ISSUE_BODY: dict = {
    "name": "update_issue_body",
    "description": "Overwrite the issue body (use for spec, SDD, or final summary)",
    "input_schema": {
        "type": "object",
        "properties": {
            "issue_number": {"type": "integer"},
            "body": {"type": "string"},
        },
        "required": ["issue_number", "body"],
    },
}

# ── Git tool schemas ───────────────────────────────────────────────────────────

_FILE_ITEM = {
    "type": "object",
    "properties": {"path": {"type": "string"}, "content": {"type": "string"}},
    "required": ["path", "content"],
}

TOOL_CREATE_BRANCH: dict = {
    "name": "create_branch",
    "description": "Create a git branch for this task (e.g. backend/issue-42)",
    "input_schema": {
        "type": "object",
        "properties": {
            "issue_number": {"type": "integer"},
            "branch_name": {"type": "string", "description": "Override; defaults to {role}/issue-{n}"},
        },
        "required": ["issue_number"],
    },
}

TOOL_COMMIT_FILES: dict = {
    "name": "commit_files",
    "description": "Commit one or more files to a branch",
    "input_schema": {
        "type": "object",
        "properties": {
            "branch": {"type": "string"},
            "files": {"type": "array", "items": _FILE_ITEM},
            "message": {"type": "string"},
        },
        "required": ["branch", "files", "message"],
    },
}

TOOL_OPEN_PR: dict = {
    "name": "open_pr",
    "description": "Open a pull request from a branch to main",
    "input_schema": {
        "type": "object",
        "properties": {
            "branch": {"type": "string"},
            "title": {"type": "string"},
            "body": {"type": "string"},
            "issue_number": {"type": "integer"},
        },
        "required": ["branch", "title", "body"],
    },
}

TOOL_GET_PR_FILES: dict = {
    "name": "get_pr_files",
    "description": "List files changed in a PR with diffs; optionally include full file content",
    "input_schema": {
        "type": "object",
        "properties": {
            "pr_number": {"type": "integer"},
            "include_content": {"type": "boolean", "description": "Fetch full file content from the PR branch"},
        },
        "required": ["pr_number"],
    },
}

TOOL_POST_PR_REVIEW: dict = {
    "name": "post_pr_review",
    "description": "Submit a PR review verdict",
    "input_schema": {
        "type": "object",
        "properties": {
            "pr_number": {"type": "integer"},
            "body": {"type": "string"},
            "event": {"type": "string", "enum": ["APPROVE", "REQUEST_CHANGES", "COMMENT"]},
        },
        "required": ["pr_number", "body", "event"],
    },
}

TOOL_MERGE_PR: dict = {
    "name": "merge_pr",
    "description": "Merge a pull request",
    "input_schema": {
        "type": "object",
        "properties": {
            "pr_number": {"type": "integer"},
            "merge_method": {"type": "string", "enum": ["merge", "squash", "rebase"]},
        },
        "required": ["pr_number"],
    },
}

TOOL_BRANCH_EXISTS: dict = {
    "name": "branch_exists",
    "description": "Check whether a git branch exists",
    "input_schema": {
        "type": "object",
        "properties": {"branch_name": {"type": "string"}},
        "required": ["branch_name"],
    },
}

TOOL_CREATE_SUB_ISSUE: dict = {
    "name": "create_sub_issue",
    "description": "Create a child issue linked to the parent",
    "input_schema": {
        "type": "object",
        "properties": {
            "parent_issue_number": {"type": "integer"},
            "title": {"type": "string"},
            "body": {"type": "string"},
            "label": {"type": "string"},
        },
        "required": ["parent_issue_number", "title", "body"],
    },
}

# ── Sandbox tool schemas ───────────────────────────────────────────────────────

TOOL_RUN_PYTHON: dict = {
    "name": "run_python",
    "description": "Execute Python code in an E2B sandbox; returns stdout + stderr",
    "input_schema": {
        "type": "object",
        "properties": {
            "code": {"type": "string"},
            "timeout": {"type": "integer", "description": "Seconds, default 30"},
        },
        "required": ["code"],
    },
}

TOOL_RUN_PROJECT: dict = {
    "name": "run_project",
    "description": "Run a shell command in the E2B sandbox (use for tests and builds)",
    "input_schema": {
        "type": "object",
        "properties": {
            "command": {"type": "string"},
            "timeout": {"type": "integer", "description": "Seconds, default 120"},
        },
        "required": ["command"],
    },
}

TOOL_RUN_COMMAND: dict = {
    "name": "run_command",
    "description": "Run a shell command in the E2B sandbox (use to verify docker builds or infra scripts)",
    "input_schema": {
        "type": "object",
        "properties": {
            "command": {"type": "string"},
            "timeout": {"type": "integer", "description": "Seconds, default 120"},
        },
        "required": ["command"],
    },
}

# ── Composed tool sets ─────────────────────────────────────────────────────────

TOOLS_ISSUE: list[dict] = [
    TOOL_GET_ISSUE,
    TOOL_GET_COMMENTS,
    TOOL_POST_COMMENT,
    TOOL_UPDATE_LABEL,
    TOOL_UPDATE_ISSUE_BODY,
]

TOOLS_GIT: list[dict] = [TOOL_CREATE_BRANCH, TOOL_COMMIT_FILES, TOOL_OPEN_PR]

# ── Shared executors ───────────────────────────────────────────────────────────


def execute_issue_tools(name: str, inputs: dict, agent_name: str) -> str | None:
    """Handle the 5 common issue tools. Returns None if name is not recognised."""
    from tools.github_issues import (
        get_issue, get_comments, post_comment, update_label, update_issue_body,
    )
    if name == "get_issue":
        return str(get_issue(inputs["issue_number"]))
    if name == "get_comments":
        return str(get_comments(inputs["issue_number"]))
    if name == "post_comment":
        post_comment(inputs["issue_number"], agent_name, inputs["message"])
        return "Comment posted"
    if name == "update_label":
        update_label(inputs["issue_number"], inputs["new_label"])
        return f"Label updated to {inputs['new_label']}"
    if name == "update_issue_body":
        update_issue_body(inputs["issue_number"], inputs["body"])
        return "Issue body updated"
    return None


def execute_git_tools(name: str, inputs: dict, agent_name: str) -> str | None:
    """Handle create_branch / commit_files / open_pr. Returns None if not recognised."""
    from tools.git import agent_branch, create_branch, commit_files, open_pr
    if name == "create_branch":
        branch = inputs.get("branch_name") or agent_branch(agent_name, inputs["issue_number"])
        return create_branch(branch)
    if name == "commit_files":
        commit_files(inputs["branch"], inputs["files"], inputs["message"])
        return f"Committed {len(inputs['files'])} file(s) to {inputs['branch']}"
    if name == "open_pr":
        pr_number = open_pr(
            inputs["branch"], inputs["title"], inputs["body"], inputs.get("issue_number")
        )
        return f"PR #{pr_number} opened"
    return None


# ── Poll loop ──────────────────────────────────────────────────────────────────


def poll(
    agent_name: str,
    labels: list[str],
    handler: Callable[[dict], None],
    interval: int = 10,
) -> None:
    """Blocking poll loop. Skips issues already in-flight for this agent."""
    from tools.github_issues import get_issues_by_label

    logging.basicConfig(level=logging.INFO)
    logger.info(f"[{agent_name}] started, polling {labels}")

    in_progress: set[int] = set()

    while True:
        try:
            for label in labels:
                for issue in get_issues_by_label(label):
                    n = issue["number"]
                    if n in in_progress:
                        continue
                    in_progress.add(n)
                    logger.info(f"[{agent_name}] picking up issue #{n} ({label})")
                    try:
                        handler(issue)
                    finally:
                        in_progress.discard(n)
        except Exception:
            logger.exception(f"[{agent_name}] poll error")
        time.sleep(interval)


# ── Agent service harness ──────────────────────────────────────────────────────


def run_agent_service(
    agent_name: str,
    poll_labels: list[str],
    tools: list[dict],
    tool_executor: Callable,
    prompt_file: Path,
    *,
    on_pickup: Callable[[dict], "bool | None"] | None = None,
) -> None:
    """Start the agent service: load prompt, resolve model, enter the poll loop.

    on_pickup(issue) runs before the agent loop. Return False to skip that issue.
    Model is read from {AGENT_NAME_UPPER}_MODEL env var, falling back to AGENT_DEFAULTS.
    """
    from agents.base import run_agent
    from tools.models import AGENT_DEFAULTS

    model = os.environ.get(
        f"{agent_name.upper()}_MODEL",
        AGENT_DEFAULTS.get(agent_name, AGENT_DEFAULTS["pm"]),
    )
    system_prompt = Path(prompt_file).read_text()

    def handle(issue: dict) -> None:
        if on_pickup is not None and on_pickup(issue) is False:
            return
        run_agent(issue["number"], agent_name, model, tools, system_prompt, tool_executor)

    poll(agent_name, poll_labels, handle)
