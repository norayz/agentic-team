import os
from github import Github
from datetime import datetime

_g = Github(os.environ["GITHUB_TOKEN"])
_repo = _g.get_repo(os.environ["GITHUB_REPO"])

REQUIRED_LABELS = [
    {"name": "new", "color": "0075ca", "description": "New issue, not yet assigned"},
    {"name": "pm-drafting", "color": "d4c5f9", "description": "PM is drafting the spec"},
    {"name": "tl-pm-review", "color": "fef2c0", "description": "Team Lead reviewing PM draft"},
    {"name": "waiting-for-human", "color": "e4e669", "description": "Blocked on human input"},
    {"name": "approved-for-architect", "color": "0e8a16", "description": "Approved to proceed to architecture"},
    {"name": "arch-drafting", "color": "c5def5", "description": "Architect is drafting the design"},
    {"name": "tl-arch-review", "color": "fef2c0", "description": "Team Lead reviewing architecture"},
    {"name": "in-dev", "color": "e99695", "description": "Under active development"},
    {"name": "cr-review", "color": "f9d0c4", "description": "Code review in progress"},
    {"name": "in-qa", "color": "0075ca", "description": "In QA testing"},
    {"name": "in-devops", "color": "0075ca", "description": "DevOps deploying"},
    {"name": "tl-final-review", "color": "fef2c0", "description": "Team Lead final review"},
    {"name": "done", "color": "0e8a16", "description": "Completed"},
]


def get_issue(issue_number: int) -> dict:
    """Returns {number, title, body, labels: [str], state}"""
    issue = _repo.get_issue(issue_number)
    return {
        "number": issue.number,
        "title": issue.title,
        "body": issue.body,
        "labels": [label.name for label in issue.labels],
        "state": issue.state,
    }


def get_comments(issue_number: int) -> list[dict]:
    """Returns list of {author, body, created_at} sorted by created_at"""
    issue = _repo.get_issue(issue_number)
    comments = [
        {
            "author": comment.user.login,
            "body": comment.body,
            "created_at": comment.created_at.isoformat(),
        }
        for comment in issue.get_comments()
    ]
    return sorted(comments, key=lambda c: c["created_at"])


def post_comment(issue_number: int, agent_name: str, message: str) -> None:
    """Posts comment formatted as: [AGENT_NAME] message"""
    issue = _repo.get_issue(issue_number)
    formatted = f"[{agent_name.upper()}] {message}"
    issue.create_comment(formatted)


def update_label(issue_number: int, new_label: str) -> None:
    """Replaces all current labels with new_label"""
    issue = _repo.get_issue(issue_number)
    issue.set_labels(new_label)


def add_label(issue_number: int, label: str) -> None:
    """Adds label without removing existing ones"""
    issue = _repo.get_issue(issue_number)
    issue.add_to_labels(label)


def create_sub_issue(parent_number: int, title: str, body: str, label: str) -> int:
    """Creates a new issue, references parent in body, returns issue number"""
    full_body = f"Parent issue: #{parent_number}\n\n{body}"
    new_issue = _repo.create_issue(
        title=title,
        body=full_body,
        labels=[label],
    )
    return new_issue.number


def setup_labels(labels_config: list[dict]) -> None:
    """Creates labels if they don't exist. labels_config = [{name, color, description}]"""
    existing = {label.name for label in _repo.get_labels()}
    for cfg in labels_config:
        if cfg["name"] not in existing:
            _repo.create_label(
                name=cfg["name"],
                color=cfg["color"],
                description=cfg.get("description", ""),
            )


def get_issues_by_label(label: str) -> list[dict]:
    """Returns all open issues with given label"""
    issues = _repo.get_issues(state="open", labels=[label])
    return [
        {
            "number": issue.number,
            "title": issue.title,
            "body": issue.body,
            "labels": [lbl.name for lbl in issue.labels],
            "state": issue.state,
        }
        for issue in issues
    ]
