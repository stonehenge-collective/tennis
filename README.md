# Tennis Match Tracker

This repository contains an automated system for tracking tennis matches and calculating player rankings using the Elo rating system. The entire process is managed through GitHub Issues and Actions, making it easy to use, especially on mobile devices.

[**View the Live Leaderboard**](https://github-org-or-username.github.io/fork-of-this-repo)

## Initial Setup (For New Tennis Leagues)

If you're setting up this system for your own tennis league, follow these one-time configuration steps:

### 1. Fork This Repository

- Click the **"Fork"** button at the top of this repository
- Choose your GitHub account or organization as the destination
- Keep the repository name as "tennis" or rename it for your league

### 2. Configure Repository Settings

After forking, you'll need to configure several settings in your new repository:

#### Enable Issues

1. Go to your repository **Settings** → **General**
2. Under "Features", check **"Issues"** to enable them
3. Issues are disabled by default in forks but required for match recording

#### Enable GitHub Actions to Create Pull Requests

1. Go to your repository **Settings** → **Actions** → **General**
2. Under "Workflow permissions", select **"Read and write permissions"**
3. Check **"Allow GitHub Actions to create and approve pull requests"**

Note: If you forked this under an organization, you need to enable the "Allow GitHub Actions to create and approve pull requests" option for the organization or else the organization's setting will override the repository setting.

#### Enable GitHub Pages

1. Go to your repository **Settings** → **Pages**
2. Under "Source", select **"GitHub Actions"**
3. This allows the automated workflows to deploy your leaderboard

### 3. Create Required Labels

Create these labels in your repository (**Issues** → **Labels** → **New label**):

- **`new-match`** (color: #0E8A16) - Used by the issue template to trigger match processing
- **`ranking-update`** (color: #0052CC) - Applied to automated ranking update pull requests

### 4. Add Your Players

Edit the `players.yml` file to include the GitHub usernames of all players in your league (you can delete the example players):

```yaml
- github-username-of-player-1
- github-username-of-player-2
- ...
```

### 5. Update the README Links

Update the live leaderboard link in this README to point to your deployment:

For organizations:

```markdown
[**View the Live Leaderboard**](https://your-org.github.io/fork-of-this-repo)
```

For personal accounts:

```markdown
[**View the Live Leaderboard**](https://your-username.github.io/fork-of-this-repo)
```

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

Player rankings are calculated using the [Elo rating system](https://en.wikipedia.org/wiki/Elo_rating_system). After each match is merged, an automated workflow recalculates the ratings and creates a pull request with the updated `ranking.csv` file. Once that PR is merged, the [live leaderboard](https://github-org-or-username.github.io/fork-of-this-repo) is updated automatically.
