import os
import base64
from github import Github, GithubException, InputGitTreeElement

_g = Github(os.environ["GITHUB_TOKEN"])
_repo = _g.get_repo(os.environ["GITHUB_REPO"])


def agent_branch(agent_name: str, issue_number: int) -> str:
    return f"{agent_name}/{issue_number}"


def create_branch(name: str) -> str:
    """Create named branch from main. No-ops if branch already exists. Returns name."""
    main_sha = _repo.get_git_ref("heads/main").object.sha
    try:
        _repo.create_git_ref(ref=f"refs/heads/{name}", sha=main_sha)
    except GithubException as e:
        if e.status != 422:
            raise
    return name


def commit_files(branch: str, files: list[dict], message: str) -> None:
    """
    Commit files to branch via GitHub API.
    files = [{"path": "src/foo.py", "content": "..."}]
    """
    ref = _repo.get_git_ref(f"heads/{branch}")
    base_commit = _repo.get_git_commit(ref.object.sha)

    elements = [
        InputGitTreeElement(
            path=f["path"],
            mode="100644",
            type="blob",
            content=f["content"],
        )
        for f in files
    ]

    new_tree = _repo.create_git_tree(elements, base_tree=base_commit.tree)
    new_commit = _repo.create_git_commit(message, new_tree, [base_commit])
    ref.edit(sha=new_commit.sha)


def open_pr(branch: str, title: str, body: str, issue_number: int | None = None) -> int:
    """Open PR from branch to main. Returns PR number."""
    full_body = f"Closes #{issue_number}\n\n{body}" if issue_number else body
    return _repo.create_pull(title=title, body=full_body, head=branch, base="main").number


def branch_exists(name: str) -> bool:
    try:
        _repo.get_branch(name)
        return True
    except GithubException as e:
        if e.status == 404:
            return False
        raise


def get_pr_files(pr_number: int, include_content: bool = False) -> list[dict]:
    pr = _repo.get_pull(pr_number)
    result = []
    for f in pr.get_files():
        entry = {
            "filename": f.filename,
            "status": f.status,
            "additions": f.additions,
            "deletions": f.deletions,
            "patch": f.patch,
        }
        if include_content and f.status != "removed":
            try:
                cf = _repo.get_contents(f.filename, ref=pr.head.sha)
                entry["content"] = cf.decoded_content.decode()
            except Exception as e:
                entry["content_error"] = str(e)
        result.append(entry)
    return result


def post_pr_review(pr_number: int, body: str, event: str) -> None:
    """event: APPROVE | REQUEST_CHANGES | COMMENT"""
    _repo.get_pull(pr_number).create_review(body=body, event=event)


def merge_pr(pr_number: int, merge_method: str = "squash") -> None:
    _repo.get_pull(pr_number).merge(merge_method=merge_method)


def get_branch_files(branch: str) -> dict[str, str]:
    """Returns {path: content} for all files in branch."""
    result = {}
    try:
        stack = list(_repo.get_contents("", ref=branch))
    except GithubException:
        return result
    while stack:
        item = stack.pop()
        if item.type == "dir":
            stack.extend(_repo.get_contents(item.path, ref=branch))
        else:
            cf = _repo.get_contents(item.path, ref=branch)
            result[item.path] = base64.b64decode(cf.content).decode()
    return result
