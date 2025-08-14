import os
import re
import yaml
import pandas as pd
from datetime import datetime, timezone
import tempfile
from typing import Optional

from github_utils import get_repo_owner_and_name_or_default, list_issue_comments

# Pre-compiled regex for efficiency
# Matches " #123" in the bot's comment
PR_NUM_RE = re.compile(r"#(\d+)")
# Extracts the issue number from a filename like "2024-01-01-123.yml"
ISSUE_NUM_RE = re.compile(r"-(\d+)\.yml$")


def find_pr_number_from_comments(owner: str, repo: str, issue_number: int) -> int:
    """
    Find the PR number from the comments of an issue.
    The bot posts a comment with a link to the PR.
    """
    comments = list_issue_comments(owner, repo, issue_number)
    for comment in comments:
        # The bot's username is "github-actions[bot]"
        if comment["user"]["login"] == "github-actions[bot]":
            match = PR_NUM_RE.search(comment["body"])
            if match:
                return int(match.group(1))
    return 0


def build_history_page(output_dir: Optional[str] = None):
    """
    Generates a static HTML page with the match history.

    If `output_dir` is provided, `history.html` is created there. Otherwise,
    a temporary directory is created.
    """
    owner, repo = get_repo_owner_and_name_or_default()

    # Gracefully handle missing matches directory
    if not os.path.exists("matches"):
        match_files = []
    else:
        match_files = sorted(
            [f for f in os.listdir("matches") if f.endswith(".yml")], reverse=True
        )

    matches = []
    for match_file in match_files:
        match_path = os.path.join("matches", match_file)
        with open(match_path, 'r') as f:
            match_data = yaml.safe_load(f)

        issue_search = ISSUE_NUM_RE.search(match_file)
        if not issue_search:
            continue

        issue_number = int(issue_search.group(1))
        pr_number = find_pr_number_from_comments(owner, repo, issue_number)

        # Format score
        sets_html = "".join([f"<li>{s['player1_games']}-{s['player2_games']}</li>" for s in match_data["sets"]])
        score_html = f"<ul>{sets_html}</ul>"

        matches.append({
            "date": match_data["date"],
            "player1": match_data["player1"],
            "player2": match_data["player2"],
            "score": score_html,
            "issue_url": f"https://github.com/{owner}/{repo}/issues/{issue_number}",
            "pr_url": f"https://github.com/{owner}/{repo}/pull/{pr_number}" if pr_number else ""
        })

    # Generate the HTML table rows
    table_rows = ""
    for match in matches:
        player1_link = f'<a href="https://github.com/{match["player1"]}">{match["player1"]}</a>'
        player2_link = f'<a href="https://github.com/{match["player2"]}">{match["player2"]}</a>'
        pr_link = f'<a href="{match["pr_url"]}">PR</a>' if match["pr_url"] else "N/A"
        issue_link = f'<a href="{match["issue_url"]}">Issue</a>'

        table_rows += f"""
        <tr>
            <td>{match["date"]}</td>
            <td>{player1_link} vs {player2_link}</td>
            <td>{match["score"]}</td>
            <td>{issue_link}</td>
            <td>{pr_link}</td>
        </tr>
        """

    html_table = f"""
    <table class="table table-striped table-hover">
        <thead>
            <tr>
                <th>Date</th>
                <th>Players</th>
                <th>Score</th>
                <th>Issue</th>
                <th>PR</th>
            </tr>
        </thead>
        <tbody>
            {table_rows}
        </tbody>
    </table>
    """

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    repo_url = f"https://github.com/{owner}/{repo}"

    html_template = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Match History</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body {{ padding: 2rem; }}
            .container {{ max-width: 800px; }}
            h1 {{ margin-bottom: 1.5rem; }}
            .footer {{ margin-top: 2rem; font-size: 0.8rem; color: #6c757d; }}
            ul {{ margin-bottom: 0; padding-left: 1.5rem; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎾 Match History</h1>
            {html_table}
            <div class="footer">
                <p>Last updated: {timestamp}</p>
                <p><a href="index.html">Back to Leaderboard</a> | <a href="{repo_url}">GitHub Repository</a></p>
            </div>
        </div>
    </body>
    </html>
    """

    # If an output_dir is provided, use it; otherwise, create a temp dir
    if output_dir:
        # We are being called by another script; no need to return the dir
        output_file = os.path.join(output_dir, "history.html")
        with open(output_file, "w") as f:
            f.write(html_template)
        return None, output_file

    # Standalone execution for testing or other uses
    temp_dir = tempfile.mkdtemp(prefix="tennis_history_")
    output_file = os.path.join(temp_dir, "history.html")
    with open(output_file, "w") as f:
        f.write(html_template)
    return temp_dir, output_file


if __name__ == "__main__":
    temp_dir, _ = build_history_page()
    if temp_dir and os.environ.get("GITHUB_ACTIONS") == "true":
        with open(os.environ.get("GITHUB_OUTPUT", "/dev/null"), "a") as f:
            f.write(f"history_temp_dir={temp_dir}")
