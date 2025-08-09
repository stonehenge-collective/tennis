import pandas as pd
import os
import tempfile
from datetime import datetime
import glob
import yaml
from collections import defaultdict


def calculate_game_records():
    """Calculates all-time game wins and losses for each player from match files."""
    game_records = defaultdict(lambda: {"won": 0, "lost": 0})
    match_files = glob.glob("matches/*.yml")

    for match_file in match_files:
        with open(match_file, "r") as f:
            match_data = yaml.safe_load(f)

        if not match_data or "players" not in match_data or "sets" not in match_data:
            continue

        winner, loser = match_data["players"]

        for s in match_data["sets"]:
            # s[0] is always the match winner's score for the set
            # s[1] is always the match loser's score for the set
            game_records[winner]["won"] += s[0]
            game_records[winner]["lost"] += s[1]
            game_records[loser]["won"] += s[1]
            game_records[loser]["lost"] += s[0]

    return dict(game_records)


def get_repo_info():
    github_repository = os.environ.get("GITHUB_REPOSITORY")
    if github_repository:
        owner, repo = github_repository.split("/")
        return owner, repo
    return "your-org", "your-repo"


def format_rank_change(change):
    if change > 0:
        return f"▲ {change}"
    elif change < 0:
        return f"▼ {abs(change)}"
    else:
        return "–"


def build_leaderboard():
    """Generates a static HTML leaderboard from ranking.csv."""
    try:
        df = pd.read_csv("ranking.csv")
    except (FileNotFoundError, pd.errors.EmptyDataError):
        print("ranking.csv not found or is empty. Creating a default leaderboard.")
        df = pd.DataFrame(columns=["player", "rating", "wins", "losses", "rank_change"])

    # Ensure all required columns exist, even if the CSV is old
    for col in ["wins", "losses", "rank_change"]:
        if col not in df.columns:
            df[col] = 0

    # Sort by rating, descending
    df = df.sort_values(by="rating", ascending=False).reset_index(drop=True)
    df.index += 1
    df.index.name = "Rank"

    # Calculate game records
    game_records = calculate_game_records()

    # Generate the HTML table rows
    table_rows = ""
    for rank, row in df.iterrows():
        player = row["player"]
        player_link = f'<a href="https://github.com/{player}">{player}</a>'
        player_games = game_records.get(player, {"won": 0, "lost": 0})
        record = f'{player_games["won"]}-{player_games["lost"]}'
        rank_change = format_rank_change(int(row["rank_change"]))
        table_rows += f"""
        <tr>
            <td>{rank}</td>
            <td>{player_link}</td>
            <td>{int(row["rating"])}</td>
            <td>{record}</td>
            <td>{rank_change}</td>
        </tr>
        """

    html_table = f"""
    <table class="table table-striped table-hover">
        <thead>
            <tr>
                <th>Rank</th>
                <th>Player</th>
                <th>Rating</th>
                <th>Record</th>
                <th>Change</th>
            </tr>
        </thead>
        <tbody>
            {table_rows}
        </tbody>
    </table>
    """

    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
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
            td:nth-child(5) {{ text-align: center; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎾 Tennis Leaderboard</h1>
            {html_table}
            <div class="footer">
                <p>Last updated: {timestamp}</p>
                <p><a href="{issues_url}">Record a new match</a></p>
            </div>
        </div>
    </body>
    </html>
    """

    temp_dir = tempfile.mkdtemp(prefix="tennis_leaderboard_")
    output_file = os.path.join(temp_dir, "index.html")

    with open(output_file, "w") as f:
        f.write(html_template)

    return temp_dir, output_file


if __name__ == "__main__":
    temp_dir, output_file = build_leaderboard()
    if os.environ.get("GITHUB_ACTIONS") == "true":
        with open(os.environ.get("GITHUB_OUTPUT", "/dev/null"), "a") as f:
            f.write(f"temp_dir={temp_dir}")
