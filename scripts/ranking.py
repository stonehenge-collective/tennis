import glob
import sys
import yaml
import pandas as pd
import numpy as np

K = 32
ratings = {}

def expected(rA, rB):
    return 1 / (1 + 10 ** ((rB - rA) / 400))

def apply_match(match):
    """Updates ratings based on a single match."""
    winner, loser = match['players']
    rW = ratings.get(winner, 1200)
    rL = ratings.get(loser, 1200)
    eW = expected(rW, rL)
    eL = expected(rL, rW)
    ratings[winner] = rW + K * (1 - eW)
    ratings[loser] = rL + K * (0 - eL)

def main():
    """Main function to calculate and print rankings."""
    for fn in sorted(glob.glob('matches/*.yml')):
        with open(fn) as f:
            try:
                match_data = yaml.safe_load(f)
                if match_data and 'players' in match_data:
                    apply_match(match_data)
            except yaml.YAMLError as e:
                print(f"Error reading {fn}: {e}", file=sys.stderr)

    df = pd.DataFrame([
        {'player': p, 'rating': round(r, 1)}
        for p, r in sorted(ratings.items(), key=lambda item: -item[1])
    ])

    df.to_csv(sys.stdout, index=False)

if __name__ == '__main__':
    main()
