# SC Tennis League

[![leaderboard](https://github.com/stonehenge-collective/tennis/actions/workflows/pages-deploy.yml/badge.svg)](https://github.com/stonehenge-collective/tennis/actions/workflows/pages-deploy.yml)

## How to Record a Match

Follow these simple steps to record a match and have the rankings updated automatically.

1. **Open the Issue Form**: Go to the "Issues" tab of this repository, click the **"New issue"** button, and select **"🎾 Record a match"** from the template.
2. **Fill in the Details**:
    - **Title**: Do what you will.
    - **Match date**: The date the match was played (in YYYY-MM-DD format).
    - **Players**: The GitHub handles of the two players, separated by a comma. The first listed is Player 1, the second is Player 2 (e.g., `@player1, @player2`).
    - **Sets**: The score of each set, one per line. The first number is Player 1's games; the second is Player 2's games (e.g., `6-3`).
3. **Submit the Issue**: Click "Submit new issue".
4. **Review and Approve the PR**: A bot will create a pull request (PR) with the match data and link to this PR from the issue. The two players involved will be requested to review it.
5. **Merge the PR**: Once the PR is approved, it can be merged. On merge an action will be triggered that will update the rankings.csv file.
6. **Merge the PR**: Another PR will be opened that will update the rankings.csv file. You will need to merge this PR as well. Upon merge the leaderboard will be updated.

## Terminology and Rules

This section defines core terms and documents the current behavior so contributors and players share the same mental model.

- **Match**: A single github issue representing one play "session" or match. A match will contain some number of sets.
- **Set**: A line in the issue’s Sets block, e.g., `6-4`. The winner is the side with the higher games on that line.
- **Game**: The tennis unit within a set.

### Current ELO behavior

- Ratings are based on individual sets. If a Match contains multiple sets, each set contributes an ELO update independently.
- Score margin (e.g., 6‑0 vs 6‑5) does not change the ELO delta; only who won the set matters.
- Player rankings are calculated using the [Elo rating system](https://en.wikipedia.org/wiki/Elo_rating_system).
