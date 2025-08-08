import json
import os
import sys
from typing import Dict, List, Tuple

import requests


GITHUB_API = "https://api.github.com"


def get_repo_owner_and_name() -> Tuple[str, str]:
    repo = os.environ.get("GITHUB_REPOSITORY")
    if not repo or "/" not in repo:
        print("GITHUB_REPOSITORY is not set", file=sys.stderr)
        sys.exit(1)
    owner, name = repo.split("/", 1)
    return owner, name


def get_token() -> str:
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        print("GITHUB_TOKEN is not available", file=sys.stderr)
        sys.exit(1)
    return token


def gh_get(url: str, token: str) -> requests.Response:
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    return requests.get(url, headers=headers, timeout=30)


def gh_post(url: str, token: str, body: Dict) -> requests.Response:
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "Content-Type": "application/json",
    }
    return requests.post(url, headers=headers, data=json.dumps(body), timeout=30)


def is_collaborator(owner: str, repo: str, username: str, token: str) -> bool:
    url = f"{GITHUB_API}/repos/{owner}/{repo}/collaborators/{username}"
    resp = gh_get(url, token)
    if resp.status_code == 204:
        return True
    if resp.status_code == 404:
        return False
    print(f"Warn: collaborator check for {username} -> {resp.status_code} {resp.text}")
    return False


def list_issue_comments(owner: str, repo: str, issue_number: int, token: str) -> List[Dict]:
    url = f"{GITHUB_API}/repos/{owner}/{repo}/issues/{issue_number}/comments"
    resp = gh_get(url, token)
    if resp.status_code != 200:
        print(f"Error fetching comments: {resp.status_code} {resp.text}", file=sys.stderr)
        sys.exit(1)
    return resp.json()


def comment_once(owner: str, repo: str, issue_number: int, token: str, body_text: str, dedupe_hint: str) -> None:
    comments = list_issue_comments(owner, repo, issue_number, token)
    if any(dedupe_hint in (c.get("body") or "") for c in comments):
        return
    url = f"{GITHUB_API}/repos/{owner}/{repo}/issues/{issue_number}/comments"
    resp = gh_post(url, token, {"body": body_text})
    if resp.status_code not in (200, 201):
        print(f"Warn: failed to post comment: {resp.status_code} {resp.text}")


def request_reviewers(owner: str, repo: str, pr_number: int, reviewers: List[str], token: str) -> None:
    if not reviewers:
        return
    url = f"{GITHUB_API}/repos/{owner}/{repo}/pulls/{pr_number}/requested_reviewers"
    resp = gh_post(url, token, {"reviewers": reviewers})
    if resp.status_code not in (200, 201):
        print(f"Warn: failed to request reviewers: {resp.status_code} {resp.text}")


def main() -> None:
    token = get_token()
    owner, repo = get_repo_owner_and_name()

    pr_number_raw = os.environ.get("PR_NUMBER")
    winner = os.environ.get("WINNER")
    loser = os.environ.get("LOSER")

    if not pr_number_raw:
        print("PR_NUMBER is required", file=sys.stderr)
        sys.exit(1)

    pr_number = int(pr_number_raw)
    players = [p for p in [winner, loser] if p]

    collaborators: List[str] = []
    non_collaborators: List[str] = []
    for login in players:
        if is_collaborator(owner, repo, login, token):
            collaborators.append(login)
        else:
            non_collaborators.append(login)

    # Request reviews from collaborators only
    request_reviewers(owner, repo, pr_number, collaborators, token)

    # Comment guidance for non-collaborators
    if non_collaborators:
        guidance_hint = "cannot be requested as reviewers"
        guidance = (
            f"Heads up: {', '.join('@' + u for u in non_collaborators)} {guidance_hint} because they are not collaborators. "
            "Please add them as collaborators if you want them to provide Approve reviews on future PRs."
        )
        comment_once(owner, repo, pr_number, token, guidance, dedupe_hint=guidance_hint)


if __name__ == "__main__":
    main()
