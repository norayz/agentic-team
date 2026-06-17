import os
import base64
from github import Github, GithubException

_g = Github(os.environ["GITHUB_TOKEN"])
_repo_name = os.environ["GITHUB_REPO"]
_gh_repo = _g.get_repo(_repo_name)


def get_agent_branch(agent_name: str, issue_number: int) -> str:
    """Returns branch name like backend/42"""
    return f"{agent_name}/{issue_number}"


def create_agent_branch(agent_name: str, issue_number: int) -> str:
    """Creates git branch {agent_name}/{issue_number} from main. Returns branch name."""
    branch_name = get_agent_branch(agent_name, issue_number)
    main_ref = _gh_repo.get_git_ref("heads/main")
    try:
        _gh_repo.create_git_ref(
            ref=f"refs/heads/{branch_name}",
            sha=main_ref.object.sha,
        )
    except GithubException as e:
        # Branch already exists — that's fine
        if e.status != 422:
            raise
    return branch_name


def commit_files(branch: str, files: dict, message: str) -> None:
    """
    Commits multiple files to a branch using GitHub API.
    files = {"path/to/file.py": "file content as string"}
    Uses push_files GitHub API pattern via PyGithub.
    """
    branch_ref = _gh_repo.get_git_ref(f"heads/{branch}")
    base_tree_sha = _gh_repo.get_git_commit(branch_ref.object.sha).tree.sha

    blobs = []
    for path, content in files.items():
        blob = _gh_repo.create_git_blob(
            content=base64.b64encode(content.encode("utf-8")).decode("utf-8"),
            encoding="base64",
        )
        blobs.append(
            {
                "path": path,
                "mode": "100644",
                "type": "blob",
                "sha": blob.sha,
            }
        )

    new_tree = _gh_repo.create_git_tree(blobs, base_tree=_gh_repo.get_git_tree(base_tree_sha))
    parent_commit = _gh_repo.get_git_commit(branch_ref.object.sha)
    new_commit = _gh_repo.create_git_commit(
        message=message,
        tree=new_tree,
        parents=[parent_commit],
    )
    branch_ref.edit(sha=new_commit.sha)


def open_pr(branch: str, title: str, body: str, issue_number: int) -> int:
    """Opens PR from branch to main. Body references the issue. Returns PR number."""
    full_body = f"Closes #{issue_number}\n\n{body}"
    pr = _gh_repo.create_pull(
        title=title,
        body=full_body,
        head=branch,
        base="main",
    )
    return pr.number


def get_branch_files(branch: str) -> dict:
    """Returns {path: content} for all files in the branch"""
    result = {}
    try:
        contents = _gh_repo.get_contents("", ref=branch)
    except GithubException:
        return result

    stack = list(contents)
    while stack:
        item = stack.pop()
        if item.type == "dir":
            stack.extend(_gh_repo.get_contents(item.path, ref=branch))
        else:
            file_content = _gh_repo.get_contents(item.path, ref=branch)
            result[item.path] = base64.b64decode(file_content.content).decode("utf-8")

    return result
