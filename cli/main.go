package main

import (
	"context"
	"fmt"
	"os"
	"os/exec"
	"strings"

	"github.com/google/go-github/v67/github"
	"github.com/spf13/cobra"
	"golang.org/x/oauth2"
)

const version = "1.0.0"

var (
	token string
	owner string
	repo  string
)

var rootCmd = &cobra.Command{
	Use:     "tennis",
	Version: version,
	Short:   "Tennis repository CLI tool",
	Long:    "A CLI tool to interact with the tennis repository - trigger workflows and create match issues",
	PersistentPreRunE: func(cmd *cobra.Command, args []string) error {
		// Skip token validation for version and help commands
		if cmd.Name() == "version" || cmd.Name() == "help" {
			return nil
		}

		// Get token from environment if not provided. A dry run never
		// contacts GitHub, so a token isn't required for it.
		if token == "" {
			token = os.Getenv("GITHUB_TOKEN")
			if token == "" {
				token = os.Getenv("GH_TOKEN")
			}
			// Fall back to the gh CLI's stored token if available
			if token == "" {
				token = ghAuthToken()
			}
			if token == "" && !dryRun {
				return fmt.Errorf("GitHub token required. Set GITHUB_TOKEN, run `gh auth login`, or use --token flag")
			}
		}

		// Get owner/repo from environment if not provided
		if owner == "" || repo == "" {
			githubRepo := os.Getenv("GITHUB_REPOSITORY")
			if githubRepo != "" {
				parts := splitRepoString(githubRepo)
				if len(parts) == 2 {
					owner = parts[0]
					repo = parts[1]
				}
			}
		}

		// Fall back to the current checkout's git remote so the CLI
		// targets whatever repo you're working in without flags.
		if owner == "" || repo == "" {
			if o, r, ok := repoFromGitRemote(); ok {
				if owner == "" {
					owner = o
				}
				if repo == "" {
					repo = r
				}
			}
		}

		// Final fallback
		if owner == "" {
			owner = "stonehenge-collective"
		}
		if repo == "" {
			repo = "tennis"
		}

		return nil
	},
}

// ghAuthToken returns the token stored by the `gh` CLI, or "" if gh is
// unavailable or not authenticated.
func ghAuthToken() string {
	path, err := exec.LookPath("gh")
	if err != nil {
		return ""
	}
	out, err := exec.Command(path, "auth", "token").Output()
	if err != nil {
		return ""
	}
	return strings.TrimSpace(string(out))
}

// repoFromGitRemote parses owner/repo from the origin remote of the current
// git checkout. Handles both https and ssh remote URLs.
func repoFromGitRemote() (owner, repo string, ok bool) {
	path, err := exec.LookPath("git")
	if err != nil {
		return "", "", false
	}
	out, err := exec.Command(path, "remote", "get-url", "origin").Output()
	if err != nil {
		return "", "", false
	}
	url := strings.TrimSpace(string(out))
	url = strings.TrimSuffix(url, ".git")

	// git@github.com:owner/repo  ->  owner/repo
	if i := strings.Index(url, ":"); strings.HasPrefix(url, "git@") && i != -1 {
		url = url[i+1:]
	} else if i := strings.Index(url, "github.com/"); i != -1 {
		// https://github.com/owner/repo
		url = url[i+len("github.com/"):]
	} else {
		return "", "", false
	}

	parts := strings.Split(url, "/")
	if len(parts) < 2 || parts[0] == "" || parts[1] == "" {
		return "", "", false
	}
	return parts[0], parts[1], true
}

func splitRepoString(repoString string) []string {
	for i, char := range repoString {
		if char == '/' {
			return []string{repoString[:i], repoString[i+1:]}
		}
	}
	return []string{repoString}
}

func getGitHubClient() *github.Client {
	ctx := context.Background()
	ts := oauth2.StaticTokenSource(
		&oauth2.Token{AccessToken: token},
	)
	tc := oauth2.NewClient(ctx, ts)
	return github.NewClient(tc)
}

var versionCmd = &cobra.Command{
	Use:   "version",
	Short: "Print the version number",
	Long:  "Print the version number of the tennis CLI",
	Run: func(cmd *cobra.Command, args []string) {
		fmt.Printf("tennis CLI v%s\n", version)
	},
}

func init() {
	rootCmd.PersistentFlags().StringVar(&token, "token", "", "GitHub token")
	rootCmd.PersistentFlags().StringVar(&owner, "owner", "", "Repository owner")
	rootCmd.PersistentFlags().StringVar(&repo, "repo", "", "Repository name")

	rootCmd.AddCommand(versionCmd)
}

func main() {
	if err := rootCmd.Execute(); err != nil {
		fmt.Fprintf(os.Stderr, "Error: %v\n", err)
		os.Exit(1)
	}
}
