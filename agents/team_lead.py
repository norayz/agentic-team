"""Team Lead Agent — reviews PM specs, arch designs, and final PRs before handoff."""
import os
import time
import logging
from pathlib import Path
from agents.base import run_agent
from tools.github_issues import get_issues_by_label, update_label
from tools.models import AGENT_DEFAULTS

logger = logging.getLogger(__name__)
AGENT_NAME = "team_lead"
MODEL = os.environ.get("TL_MODEL", AGENT_DEFAULTS["team_lead"])
SYSTEM_PROMPT = Path("/app/prompts/team_lead.md").read_text()

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
        "description": "Update the issue body",
        "input_schema": {"type": "object", "properties": {"issue_number": {"type": "integer"}, "body": {"type": "string"}}, "required": ["issue_number", "body"]}
    },
    {
        "name": "create_sub_issue",
        "description": "Create a sub-task issue linked to the parent",
        "input_schema": {
            "type": "object",
            "properties": {
                "parent_issue_number": {"type": "integer"},
                "title": {"type": "string"},
                "body": {"type": "string"},
                "label": {"type": "string"}
            },
            "required": ["parent_issue_number", "title", "body"]
        }
    },
    {
        "name": "merge_pr",
        "description": "Merge a pull request by PR number",
        "input_schema": {
            "type": "object",
            "properties": {
                "pr_number": {"type": "integer"},
                "merge_method": {"type": "string", "enum": ["merge", "squash", "rebase"], "description": "Merge strategy, defaults to squash"}
            },
            "required": ["pr_number"]
        }
    },
]


def tool_executor(name: str, inputs: dict) -> str:
    from tools.github_issues import get_issue, get_comments, post_comment, update_label, create_sub_issue
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
    elif name == "create_sub_issue":
        result = create_sub_issue(
            inputs["parent_issue_number"],
            inputs["title"],
            inputs["body"],
            inputs.get("label"),
        )
        return str(result)
    elif name == "merge_pr":
        g = Github(os.environ["GITHUB_TOKEN"])
        repo = g.get_repo(os.environ["GITHUB_REPO"])
        pr = repo.get_pull(inputs["pr_number"])
        method = inputs.get("merge_method", "squash")
        pr.merge(merge_method=method)
        return f"PR #{inputs['pr_number']} merged via {method}"
    return f"Unknown tool: {name}"


def main():
    logging.basicConfig(level=logging.INFO)
    logger.info("Team Lead agent started, polling for work...")
    while True:
        try:
            for label in ["tl-pm-review", "tl-arch-review", "tl-final-review"]:
                issues = get_issues_by_label(label)
                for issue in issues:
                    logger.info(f"Team Lead picking up issue #{issue['number']} ({label})")
                    run_agent(issue["number"], AGENT_NAME, MODEL, TOOLS, SYSTEM_PROMPT, tool_executor)
        except Exception as e:
            logger.error(f"Team Lead agent error: {e}")
        time.sleep(10)


if __name__ == "__main__":
    main()
