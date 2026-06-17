"""Architect Agent — designs technical architecture and creates implementation plan."""
import os
from pathlib import Path
from agents.base import run_agent
from agents.shared import TOOLS_ISSUE, TOOLS_GIT, execute_issue_tools, execute_git_tools, poll
from tools.github_issues import update_label
from tools.models import AGENT_DEFAULTS

AGENT_NAME = "architect"
MODEL = os.environ.get("ARCH_MODEL", AGENT_DEFAULTS["architect"])
SYSTEM_PROMPT = Path(__file__).parent.joinpath("architect.md").read_text()

TOOLS = TOOLS_ISSUE + TOOLS_GIT


def tool_executor(name: str, inputs: dict) -> str:
    return (
        execute_issue_tools(name, inputs, AGENT_NAME)
        or execute_git_tools(name, inputs, AGENT_NAME)
        or f"Unknown tool: {name}"
    )


def handle(issue: dict) -> None:
    update_label(issue["number"], "arch-drafting")
    run_agent(issue["number"], AGENT_NAME, MODEL, TOOLS, SYSTEM_PROMPT, tool_executor)


def main():
    poll(AGENT_NAME, ["approved-for-architect"], handle)


if __name__ == "__main__":
    main()
