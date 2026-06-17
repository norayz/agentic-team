"""Team Lead Agent — reviews PM specs, arch designs, and final PRs before handoff."""
import os
from pathlib import Path
from agents.base import run_agent
from agents.shared import TOOLS_ISSUE, execute_issue_tools, poll
from tools.models import AGENT_DEFAULTS

AGENT_NAME = "team_lead"
MODEL = os.environ.get("TL_MODEL", AGENT_DEFAULTS["team_lead"])
SYSTEM_PROMPT = Path(__file__).parent.joinpath("team_lead.md").read_text()

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

TOOL_CREATE_SUB_ISSUE = {
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

TOOL_MERGE_PR = {
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

TOOLS = TOOLS_ISSUE + [TOOL_GET_PR_FILES, TOOL_CREATE_SUB_ISSUE, TOOL_MERGE_PR]


def tool_executor(name: str, inputs: dict) -> str:
    from tools.github_issues import create_sub_issue
    from tools.git import merge_pr

    result = execute_issue_tools(name, inputs, AGENT_NAME)
    if result is not None:
        return result
    if name == "get_pr_files":
        from tools.git import get_pr_files
        return str(get_pr_files(inputs["pr_number"], inputs.get("include_content", False)))
    if name == "create_sub_issue":
        n = create_sub_issue(
            inputs["parent_issue_number"], inputs["title"], inputs["body"], inputs.get("label")
        )
        return f"Sub-issue #{n} created"
    if name == "merge_pr":
        merge_pr(inputs["pr_number"], inputs.get("merge_method", "squash"))
        return f"PR #{inputs['pr_number']} merged"
    return f"Unknown tool: {name}"


def handle(issue: dict) -> None:
    run_agent(issue["number"], AGENT_NAME, MODEL, TOOLS, SYSTEM_PROMPT, tool_executor)


def main():
    poll(AGENT_NAME, ["tl-pm-review", "tl-arch-review", "tl-final-review"], handle)


if __name__ == "__main__":
    main()
