# Tennis Match Tracker

This repository contains an automated system for tracking tennis matches and calculating player rankings using the Elo rating system. The entire process is managed through GitHub Issues and Actions, making it easy to use, especially on mobile devices.

[**View the Live Leaderboard**](https://stonehenge-collective.github.io/sc-tennis-league)

## How to Record a Match

Follow these simple steps to record a match and have the rankings updated automatically.

1. **Open the Issue Form**: Go to the "Issues" tab of this repository and click on the **"🎾 Record a match"** button.
2. **Fill in the Details**:
    - **Match date**: The date the match was played (in YYYY-MM-DD format).
    - **Players**: The GitHub handles of the two players, separated by a comma. **The winner must be listed first.** (e.g., `@winner, @loser`)
    - **Sets**: The score of each set, one per line. The winner's score must be listed first. (e.g., `6-3`)
3. **Submit the Issue**: Click "Submit new issue".
4. **Review and Approve the PR**: A bot will create a pull request (PR) with the match data. The two players involved will be requested to review it.
5. **Merge the PR**: Once the PR is approved, it can be merged. The rankings will be automatically updated within a minute or two.

That's it! No command line, no code, just a simple form.

## Ranking System

Player rankings are calculated using the [Elo rating system](https://en.wikipedia.org/wiki/Elo_rating_system). After each match is merged, an automated workflow recalculates the ratings and creates a pull request with the updated `ranking.csv` file. Once that PR is merged, the [live leaderboard](https://stonehenge-collective.github.io/sc-tenis-league) is updated automatically.

