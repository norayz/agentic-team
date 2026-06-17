"""PM Agent — turns a raw prompt into a full software specification."""
import os
import time
import logging
from pathlib import Path
from agents.base import run_agent
from tools.github_issues import get_issues_by_label, update_label
from tools.models import AGENT_DEFAULTS

logger = logging.getLogger(__name__)
AGENT_NAME = "pm"
MODEL = os.environ.get("PM_MODEL", AGENT_DEFAULTS["pm"])
SYSTEM_PROMPT = Path("/app/prompts/pm.md").read_text()

# Tool definitions (Claude tool schema)
TOOLS = [
    {
        "name": "get_issue",
        "description": "Get issue details including title, body, labels",
        "input_schema": {"type": "object", "properties": {"issue_number": {"type": "integer"}}, "required": ["issue_number"]}
    },
    {
        "name": "get_comments",
        "description": "Get all comments on an issue",
        "input_schema": {"type": "object", "properties": {"issue_number": {"type": "integer"}}, "required": ["issue_number"]}
    },
    {
        "name": "post_comment",
        "description": "Post a comment as this agent",
        "input_schema": {"type": "object", "properties": {"issue_number": {"type": "integer"}, "message": {"type": "string"}}, "required": ["issue_number", "message"]}
    },
    {
        "name": "update_label",
        "description": "Update the status label on an issue",
        "input_schema": {"type": "object", "properties": {"issue_number": {"type": "integer"}, "new_label": {"type": "string"}}, "required": ["issue_number", "new_label"]}
    },
    {
        "name": "update_issue_body",
        "description": "Update the issue body (write the full spec here)",
        "input_schema": {"type": "object", "properties": {"issue_number": {"type": "integer"}, "body": {"type": "string"}}, "required": ["issue_number", "body"]}
    },
]


def tool_executor(name: str, inputs: dict) -> str:
    from tools.github_issues import get_issue, get_comments, post_comment, update_label
    from github import Github

    if name == "get_issue":
        return str(get_issue(inputs["issue_number"]))
    elif name == "get_comments":
        return str(get_comments(inputs["issue_number"]))
    elif name == "post_comment":
        post_comment(inputs["issue_number"], AGENT_NAME, inputs["message"])
        return "Comment posted"
    elif name == "update_label":
        update_label(inputs["issue_number"], inputs["new_label"])
        return f"Label updated to {inputs['new_label']}"
    elif name == "update_issue_body":
        g = Github(os.environ["GITHUB_TOKEN"])
        repo = g.get_repo(os.environ["GITHUB_REPO"])
        issue = repo.get_issue(inputs["issue_number"])
        issue.edit(body=inputs["body"])
        return "Issue body updated"
    return f"Unknown tool: {name}"


def main():
    logging.basicConfig(level=logging.INFO)
    logger.info("PM agent started, polling for work...")
    while True:
        try:
            for label in ["new", "pm-drafting"]:
                issues = get_issues_by_label(label)
                for issue in issues:
                    logger.info(f"PM picking up issue #{issue['number']}")
                    update_label(issue["number"], "pm-drafting")
                    run_agent(issue["number"], AGENT_NAME, MODEL, TOOLS, SYSTEM_PROMPT, tool_executor)
        except Exception as e:
            logger.error(f"PM agent error: {e}")
        time.sleep(10)


if __name__ == "__main__":
    main()
