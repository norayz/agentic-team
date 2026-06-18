"""QA Agent — writes and runs tests against the implemented code."""
from pathlib import Path
from agents.shared import (
    TOOLS_ISSUE,
    TOOLS_GIT,
    TOOL_GET_PR_FILES,
    TOOL_RUN_PROJECT,
    execute_issue_tools,
    execute_git_tools,
    run_agent_service,
)

AGENT_NAME = "qa"
TOOLS = TOOLS_ISSUE + TOOLS_GIT + [TOOL_GET_PR_FILES, TOOL_RUN_PROJECT]

_current_issue: int | None = None


def tool_executor(name: str, inputs: dict) -> str:
    from tools.git import get_pr_files
    from tools.sandbox import run_project

    session_id = str(_current_issue) if _current_issue else "default"

    result = execute_issue_tools(name, inputs, AGENT_NAME) or execute_git_tools(name, inputs, AGENT_NAME)
    if result is not None:
        return result
    if name == "get_pr_files":
        return str(get_pr_files(inputs["pr_number"], inputs.get("include_content", False)))
    if name == "run_project":
        return str(run_project(inputs["command"], inputs.get("timeout", 120), session_id=session_id))
    return f"Unknown tool: {name}"


def on_pickup(issue: dict) -> None:
    global _current_issue
    _current_issue = issue["number"]


def main():
    run_agent_service(
        AGENT_NAME,
        ["in-qa"],
        TOOLS,
        tool_executor,
        Path(__file__).parent / "qa.md",
        on_pickup=on_pickup,
    )


if __name__ == "__main__":
    main()
