"""Code Reviewer Agent — reviews pull requests for correctness, style, and security."""
import os
import time
import logging
from pathlib import Path
from agents.base import run_agent
from tools.github_issues import get_issues_by_label, update_label
from tools.models import AGENT_DEFAULTS

logger = logging.getLogger(__name__)
AGENT_NAME = "code_reviewer"
MODEL = os.environ.get("CR_MODEL", AGENT_DEFAULTS["code_reviewer"])
SYSTEM_PROMPT = Path("/app/prompts/code_reviewer.md").read_text()

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
        "name": "get_pr_files",
        "description": "Get the list of files changed in a pull request, including their content",
        "input_schema": {
            "type": "object",
            "properties": {
                "pr_number": {"type": "integer"},
                "include_content": {"type": "boolean", "description": "If true, fetch file content from the PR branch"}
            },
            "required": ["pr_number"]
        }
    },
    {
        "name": "post_pr_review",
        "description": "Post a review comment on a pull request",
        "input_schema": {
            "type": "object",
            "properties": {
                "pr_number": {"type": "integer"},
                "body": {"type": "string"},
                "event": {"type": "string", "enum": ["APPROVE", "REQUEST_CHANGES", "COMMENT"], "description": "Review verdict"}
            },
            "required": ["pr_number", "body", "event"]
        }
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
    elif name == "get_pr_files":
        g = Github(os.environ["GITHUB_TOKEN"])
        repo = g.get_repo(os.environ["GITHUB_REPO"])
        pr = repo.get_pull(inputs["pr_number"])
        files = list(pr.get_files())
        result = []
        for f in files:
            entry = {
                "filename": f.filename,
                "status": f.status,
                "additions": f.additions,
                "deletions": f.deletions,
                "patch": f.patch,
            }
            if inputs.get("include_content") and f.status != "removed":
                try:
                    content_file = repo.get_contents(f.filename, ref=pr.head.sha)
                    entry["content"] = content_file.decoded_content.decode("utf-8")
                except Exception as e:
                    entry["content_error"] = str(e)
            result.append(entry)
        return str(result)
    elif name == "post_pr_review":
        g = Github(os.environ["GITHUB_TOKEN"])
        repo = g.get_repo(os.environ["GITHUB_REPO"])
        pr = repo.get_pull(inputs["pr_number"])
        pr.create_review(body=inputs["body"], event=inputs["event"])
        return f"Review posted ({inputs['event']})"
    return f"Unknown tool: {name}"


def main():
    logging.basicConfig(level=logging.INFO)
    logger.info("Code Reviewer agent started, polling for work...")
    while True:
        try:
            issues = get_issues_by_label("cr-review")
            for issue in issues:
                logger.info(f"Code Reviewer picking up issue #{issue['number']}")
                run_agent(issue["number"], AGENT_NAME, MODEL, TOOLS, SYSTEM_PROMPT, tool_executor)
        except Exception as e:
            logger.error(f"Code Reviewer agent error: {e}")
        time.sleep(10)


if __name__ == "__main__":
    main()
