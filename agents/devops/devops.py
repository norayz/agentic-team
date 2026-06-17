"""DevOps Agent — sets up CI/CD, Docker, and infra config in parallel with backend."""
import logging
from pathlib import Path
from agents.shared import (
    TOOLS_ISSUE,
    TOOLS_GIT,
    TOOL_GET_PR_FILES,
    TOOL_BRANCH_EXISTS,
    TOOL_RUN_COMMAND,
    execute_issue_tools,
    execute_git_tools,
    run_agent_service,
)
from tools.git import agent_branch, branch_exists

_log = logging.getLogger(__name__)

AGENT_NAME = "devops"
TOOLS = TOOLS_ISSUE + TOOLS_GIT + [TOOL_GET_PR_FILES, TOOL_BRANCH_EXISTS, TOOL_RUN_COMMAND]


def tool_executor(name: str, inputs: dict) -> str:
    from tools.git import get_pr_files
    from tools.sandbox import run_command

    result = execute_issue_tools(name, inputs, AGENT_NAME) or execute_git_tools(name, inputs, AGENT_NAME)
    if result is not None:
        return result
    if name == "branch_exists":
        exists = branch_exists(inputs["branch_name"])
        return f"Branch '{inputs['branch_name']}' {'exists' if exists else 'does not exist'}"
    if name == "get_pr_files":
        return str(get_pr_files(inputs["pr_number"], inputs.get("include_content", False)))
    if name == "run_command":
        return str(run_command(inputs["command"], inputs.get("timeout", 120)))
    return f"Unknown tool: {name}"


def on_pickup(issue: dict) -> bool | None:
    backend = agent_branch("backend", issue["number"])
    if not branch_exists(backend):
        _log.debug(f"Skipping issue #{issue['number']} — {backend} not yet created")
        return False


def main():
    run_agent_service(
        AGENT_NAME,
        ["in-dev"],
        TOOLS,
        tool_executor,
        Path(__file__).parent / "devops.md",
        on_pickup=on_pickup,
    )


if __name__ == "__main__":
    main()
