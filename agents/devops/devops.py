"""DevOps Agent — sets up CI/CD, Docker, and infra config in parallel with backend."""
import logging
import os
from pathlib import Path
from agents.base import run_agent
from agents.shared import TOOLS_ISSUE, TOOLS_GIT, execute_issue_tools, execute_git_tools, poll
from tools.git import agent_branch, branch_exists
from tools.models import AGENT_DEFAULTS

_log = logging.getLogger(__name__)

AGENT_NAME = "devops"
MODEL = os.environ.get("DEVOPS_MODEL", AGENT_DEFAULTS["devops"])
SYSTEM_PROMPT = Path(__file__).parent.joinpath("devops.md").read_text()

TOOL_GET_PR_FILES = {
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

TOOL_BRANCH_EXISTS = {
    "name": "branch_exists",
    "description": "Check whether a git branch exists",
    "input_schema": {
        "type": "object",
        "properties": {"branch_name": {"type": "string"}},
        "required": ["branch_name"],
    },
}

TOOL_RUN_COMMAND = {
    "name": "run_command",
    "description": "Run a shell command in the sandbox (to verify docker builds or infra scripts)",
    "input_schema": {
        "type": "object",
        "properties": {
            "command": {"type": "string"},
            "timeout": {"type": "integer", "description": "Seconds, default 120"},
        },
        "required": ["command"],
    },
}

TOOLS = TOOLS_ISSUE + TOOLS_GIT + [TOOL_GET_PR_FILES, TOOL_BRANCH_EXISTS, TOOL_RUN_COMMAND]


def tool_executor(name: str, inputs: dict) -> str:
    from tools.sandbox import run_command

    result = execute_issue_tools(name, inputs, AGENT_NAME) or execute_git_tools(name, inputs, AGENT_NAME)
    if result is not None:
        return result
    if name == "branch_exists":
        exists = branch_exists(inputs["branch_name"])
        return f"Branch '{inputs['branch_name']}' {'exists' if exists else 'does not exist'}"
    if name == "get_pr_files":
        from tools.git import get_pr_files
        return str(get_pr_files(inputs["pr_number"], inputs.get("include_content", False)))
    if name == "run_command":
        return str(run_command(inputs["command"], inputs.get("timeout", 120)))
    return f"Unknown tool: {name}"


def handle(issue: dict) -> None:
    backend = agent_branch("backend", issue["number"])
    if not branch_exists(backend):
        _log.debug(f"Skipping issue #{issue['number']} — {backend} not yet created")
        return
    run_agent(issue["number"], AGENT_NAME, MODEL, TOOLS, SYSTEM_PROMPT, tool_executor)


def main():
    poll(AGENT_NAME, ["in-dev"], handle)


if __name__ == "__main__":
    main()
