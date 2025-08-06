import pandas as pd
from datetime import datetime

def build_leaderboard():
    """Generates a static HTML leaderboard from ranking.csv."""
    try:
        df = pd.read_csv('ranking.csv')
    except FileNotFoundError:
        print("ranking.csv not found. Creating a default leaderboard.")
        df = pd.DataFrame(columns=['player', 'rating'])

    # Sort by rating, descending
    df = df.sort_values(by='rating', ascending=False).reset_index(drop=True)
    df.index += 1 # Start ranking from 1
    df.index.name = "Rank"

    # Generate the HTML table
    html_table = df.to_html(index=True, classes='table table-striped table-hover')

    # Get the current timestamp
    timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')

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
                    <a href="https://github.com/your-org/your-repo/issues/new/choose">Record a new match</a>
                </p>
            </div>
        </div>
    </body>
    </html>
    """

    # Write the HTML to docs/index.html
    with open('docs/index.html', 'w') as f:
        f.write(html_template)

    print("Leaderboard successfully built at docs/index.html")

if __name__ == "__main__":
    build_leaderboard()
