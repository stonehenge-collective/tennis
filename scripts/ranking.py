import glob
import sys
import yaml
import pandas as pd
import numpy as np

K = 32
ratings = {}
stats = {}  # To store player stats (wins, losses)


def expected(rA, rB):
    return 1 / (1 + 10 ** ((rB - rA) / 400))


def apply_match(match):
    """Updates ratings and stats based on a single match."""
    winner, loser = match["players"]
    rW = ratings.get(winner, 1200)
    rL = ratings.get(loser, 1200)
    eW = expected(rW, rL)
    eL = expected(rL, rW)
    ratings[winner] = rW + K * (1 - eW)
    ratings[loser] = rL + K * (0 - eL)

    # Update stats
    for player in [winner, loser]:
        if player not in stats:
            stats[player] = {"wins": 0, "losses": 0}
    stats[winner]["wins"] += 1
    stats[loser]["losses"] += 1


def main():
    """Main function to calculate and print rankings."""
    # Load existing rankings to get old rank and historical stats
    try:
        old_df = pd.read_csv("ranking.csv")
        # Sort by rating to establish rank
        old_df = old_df.sort_values(by="rating", ascending=False).reset_index(drop=True)
        old_ranks = {row["player"]: i + 1 for i, row in old_df.iterrows()}
        for _, row in old_df.iterrows():
            player = row["player"]
            ratings[player] = row["rating"]
            stats[player] = {"wins": row.get("wins", 0), "losses": row.get("losses", 0)}
    except (FileNotFoundError, pd.errors.EmptyDataError):
        old_ranks = {}

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
        player_stats = stats.get(p, {"wins": 0, "losses": 0})
        new_players_data.append(
            {
                "player": p,
                "rating": round(r, 1),
                "wins": player_stats["wins"],
                "losses": player_stats["losses"],
            }
        )

    if not new_players_data:
        # Handle case with no players
        df = pd.DataFrame(columns=["player", "rating", "wins", "losses", "rank_change"])
        df.to_csv(sys.stdout, index=False)
        return

    df = pd.DataFrame(new_players_data)
    df["new_rank"] = df.index + 1

    # Calculate rank change
    def get_rank_change(row):
        old_rank = old_ranks.get(row["player"])
        if old_rank is None:
            return 0  # New player
        return old_rank - row["new_rank"]

    df["rank_change"] = df.apply(get_rank_change, axis=1)

    # Select and order columns for the output
    output_df = df[["player", "rating", "wins", "losses", "rank_change"]]

    output_df.to_csv(sys.stdout, index=False)


if __name__ == "__main__":
    main()
