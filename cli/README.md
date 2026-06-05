# Tennis CLI

A command-line tool to interact with the tennis repository - trigger workflows and create match issues.

## Installation

```bash
cd cli
go build -o tennis
```

## Configuration

The CLI requires a GitHub token to interact with the repository. It is resolved in this order:

1. Command line flag: `--token your_token_here`
2. Environment variable: `GITHUB_TOKEN=your_token_here`
3. Environment variable: `GH_TOKEN=your_token_here`
4. The `gh` CLI's stored token (via `gh auth token`), if `gh` is installed and authenticated

So if you're already logged in with `gh auth login`, no token setup is needed.

The repository owner/name is resolved in this order:

1. Command line flags: `--owner owner --repo repo`
2. Environment variable: `GITHUB_REPOSITORY=owner/repo`
3. The `origin` remote of the current git checkout (https or ssh URLs)
4. Defaults to `stonehenge-collective/tennis`

## Usage

### Trigger Workflows

Trigger the rebuild rankings workflow:

```bash
./tennis workflow trigger rebuild-rankings
```

You can also use the full workflow name or filename:

```bash
./tennis workflow trigger "🏆 Rebuild Rankings"
./tennis workflow trigger rebuild-rankings.yml
```

### Create Match Issues

#### Singles Match

Create a singles match issue:

```bash
./tennis match singles --players "@player_one,@player_two" --sets "6-3,4-6,6-4" --date "2025-01-15"
```

Short form:

```bash
./tennis match singles -p "@player_one,@player_two" -s "6-3,4-6,6-4" -d "2025-01-15"
```

If no date is provided, today's date will be used:

```bash
./tennis match singles -p "@player_one,@player_two" -s "6-3,4-6,6-4"
```

#### Doubles Match

Create a doubles match issue:

```bash
./tennis match doubles --teams "@player_one,@player_two||@player_three,@player_four" --sets "6-3,4-6,6-4" --date "2025-01-15"
```

Short form:

```bash
./tennis match doubles -t "@player_one,@player_two||@player_three,@player_four" -s "6-3,4-6,6-4" -d "2025-01-15"
```

## Examples

```bash
# Set up environment
export GITHUB_TOKEN=your_token_here
export GITHUB_REPOSITORY=stonehenge-collective/tennis

# Trigger rebuild rankings workflow
./tennis workflow trigger rebuild-rankings

# Create a singles match (Player 1 beats Player 2)
./tennis match singles -p "@player_one,@player_two" -s "6-3,4-6,6-4"

# Create a doubles match (Player 1 & Player 2 beat Player 3 & Player 4)
./tennis match doubles -t "@player_one,@player_two||@player_three,@player_four" -s "6-3,4-6,10-8"

# Use specific date
./tennis match singles -p "@player_one,@player_two" -s "6-2,6-1" -d "2025-01-15"
```

### Flags for match commands

Both `match singles` and `match doubles` support:

- `--dry-run` — print the issue that would be created, without creating it (no token required)
- `--no-validate` — skip the check that each player handle is a real GitHub user

Before creating an issue, the CLI:

- verifies every `@handle` resolves to a real GitHub user (skip with `--no-validate`). Note this only checks that the account exists, not that they're a registered league player.
- (singles) checks the first-listed player actually won more sets, to catch swapped arguments

```bash
# Preview without creating anything
./tennis match singles -p "@player_one,@player_two" -s "6-3,6-2" --dry-run
```

## Notes

- Players should be listed with the winner first
- Teams in doubles matches should be listed with the winning team first
- Sets should be in the format `games-games` (e.g., `6-3`, `7-5`, `10-8`)
- Dates must be in YYYY-MM-DD format
- GitHub handles should include the @ symbol
