import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Tuple

import requests


GITHUB_API = "https://api.github.com"


def read_event_payload() -> Dict:
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if not event_path or not os.path.isfile(event_path):
        print("GITHUB_EVENT_PATH is not set or file does not exist", file=sys.stderr)
        sys.exit(1)
    with open(event_path, "r") as f:
        return json.load(f)


def get_repo_owner_and_name() -> Tuple[str, str]:
    repo = os.environ.get("GITHUB_REPOSITORY")
    if not repo or "/" not in repo:
        print("GITHUB_REPOSITORY is not set", file=sys.stderr)
        sys.exit(1)
    owner, name = repo.split("/", 1)
    return owner, name


def get_token() -> str:
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GITHUB_BEARER_TOKEN")
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
    resp = requests.get(url, headers=headers, timeout=30)
    return resp


def gh_post(url: str, token: str, body: Dict) -> requests.Response:
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "Content-Type": "application/json",
    }
    resp = requests.post(url, headers=headers, data=json.dumps(body), timeout=30)
    return resp


def list_pr_reviews(owner: str, repo: str, pr_number: int, token: str) -> List[Dict]:
    url = f"{GITHUB_API}/repos/{owner}/{repo}/pulls/{pr_number}/reviews"
    resp = gh_get(url, token)
    if resp.status_code != 200:
        print(f"Error fetching reviews: {resp.status_code} {resp.text}", file=sys.stderr)
        sys.exit(1)
    return resp.json()


def get_pr(owner: str, repo: str, pr_number: int, token: str) -> Dict:
    url = f"{GITHUB_API}/repos/{owner}/{repo}/pulls/{pr_number}"
    resp = gh_get(url, token)
    if resp.status_code != 200:
        print(f"Error fetching PR: {resp.status_code} {resp.text}", file=sys.stderr)
        sys.exit(1)
    return resp.json()


def get_issue(owner: str, repo: str, issue_number: int, token: str) -> Dict:
    url = f"{GITHUB_API}/repos/{owner}/{repo}/issues/{issue_number}"
    resp = gh_get(url, token)
    if resp.status_code != 200:
        print(f"Error fetching Issue: {resp.status_code} {resp.text}", file=sys.stderr)
        sys.exit(1)
    return resp.json()


def resolve_pr_number(event: Dict) -> int:
    if "pull_request" in event and isinstance(event["pull_request"], dict):
        return int(event["pull_request"]["number"])
    if event.get("issue") and event["issue"].get("pull_request"):
        return int(event["issue"]["number"])
    print("This event is not associated with a pull request", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    token = get_token()
    owner, repo = get_repo_owner_and_name()
    event = read_event_payload()
    pr_number = resolve_pr_number(event)

    pr = get_pr(owner, repo, pr_number, token)
    head_sha = pr.get("head", {}).get("sha")

    reviews = list_pr_reviews(owner, repo, pr_number, token)
    # Build latest review per user on the head commit
    latest_review_by_user: Dict[str, Dict] = {}
    for r in reviews:
        user_login = (r.get("user") or {}).get("login", "").lower()
        commit_id = r.get("commit_id")
        submitted_at = r.get("submitted_at") or ""
        if commit_id != head_sha or not user_login:
            continue
        previous = latest_review_by_user.get(user_login)
        if not previous:
            latest_review_by_user[user_login] = r
            continue
        prev_time = (previous.get("submitted_at") or "").replace("Z", "+00:00")
        curr_time = submitted_at.replace("Z", "+00:00")
        try:
            if datetime.fromisoformat(curr_time) > datetime.fromisoformat(prev_time):
                latest_review_by_user[user_login] = r
        except ValueError:
            # Fallback: if parsing fails, keep existing
            pass

    requested_reviewers = [u.get("login", "").lower() for u in pr.get("requested_reviewers", []) if u.get("login")]

    if requested_reviewers:
        # Require each requested reviewer to have APPROVED on the latest commit
        missing_or_unapproved: List[str] = []
        for login in requested_reviewers:
            latest = latest_review_by_user.get(login)
            if not latest or latest.get("state") != "APPROVED":
                missing_or_unapproved.append(login)
        if missing_or_unapproved:
            print(
                "Missing required approvals from: " + ", ".join("@" + u for u in missing_or_unapproved),
                file=sys.stderr,
            )
            sys.exit(1)
        print("All requested reviewers have approved on the latest commit.")
        return

    # If there are no requested reviewers, they have submitted reviews.
    # Require that all latest reviews on head commit are APPROVED.
    non_approved = [u for u, r in latest_review_by_user.items() if r.get("state") != "APPROVED"]
    if non_approved:
        print(
            "Reviewers present but not APPROVED: " + ", ".join("@" + u for u in non_approved),
            file=sys.stderr,
        )
        sys.exit(1)
    if not latest_review_by_user:
        print("No reviews found on the latest commit.", file=sys.stderr)
        sys.exit(1)
    print("All reviewers are in APPROVED state on the latest commit.")


if __name__ == "__main__":
    main()
