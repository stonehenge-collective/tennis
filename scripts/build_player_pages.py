import glob
import sys
import yaml
import pandas as pd
import os
import json
import re
from datetime import datetime
from github_utils import get_repo_owner_and_name_or_default

K = 32
PLAYER_DATA = {} # {player: {singles: [], doubles: []}}

def expected(rA, rB):
    return 1 / (1 + 10 ** ((rB - rA) / 400))

def get_issue_number_from_filename(filename):
    # Extracts the issue number from a filename like "2024-01-01-123.yml"
    match = re.search(r'-(\d+)\.yml$', filename)
    if match:
        return int(match.group(1))
    return None

def calculate_elo_history():
    """
    Calculates ELO history for all players for both singles and doubles.
    """
    singles_ratings = {}
    doubles_ratings = {}

    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)
    singles_matches_dir = os.path.join(repo_root, 'singles-matches', '*.yml')
    doubles_matches_dir = os.path.join(repo_root, 'doubles-matches', '*.yml')
    match_files = glob.glob(singles_matches_dir) + glob.glob(doubles_matches_dir)

    # Sort matches by date, which is the prefix of the filename
    match_files.sort()

    for fn in match_files:
        with open(fn) as f:
            match_data = yaml.safe_load(f)
            match_date = datetime.strptime(match_data['date'], '%Y-%m-%d').isoformat()
            issue_number = get_issue_number_from_filename(fn)

            if 'players' in match_data: # Singles match
                player1, player2 = match_data['players']

                for p in [player1, player2]:
                    if p not in PLAYER_DATA:
                        PLAYER_DATA[p] = {'singles': [], 'doubles': []}

                r1 = singles_ratings.get(player1, 1200)
                r2 = singles_ratings.get(player2, 1200)

                for s in match_data.get('sets', []):
                    p1_games, p2_games = int(s[0]), int(s[1])
                    if p1_games == p2_games: continue

                    winner, loser = (player1, player2) if p1_games > p2_games else (player2, player1)

                    rW_before = singles_ratings.get(winner, 1200)
                    rL_before = singles_ratings.get(loser, 1200)

                    eW = expected(rW_before, rL_before)
                    eL = expected(rL_before, rW_before)

                    rW_after = rW_before + K * (1 - eW)
                    rL_after = rL_before + K * (0 - eL)

                    elo_change_winner = rW_after - rW_before
                    elo_change_loser = rL_after - rL_before

                    singles_ratings[winner] = rW_after
                    singles_ratings[loser] = rL_after

                    # Add data points for both players
                    PLAYER_DATA[winner]['singles'].append({
                        'date': match_date,
                        'opponent': loser,
                        'sets': f"{p1_games}-{p2_games}" if winner==player1 else f"{p2_games}-{p1_games}",
                        'elo_change': round(elo_change_winner),
                        'elo': round(rW_after),
                        'result': 'W',
                        'issue_number': issue_number
                    })
                    PLAYER_DATA[loser]['singles'].append({
                        'date': match_date,
                        'opponent': winner,
                        'sets': f"{p2_games}-{p1_games}" if loser==player1 else f"{p1_games}-{p2_games}",
                        'elo_change': round(elo_change_loser),
                        'elo': round(rL_after),
                        'result': 'L',
                        'issue_number': issue_number
                    })

            elif 'team1' in match_data: # Doubles match
                team1 = match_data['team1']
                team2 = match_data['team2']

                for p in team1 + team2:
                    if p not in PLAYER_DATA:
                        PLAYER_DATA[p] = {'singles': [], 'doubles': []}

                r_team1_avg = sum(doubles_ratings.get(p, 1200) for p in team1) / 2
                r_team2_avg = sum(doubles_ratings.get(p, 1200) for p in team2) / 2

                for s in match_data.get('sets', []):
                    t1_games, t2_games = int(s[0]), int(s[1])
                    if t1_games == t2_games: continue

                    winning_team, losing_team = (team1, team2) if t1_games > t2_games else (team2, team1)

                    e_win = expected(r_team1_avg, r_team2_avg) if winning_team == team1 else expected(r_team2_avg, r_team1_avg)

                    elo_change_per_player = K * (1 - e_win) / 2

                    for p in winning_team:
                        r_before = doubles_ratings.get(p, 1200)
                        r_after = r_before + elo_change_per_player
                        doubles_ratings[p] = r_after
                        PLAYER_DATA[p]['doubles'].append({
                            'date': match_date,
                            'opponent': ", ".join(losing_team),
                            'sets': f"{t1_games}-{t2_games}" if winning_team==team1 else f"{t2_games}-{t1_games}",
                            'elo_change': round(elo_change_per_player),
                            'elo': round(r_after),
                            'result': 'W',
                            'issue_number': issue_number,
                            'partner': [partner for partner in winning_team if partner != p][0]
                        })
                    for p in losing_team:
                        r_before = doubles_ratings.get(p, 1200)
                        r_after = r_before - elo_change_per_player
                        doubles_ratings[p] = r_after
                        PLAYER_DATA[p]['doubles'].append({
                            'date': match_date,
                            'opponent': ", ".join(winning_team),
                            'sets': f"{t2_games}-{t1_games}" if losing_team==team1 else f"{t1_games}-{t2_games}",
                            'elo_change': round(elo_change_per_player),
                            'elo': round(r_after),
                            'result': 'L',
                            'issue_number': issue_number,
                            'partner': [partner for partner in losing_team if partner != p][0]
                        })


def generate_player_pages(output_dir):
    history_dir = os.path.join(output_dir, 'history')
    os.makedirs(history_dir, exist_ok=True)

    owner, repo = get_repo_owner_and_name_or_default()
    repo_url = f"https://github.com/{owner}/{repo}"

    for player, data in PLAYER_DATA.items():
        # Generate JSON file for the player
        json_path = os.path.join(history_dir, f'{player}.json')
        with open(json_path, 'w') as f:
            json.dump(data, f)

        # Generate HTML page for the player
        html_path = os.path.join(output_dir, f'player_profile_{player}.html')

        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{player}'s ELO History</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-adapter-date-fns/dist/chartjs-adapter-date-fns.bundle.min.js"></script>
    <style>
        body {{ padding: 2rem; }}
        .chart-container {{ height: 400px; }}
        .footer {{ margin-top: 2rem; padding-top: 2rem; border-top: 1px solid #dee2e6; font-size: 0.9rem; color: #6c757d; text-align: center; }}
    </style>
</head>
<body>
    <div class="container">
        <h1 class="mb-4">{player}'s ELO History</h1>

        <div class="mb-3">
            <select id="matchTypeSelector" class="form-select" style="width: auto;">
                <option value="singles">Singles</option>
                <option value="doubles">Doubles</option>
            </select>
        </div>

        <div class="chart-container">
            <canvas id="eloChart"></canvas>
        </div>

        <div class="footer">
            <p><a href="index.html">Back to Leaderboards</a> | <a href="history.html">Match History</a> | <a href="{repo_url}">GitHub Repository</a></p>
        </div>
    </div>

    <script>
        document.addEventListener('DOMContentLoaded', function () {{
            const ctx = document.getElementById('eloChart').getContext('2d');
            let chart;
            let playerData;

            function createChart(data, matchType) {{
                if (chart) {{
                    chart.destroy();
                }}

                const labels = data.map(d => new Date(d.date));
                const eloData = data.map(d => d.elo);

                chart = new Chart(ctx, {{
                    type: 'line',
                    data: {{
                        labels: labels,
                        datasets: [{{
                            label: 'ELO',
                            data: eloData,
                            borderColor: 'rgb(75, 192, 192)',
                            tension: 0.1
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {{
                            x: {{
                                type: 'time',
                                time: {{
                                    unit: 'day'
                                }},
                                title: {{
                                    display: true,
                                    text: 'Date'
                                }}
                            }},
                            y: {{
                                title: {{
                                    display: true,
                                    text: 'ELO'
                                }}
                            }}
                        }},
                        plugins: {{
                            tooltip: {{
                                callbacks: {{
                                    label: function(context) {{
                                        const d = data[context.dataIndex];
                                        let tooltip = `ELO: ${{d.elo}} (${{d.elo_change > 0 ? '+' : ''}}${{d.elo_change}})`;
                                        tooltip += `\\nResult: ${{d.result}} vs ${{d.opponent}}`;
                                        if (d.partner) {{
                                            tooltip += ` (with ${{d.partner}})`;
                                        }}
                                        tooltip += `\\nSets: ${{d.sets}}`;
                                        return tooltip;
                                    }}
                                }}
                            }}
                        }},
                        onClick: (e) => {{
                            const points = chart.getElementsAtEventForMode(e, 'nearest', {{ intersect: true }}, true);
                            if (points.length) {{
                                const firstPoint = points[0];
                                const dataPoint = data[firstPoint.index];
                                if (dataPoint.issue_number) {{
                                    window.open(`{repo_url}/issues/${{dataPoint.issue_number}}`, '_blank');
                                }}
                            }}
                        }}
                    }}
                }});
            }}

            fetch('history/{player}.json')
                .then(response => response.json())
                .then(data => {{
                    playerData = data;
                    const matchTypeSelector = document.getElementById('matchTypeSelector');

                    createChart(playerData.singles, 'singles');

                    matchTypeSelector.addEventListener('change', (event) => {{
                        createChart(playerData[event.target.value], event.target.value);
                    }});
                }});
        }});
    </script>
</body>
</html>
"""
        with open(html_path, 'w') as f:
            f.write(html_content)


def build_player_pages(output_dir):
    """
    Main function to generate all player pages.
    """
    calculate_elo_history()
    generate_player_pages(output_dir)

if __name__ == "__main__":
    output_directory = sys.argv[1] if len(sys.argv) > 1 else "dist"
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    build_player_pages(output_directory)
