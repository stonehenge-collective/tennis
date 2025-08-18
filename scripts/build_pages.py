import pandas as pd
import os
import tempfile
from datetime import datetime, timezone
from github_utils import get_repo_owner_and_name_or_default


"""
This page builder now relies solely on `ranking.csv` for all aggregates
(rating, set and game records). It no longer parses
match files. This avoids duplication of logic with `scripts/ranking.py`.
"""


def get_repo_info():
    # Use shared helper for consistent behavior (with defaults locally)
    return get_repo_owner_and_name_or_default()


from scripts.build_history import build_history_page


def build_site():
    """
    Generates all static HTML pages for the site.
    - Leaderboard (index.html)
    - Match History (history.html)
    """
    # Create a single temporary directory for all pages
    temp_dir = tempfile.mkdtemp(prefix="tennis_site_")

    # --- Build Leaderboard Page (index.html) ---
    try:
        df = pd.read_csv("ranking.csv")
    except FileNotFoundError:
        # Create an empty dataframe if ranking.csv doesn't exist
        df = pd.DataFrame(columns=["player", "rating", "set_wins", "set_losses", "game_wins", "game_losses"])
    for col in [
        "player",
        "rating",
        "set_wins",
        "set_losses",
        "game_wins",
        "game_losses",
    ]:
        if col not in df.columns:
            df[col] = 0

    # Sort by rating, descending
    df = df.sort_values(by="rating", ascending=False).reset_index(drop=True)
    df.index += 1
    df.index.name = "Rank"

    # Generate the HTML table rows
    table_rows = ""
    for rank, row in df.iterrows():
        player = row["player"]
        player_link = f'<a href="https://github.com/{player}">{player}</a>'
        games_record = f'{int(row.get("game_wins", 0))}-{int(row.get("game_losses", 0))}'
        sets_record = f'{int(row.get("set_wins", 0))}-{int(row.get("set_losses", 0))}'
        table_rows += f"""
        <tr>
            <td>{rank}</td>
            <td>{player_link}</td>
            <td>{int(row["rating"])}</td>
            <td>{sets_record}</td>
            <td>{games_record}</td>
        </tr>
        """

    html_table = f"""
    <table class="table table-striped table-hover">
        <thead>
            <tr>
                <th>Rank</th>
                <th>Player</th>
                <th>Rating</th>
                <th>Sets W-L</th>
                <th>Games W-L</th>
            </tr>
        </thead>
        <tbody>
            {table_rows}
        </tbody>
    </table>
    """

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    owner, repo = get_repo_info()
    issues_url = f"https://github.com/{owner}/{repo}/issues/new?template=match.yml"

    html_template = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Tennis Leaderboard</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body {{ padding: 2rem; }}
            .container {{ max-width: 800px; }}
            h1 {{ margin-bottom: 1.5rem; }}
            .footer {{ margin-top: 2rem; font-size: 0.8rem; color: #6c757d; }}
            td:nth-child(6) {{ text-align: center; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎾 Tennis Leaderboard</h1>
            {html_table}
            <div class="footer">
                <p>Last updated: {timestamp}</p>
                <p>
                    <a href="{issues_url}">Record a new match</a> |
                    <a href="history.html">Match History</a>
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    index_output_file = os.path.join(temp_dir, "index.html")
    with open(index_output_file, "w") as f:
        f.write(html_template)

    # --- Build Match History Page (history.html) ---
    build_history_page(output_dir=temp_dir)

    return temp_dir, index_output_file


if __name__ == "__main__":
    temp_dir, _ = build_site()
    if os.environ.get("GITHUB_ACTIONS") == "true":
        with open(os.environ.get("GITHUB_OUTPUT", "/dev/null"), "a") as f:
            f.write(f"temp_dir={temp_dir}")
