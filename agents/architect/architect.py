"""Architect Agent — designs technical architecture and creates implementation plan."""
from pathlib import Path
from agents.shared import (
    TOOLS_ISSUE,
    TOOLS_GIT,
    execute_issue_tools,
    execute_git_tools,
    run_agent_service,
)
from tools.github_issues import update_label

AGENT_NAME = "architect"
TOOLS = TOOLS_ISSUE + TOOLS_GIT


def tool_executor(name: str, inputs: dict) -> str:
    return (
        execute_issue_tools(name, inputs, AGENT_NAME)
        or execute_git_tools(name, inputs, AGENT_NAME)
        or f"Unknown tool: {name}"
    )


def on_pickup(issue: dict) -> None:
    update_label(issue["number"], "arch-drafting")


def main():
    run_agent_service(
        AGENT_NAME,
        ["approved-for-architect"],
        TOOLS,
        tool_executor,
        Path(__file__).parent / "architect.md",
        on_pickup=on_pickup,
    )


if __name__ == "__main__":
    main()
