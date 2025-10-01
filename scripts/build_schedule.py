import os
import re
import sys
import tempfile
from datetime import datetime, timezone
from typing import Optional

from github_utils import get_repo_owner_and_name_or_default, list_issues

# Regex to parse issue body
DATE_RE = re.compile(r"### Date\s*\n\s*(.*)")
TIME_RE = re.compile(r"### Time\s*\n\s*(.*)")
DESCRIPTION_RE = re.compile(r"### Description\s*\n\s*(.*)", re.DOTALL)

def parse_issue_body(body: str) -> tuple[str, str, str]:
    """Parses the body of an event issue."""
    if not body:
        return "N/A", "N/A", "N/A"

    date_match = DATE_RE.search(body)
    time_match = TIME_RE.search(body)
    description_match = DESCRIPTION_RE.search(body)

    date = date_match.group(1).strip() if date_match else "N/A"
    time = time_match.group(1).strip() if time_match else "N/A"
    description = description_match.group(1).strip() if description_match else "No description provided."

    return date, time, description

def parse_datetime(date_str: str, time_str: str) -> Optional[datetime]:
    """Parses date and time strings into a datetime object."""
    if not date_str or not time_str or date_str == "N/A" or time_str == "N/A":
        return None
    try:
        return datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %I:%M %p")
    except ValueError:
        try:
            return datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        except ValueError:
            return None

def description_to_html(description: str) -> str:
    """Converts a markdown-like description to HTML."""
    lines = description.strip().split('\n')
    html_lines = []
    in_list = False
    for line in lines:
        line = line.strip()
        if line.startswith("- "):
            if not in_list:
                html_lines.append("<ul>")
                in_list = True
            # Linkify @mentions to player profiles
            line_content = re.sub(r'@([\w-]+)', r'<a href="player_profile_\1.html">@\1</a>', line[2:])
            html_lines.append(f"<li>{line_content}</li>")
        else:
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f"<p>{line}</p>")
    if in_list:
        html_lines.append("</ul>")
    return "\n".join(html_lines)

def build_schedule_page(output_dir: Optional[str] = None):
    """Generates a static HTML page with a schedule of upcoming events."""
    owner, repo = get_repo_owner_and_name_or_default()

    issues = []
    # Only fetch issues if a token is available, otherwise build an empty page.
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_BEARER_TOKEN")
    if token:
        try:
            issues = list_issues(owner, repo, labels="event", token=token)
        except Exception as e:
            print(f"Warning: Could not fetch GitHub issues: {e}", file=sys.stderr)
            issues = []
    else:
        print("Warning: GITHUB_TOKEN not set. Building schedule page without issues.", file=sys.stderr)

    parsed_events = []
    for event in issues:
        date_str, time_str, description = parse_issue_body(event.get("body"))
        event_dt = parse_datetime(date_str, time_str)

        # Skip events that are in the past
        if event_dt and event_dt.date() < datetime.now().date():
            continue

        parsed_events.append({
            "data": event,
            "datetime": event_dt,
            "date_str": date_str,
            "time_str": time_str,
            "description": description,
        })

    # Sort events: those with valid datetimes first, then by date, then by issue number
    parsed_events.sort(key=lambda x: (x["datetime"] is None, x["datetime"], x["data"]["number"]))

    table_rows = ""
    for event in parsed_events:
        issue_data = event["data"]
        issue_link = f'<a href="{issue_data["html_url"]}" target="_blank">#{issue_data["number"]}</a>'
        description_html = description_to_html(event["description"])

        table_rows += f"""
        <tr>
            <td>{event["date_str"]}</td>
            <td>{event["time_str"]}</td>
            <td>{issue_data["title"]}</td>
            <td>{description_html}</td>
            <td>{issue_link}</td>
        </tr>
        """

    html_table = f"""
    <div class="table-responsive">
        <table class="table table-striped table-hover">
            <thead>
                <tr>
                    <th>Date</th>
                    <th>Time</th>
                    <th>Event</th>
                    <th>Description/Attendees</th>
                    <th>Issue</th>
                </tr>
            </thead>
            <tbody>
                {table_rows if parsed_events else '<tr><td colspan="5" class="text-center">No upcoming events found.</td></tr>'}
            </tbody>
        </table>
    </div>
    """

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    repo_url = f"https://github.com/{owner}/{repo}"

    html_template = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Event Schedule</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body {{ padding: 2rem; }}
            .container {{ max-width: 1000px; }}
            h1 {{ margin-bottom: 1.5rem; text-align: center; }}
            .footer {{
                margin-top: 2rem;
                padding-top: 2rem;
                border-top: 1px solid #dee2e6;
                font-size: 0.9rem;
                color: #6c757d;
                text-align: center;
            }}
            .table-responsive {{
                border: 1px solid #dee2e6;
                border-radius: 0.375rem;
            }}
            ul {{ margin-bottom: 0; padding-left: 1.2rem; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🗓️ Event Schedule</h1>
            {html_table}
            <div class="footer">
                <p>Last updated: {timestamp}</p>
                <p>
                    <a href="index.html">Leaderboards</a> |
                    <a href="history.html">Match History</a> |
                    <a href="{repo_url}">GitHub Repository</a>
                </p>
            </div>
        </div>
    </body>
    </html>
    """

    if output_dir:
        output_file = os.path.join(output_dir, "schedule.html")
        with open(output_file, "w") as f:
            f.write(html_template)
        return None, output_file

    temp_dir = tempfile.mkdtemp(prefix="tennis_schedule_")
    output_file = os.path.join(temp_dir, "schedule.html")
    with open(output_file, "w") as f:
        f.write(html_template)
    return temp_dir, output_file

if __name__ == "__main__":
    temp_dir, _ = build_schedule_page()
    if temp_dir and os.environ.get("GITHUB_ACTIONS") == "true":
        with open(os.environ.get("GITHUB_OUTPUT", "/dev/null"), "a") as f:
            f.write(f"schedule_temp_dir={temp_dir}")