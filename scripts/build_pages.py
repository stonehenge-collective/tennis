import pandas as pd
import os
import tempfile
from datetime import datetime


def get_repo_info():
    github_repository = os.environ.get("GITHUB_REPOSITORY")
    if github_repository:
        owner, repo = github_repository.split("/")
        return owner, repo

    return "your-org", "your-repo"


def build_leaderboard():
    """Generates a static HTML leaderboard from ranking.csv."""
    try:
        df = pd.read_csv("ranking.csv")
    except FileNotFoundError:
        print("ranking.csv not found. Creating a default leaderboard.")
        df = pd.DataFrame(columns=["player", "rating"])

    # Sort by rating, descending
    df = df.sort_values(by="rating", ascending=False).reset_index(drop=True)
    df.index += 1  # Start ranking from 1
    df.index.name = "Rank"

    # Generate the HTML table
    html_table = df.to_html(index=True, classes="table table-striped table-hover")

    # Get the current timestamp
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    # Get repository information for dynamic URLs
    owner, repo = get_repo_info()
    issues_url = f"https://github.com/{owner}/{repo}/issues/new?template=match.yml"

    # Basic HTML template
    html_template = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Tennis Leaderboard</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body {{
                padding: 2rem;
            }}
            .container {{
                max-width: 800px;
            }}
            h1 {{
                margin-bottom: 1.5rem;
            }}
            .footer {{
                margin-top: 2rem;
                font-size: 0.8rem;
                color: #6c757d;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎾 Tennis Leaderboard</h1>
            {html_table}
            <div class="footer">
                <p>Last updated: {timestamp}</p>
                <p>
                    <a href="{issues_url}">Record a new match</a>
                </p>
            </div>
        </div>
    </body>
    </html>
    """

    # Create a temporary directory and write the HTML
    temp_dir = tempfile.mkdtemp(prefix="tennis_leaderboard_")
    output_file = os.path.join(temp_dir, "index.html")

    with open(output_file, "w") as f:
        f.write(html_template)

    return temp_dir, output_file


if __name__ == "__main__":
    temp_dir, output_file = build_leaderboard()

    # write to GitHub Actions environment if running in CI so that the pages-deploy.yml can use it
    if os.environ.get("GITHUB_ACTIONS") == "true":
        with open(os.environ.get("GITHUB_OUTPUT", "/dev/null"), "a") as f:
            f.write(f"temp_dir={temp_dir}\n")
