import os
from github import Github

_g = Github(os.environ["GITHUB_TOKEN"])
_repo = _g.get_repo(os.environ["GITHUB_REPO"])

REQUIRED_LABELS = [
    {"name": "new",                    "color": "0075ca", "description": "New issue, not yet assigned"},
    {"name": "pm-drafting",            "color": "d4c5f9", "description": "PM is drafting the spec"},
    {"name": "tl-pm-review",           "color": "fef2c0", "description": "Team Lead reviewing PM draft"},
    {"name": "waiting-for-human",      "color": "e4e669", "description": "Blocked on human input"},
    {"name": "approved-for-architect", "color": "0e8a16", "description": "Approved to proceed to architecture"},
    {"name": "arch-drafting",          "color": "c5def5", "description": "Architect is drafting the design"},
    {"name": "tl-arch-review",         "color": "fef2c0", "description": "Team Lead reviewing architecture"},
    {"name": "in-dev",                 "color": "e99695", "description": "Under active development"},
    {"name": "cr-review",              "color": "f9d0c4", "description": "Code review in progress"},
    {"name": "in-qa",                  "color": "0075ca", "description": "In QA testing"},
    {"name": "blocked",                "color": "d73a4a", "description": "Blocked, needs human intervention"},
    {"name": "tl-final-review",        "color": "fef2c0", "description": "Team Lead final review"},
    {"name": "done",                   "color": "0e8a16", "description": "Completed"},
]


def get_issue(issue_number: int) -> dict:
    issue = _repo.get_issue(issue_number)
    return {
        "number": issue.number,
        "title": issue.title,
        "body": issue.body,
        "labels": [lbl.name for lbl in issue.labels],
        "state": issue.state,
    }


def get_comments(issue_number: int) -> list[dict]:
    issue = _repo.get_issue(issue_number)
    return sorted(
        [{"author": c.user.login, "body": c.body, "created_at": c.created_at.isoformat()}
         for c in issue.get_comments()],
        key=lambda c: c["created_at"],
    )


def post_comment(issue_number: int, agent_name: str, message: str) -> None:
    _repo.get_issue(issue_number).create_comment(message)


def update_label(issue_number: int, new_label: str) -> None:
    _repo.get_issue(issue_number).set_labels(new_label)


def add_label(issue_number: int, label: str) -> None:
    _repo.get_issue(issue_number).add_to_labels(label)


def update_issue_body(issue_number: int, body: str) -> None:
    _repo.get_issue(issue_number).edit(body=body)


def create_sub_issue(parent_number: int, title: str, body: str, label: str | None = None) -> int:
    kwargs: dict = {"title": title, "body": f"Parent issue: #{parent_number}\n\n{body}"}
    if label:
        kwargs["labels"] = [label]
    return _repo.create_issue(**kwargs).number


def get_issues_by_label(label: str) -> list[dict]:
    return [
        {
            "number": issue.number,
            "title": issue.title,
            "body": issue.body,
            "labels": [lbl.name for lbl in issue.labels],
            "state": issue.state,
        }
        for issue in _repo.get_issues(state="open", labels=[label])
    ]


def setup_labels() -> None:
    existing = {lbl.name for lbl in _repo.get_labels()}
    for cfg in REQUIRED_LABELS:
        if cfg["name"] not in existing:
            _repo.create_label(name=cfg["name"], color=cfg["color"], description=cfg.get("description", ""))
