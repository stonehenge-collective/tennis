#!/usr/bin/env python3
"""
Script to check if branch protection is properly configured for tennis match approvals.
"""

import os
import sys
import requests
from typing import Dict, Any, Optional


def get_github_token() -> Optional[str]:
    """Get GitHub token from environment variables."""
    return os.environ.get('GITHUB_TOKEN') or os.environ.get('GH_TOKEN')


def check_branch_protection(owner: str, repo: str, branch: str = 'main') -> Dict[str, Any]:
    """Check branch protection rules for the specified repository and branch."""
    token = get_github_token()
    if not token:
        return {
            'error': 'GitHub token not found. Set GITHUB_TOKEN or GH_TOKEN environment variable.',
            'success': False
        }

    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }

    url = f'https://api.github.com/repos/{owner}/{repo}/branches/{branch}/protection'

    try:
        response = requests.get(url, headers=headers)

        if response.status_code == 404:
            return {
                'error': f'Branch protection not configured for {branch} branch',
                'success': False,
                'configured': False
            }
        elif response.status_code == 403:
            return {
                'error': 'Insufficient permissions to check branch protection',
                'success': False
            }
        elif response.status_code != 200:
            return {
                'error': f'API request failed with status {response.status_code}: {response.text}',
                'success': False
            }

        protection_data = response.json()
        return analyze_protection_rules(protection_data)

    except requests.RequestException as e:
        return {
            'error': f'Request failed: {str(e)}',
            'success': False
        }


def analyze_protection_rules(protection_data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze the branch protection rules and provide recommendations."""
    result = {
        'success': True,
        'configured': True,
        'recommendations': [],
        'status': 'good'
    }

    # Check required pull request reviews
    required_reviews = protection_data.get('required_pull_request_reviews')
    if not required_reviews:
        result['recommendations'].append('❌ Pull request reviews are not required')
        result['status'] = 'needs_improvement'
    else:
        required_count = required_reviews.get('required_approving_review_count', 0)
        if required_count < 2:
            result['recommendations'].append(
                f'⚠️  Only {required_count} approval(s) required. For tennis matches, '
                'consider setting to 2 (one for each player)'
            )
            result['status'] = 'needs_improvement'
        else:
            result['recommendations'].append(
                f'✅ Requires {required_count} approvals - perfect for tennis matches!'
            )

        if required_reviews.get('dismiss_stale_reviews'):
            result['recommendations'].append('✅ Stale reviews are dismissed when new commits are pushed')
        else:
            result['recommendations'].append(
                '⚠️  Consider enabling "Dismiss stale PR approvals when new commits are pushed"'
            )

    # Check required status checks
    required_status_checks = protection_data.get('required_status_checks')
    if required_status_checks:
        contexts = required_status_checks.get('contexts', [])
        if 'tennis/match-approval' in contexts:
            result['recommendations'].append('✅ Tennis match approval status check is required')
        else:
            result['recommendations'].append(
                '💡 Consider adding "tennis/match-approval" as a required status check'
            )
    else:
        result['recommendations'].append(
            '💡 No required status checks configured. The tennis/match-approval check '
            'can provide additional validation'
        )

    # Check restrictions
    restrictions = protection_data.get('restrictions')
    if restrictions:
        result['recommendations'].append('ℹ️  Push restrictions are configured')

    # Check enforce admins
    enforce_admins = protection_data.get('enforce_admins', {}).get('enabled', False)
    if enforce_admins:
        result['recommendations'].append('✅ Rules apply to administrators')
    else:
        result['recommendations'].append(
            '💡 Consider enabling "Include administrators" to ensure even admins '
            'follow the approval process'
        )

    return result


def print_results(result: Dict[str, Any], owner: str, repo: str, branch: str):
    """Print the branch protection analysis results."""
    print(f"\n🎾 Tennis Match Branch Protection Analysis")
    print(f"Repository: {owner}/{repo}")
    print(f"Branch: {branch}")
    print("=" * 50)

    if not result['success']:
        print(f"❌ Error: {result['error']}")
        return

    if not result.get('configured', True):
        print("❌ Branch protection is not configured!")
        print("\n📋 Setup Instructions:")
        print("1. Go to repository Settings → Branches")
        print("2. Click 'Add branch protection rule'")
        print(f"3. Set branch name pattern to '{branch}'")
        print("4. Enable these settings:")
        print("   ✅ Require a pull request before merging")
        print("   ✅ Require approvals (set to 2)")
        print("   ✅ Dismiss stale PR approvals when new commits are pushed")
        print("   ✅ Require status checks to pass before merging")
        print("   ✅ Require branches to be up to date before merging")
        return

    print(f"✅ Branch protection is configured!")

    status_emoji = {
        'good': '🟢',
        'needs_improvement': '🟡',
        'poor': '🔴'
    }

    print(f"\nStatus: {status_emoji.get(result['status'], '❓')} {result['status'].replace('_', ' ').title()}")
    print("\n📋 Analysis Results:")

    for recommendation in result['recommendations']:
        print(f"  {recommendation}")

    if result['status'] != 'good':
        print(f"\n💡 To improve your setup:")
        print(f"   1. Go to https://github.com/{owner}/{repo}/settings/branches")
        print(f"   2. Edit the protection rule for the '{branch}' branch")
        print(f"   3. Apply the recommendations above")


def main():
    """Main function to run the branch protection check."""
    if len(sys.argv) < 3:
        print("Usage: python check_branch_protection.py <owner> <repo> [branch]")
        print("Example: python check_branch_protection.py myorg tennis-league main")
        sys.exit(1)

    owner = sys.argv[1]
    repo = sys.argv[2]
    branch = sys.argv[3] if len(sys.argv) > 3 else 'main'

    result = check_branch_protection(owner, repo, branch)
    print_results(result, owner, repo, branch)

    if not result['success'] or result['status'] != 'good':
        sys.exit(1)


if __name__ == '__main__':
    main()
