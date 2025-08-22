import glob
import sys
import yaml
import pandas as pd

K = 32
ratings = {}
# Stats per team. We'll compute:
# - set_wins/set_losses: count of sets won/lost
# - game_wins/game_losses: total games won/lost across all recorded sets
stats = {}


def expected(rA, rB):
    return 1 / (1 + 10 ** ((rB - rA) / 400))


def normalize_team(team_players):
    """Normalize team representation so PlayerA,PlayerB == PlayerB,PlayerA"""
    if len(team_players) != 2:
        raise ValueError(f"Team must have exactly 2 players, got {len(team_players)}")
    
    # Sort players alphabetically to ensure consistent team representation
    sorted_players = sorted(team_players)
    return f"{sorted_players[0]}, {sorted_players[1]}"


def _ensure_team(team: str) -> None:
    if team not in stats:
        stats[team] = {
            "set_wins": 0,
            "set_losses": 0,
            "game_wins": 0,
            "game_losses": 0,
        }


def apply_match(match):
    """Update ratings and aggregates from a single doubles match file.

    Elo is applied per set. Each set is an independent event that updates
    the teams' ratings based solely on who won the set (score margin ignored).
    """
    team1_players = match["team1"]
    team2_players = match["team2"]

    # Normalize team names
    team1 = normalize_team(team1_players)
    team2 = normalize_team(team2_players)

    # Ensure team entries exist for aggregation
    _ensure_team(team1)
    _ensure_team(team2)

    # Iterate sets: first number maps to team1's games, second to team2's
    sets = match.get("sets") or []
    for s in sets:
        try:
            t1_games = int(s[0])
            t2_games = int(s[1])
        except (ValueError, TypeError, IndexError):
            # Skip malformed set entries
            continue

        # Aggregate games
        stats[team1]["game_wins"] += t1_games
        stats[team1]["game_losses"] += t2_games
        stats[team2]["game_wins"] += t2_games
        stats[team2]["game_losses"] += t1_games

        # Determine set winner
        if t1_games == t2_games:
            # Ignore invalid/tied set
            continue

        set_winner = team1 if t1_games > t2_games else team2
        set_loser = team2 if set_winner == team1 else team1

        # Record set W/L
        stats[set_winner]["set_wins"] += 1
        stats[set_loser]["set_losses"] += 1

        # Elo update for this set (independent event)
        rW = ratings.get(set_winner, 1200)
        rL = ratings.get(set_loser, 1200)
        eW = expected(rW, rL)
        eL = expected(rL, rW)
        ratings[set_winner] = rW + K * (1 - eW)
        ratings[set_loser] = rL + K * (0 - eL)


def main():
    """Main function to calculate and print doubles rankings."""
    # All teams start with default rating of 1200 - no CSV bootstrapping needed

    # Process doubles matches
    for fn in sorted(glob.glob("doubles-matches/*.yml")):
        with open(fn) as f:
            try:
                match_data = yaml.safe_load(f)
                if match_data and "team1" in match_data and "team2" in match_data:
                    apply_match(match_data)
            except yaml.YAMLError as e:
                print(f"Error reading {fn}: {e}", file=sys.stderr)

    # Create new DataFrame with updated ratings and stats
    new_teams_data = []
    for team, rating in sorted(ratings.items(), key=lambda item: -item[1]):
        team_stats = stats.get(
            team,
            {
                "set_wins": 0,
                "set_losses": 0,
                "game_wins": 0,
                "game_losses": 0,
            },
        )
        new_teams_data.append(
            {
                "team": team,
                "rating": round(rating, 1),
                # Primary stats
                "set_wins": team_stats["set_wins"],
                "set_losses": team_stats["set_losses"],
                "game_wins": team_stats["game_wins"],
                "game_losses": team_stats["game_losses"],
            }
        )

    if not new_teams_data:
        # Handle case with no teams
        df = pd.DataFrame(
            columns=[
                "team",
                "rating",
                "set_wins",
                "set_losses",
                "game_wins",
                "game_losses",
            ]
        )
        df.to_csv(sys.stdout, index=False)
        return

    df = pd.DataFrame(new_teams_data)
    df = df.sort_values(by="rating", ascending=False).reset_index(drop=True)

    # Select and order columns for the output
    desired_columns = [
        "team",
        "rating",
        "set_wins",
        "set_losses",
        "game_wins",
        "game_losses",
    ]

    # Ensure all desired columns exist (defensive in case of missing keys)
    for col in desired_columns:
        if col not in df.columns:
            df[col] = 0
    output_df = df[desired_columns]

    output_df.to_csv(sys.stdout, index=False)


if __name__ == "__main__":
    main()