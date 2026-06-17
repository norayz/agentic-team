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


def tool_executor(name: str, inputs: dict) -> str:
    from tools.git import get_pr_files
    from tools.sandbox import run_project

    result = execute_issue_tools(name, inputs, AGENT_NAME) or execute_git_tools(name, inputs, AGENT_NAME)
    if result is not None:
        return result
    if name == "get_pr_files":
        return str(get_pr_files(inputs["pr_number"], inputs.get("include_content", False)))
    if name == "run_project":
        return str(run_project(inputs["command"], inputs.get("timeout", 120)))
    return f"Unknown tool: {name}"


def main():
    run_agent_service(
        AGENT_NAME,
        ["in-qa"],
        TOOLS,
        tool_executor,
        Path(__file__).parent / "qa.md",
    )


if __name__ == "__main__":
    main()
