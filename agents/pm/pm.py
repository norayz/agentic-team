"""PM Agent — turns a raw prompt into a full software specification."""
import os
from pathlib import Path
from agents.base import run_agent
from agents.shared import TOOLS_ISSUE, execute_issue_tools, poll
from tools.github_issues import update_label
from tools.models import AGENT_DEFAULTS

AGENT_NAME = "pm"
MODEL = os.environ.get("PM_MODEL", AGENT_DEFAULTS["pm"])
SYSTEM_PROMPT = Path(__file__).parent.joinpath("pm.md").read_text()

TOOLS = TOOLS_ISSUE


def tool_executor(name: str, inputs: dict) -> str:
    return execute_issue_tools(name, inputs, AGENT_NAME) or f"Unknown tool: {name}"


def handle(issue: dict) -> None:
    update_label(issue["number"], "pm-drafting")
    run_agent(issue["number"], AGENT_NAME, MODEL, TOOLS, SYSTEM_PROMPT, tool_executor)


def main():
    poll(AGENT_NAME, ["new", "pm-drafting"], handle)


if __name__ == "__main__":
    main()
