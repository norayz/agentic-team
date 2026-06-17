"""PM Agent — turns a raw user request into a reviewed, approved spec."""
from pathlib import Path
from agents.shared import TOOLS_ISSUE, execute_issue_tools, run_agent_service
from tools.github_issues import update_label

AGENT_NAME = "pm"
TOOLS = TOOLS_ISSUE


def tool_executor(name: str, inputs: dict) -> str:
    return execute_issue_tools(name, inputs, AGENT_NAME) or f"Unknown tool: {name}"


def on_pickup(issue: dict) -> None:
    update_label(issue["number"], "pm-drafting")


def main():
    run_agent_service(
        AGENT_NAME,
        ["new", "pm-revision"],
        TOOLS,
        tool_executor,
        Path(__file__).parent / "pm.md",
        on_pickup=on_pickup,
    )


if __name__ == "__main__":
    main()
