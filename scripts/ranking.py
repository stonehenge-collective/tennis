import glob
import sys
import yaml
import pandas as pd
import numpy as np

K = 32
ratings = {}
# Stats per player. We'll compute:
# - set_wins/set_losses: count of sets won/lost
# - game_wins/game_losses: total games won/lost across all recorded sets
# - wins/losses: kept for backward compatibility (mirror set stats)
stats = {}


def expected(rA, rB):
    return 1 / (1 + 10 ** ((rB - rA) / 400))


def _ensure_player(player: str) -> None:
    if player not in stats:
        stats[player] = {
            "set_wins": 0,
            "set_losses": 0,
            "game_wins": 0,
            "game_losses": 0,
        }


def apply_match(match):
    """Updates ratings and aggregates based on a single match file.

    Ratings are updated once per match (unchanged ordering). Set and game
    aggregates are computed by iterating each recorded set.
    """
    winner, loser = match["players"]

    # Ratings (keep existing behavior)
    rW = ratings.get(winner, 1200)
    rL = ratings.get(loser, 1200)
    eW = expected(rW, rL)
    eL = expected(rL, rW)
    ratings[winner] = rW + K * (1 - eW)
    ratings[loser] = rL + K * (0 - eL)

    # Ensure player entries exist
    _ensure_player(winner)
    _ensure_player(loser)

    # Compute per-set and per-game aggregates
    sets = match.get("sets") or []
    for s in sets:
        # By convention: s[0] is match winner's games for the set, s[1] is match loser's
        try:
            w_games = int(s[0])
            l_games = int(s[1])
        except (ValueError, TypeError, IndexError):
            # Skip malformed set entries
            continue

        # Game aggregates
        stats[winner]["game_wins"] += w_games
        stats[winner]["game_losses"] += l_games
        stats[loser]["game_wins"] += l_games
        stats[loser]["game_losses"] += w_games

        # Set winner/loser determination
        if w_games > l_games:
            stats[winner]["set_wins"] += 1
            stats[loser]["set_losses"] += 1
        elif l_games > w_games:
            stats[loser]["set_wins"] += 1
            stats[winner]["set_losses"] += 1
        # If equal, ignore; ties should not occur in valid tennis set scores


def main():
    """Main function to calculate and print rankings."""
    # Load existing rankings to bootstrap current ratings
    try:
        old_df = pd.read_csv("ranking.csv")
        old_df = old_df.sort_values(by="rating", ascending=False).reset_index(drop=True)
        for _, row in old_df.iterrows():
            player = row["player"]
            ratings[player] = row["rating"]
    except (FileNotFoundError, pd.errors.EmptyDataError):
        pass

    # Process matches
    for fn in sorted(glob.glob("matches/*.yml")):
        with open(fn) as f:
            try:
                match_data = yaml.safe_load(f)
                if match_data and "players" in match_data:
                    apply_match(match_data)
            except yaml.YAMLError as e:
                print(f"Error reading {fn}: {e}", file=sys.stderr)

    # Create new DataFrame with updated ratings and stats
    new_players_data = []
    for p, r in sorted(ratings.items(), key=lambda item: -item[1]):
        player_stats = stats.get(
            p,
            {
                "set_wins": 0,
                "set_losses": 0,
                "game_wins": 0,
                "game_losses": 0,
            },
        )
        new_players_data.append(
            {
                "player": p,
                "rating": round(r, 1),
                # Primary stats
                "set_wins": player_stats["set_wins"],
                "set_losses": player_stats["set_losses"],
                "game_wins": player_stats["game_wins"],
                "game_losses": player_stats["game_losses"],
            }
        )

    if not new_players_data:
        # Handle case with no players
        df = pd.DataFrame(
            columns=[
                "player",
                "rating",
                "set_wins",
                "set_losses",
                "game_wins",
                "game_losses",
            ]
        )
        df.to_csv(sys.stdout, index=False)
        return

    df = pd.DataFrame(new_players_data)
    df = df.sort_values(by="rating", ascending=False).reset_index(drop=True)

    # Select and order columns for the output
    desired_columns = [
        "player",
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
