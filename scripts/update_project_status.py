#!/usr/bin/env python3
"""Update the profile README with health signals for original public repos."""

from datetime import datetime, timezone
from os import environ
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import json
import re


OWNER = "Sharon-ctl"
PROFILE_REPOSITORY = OWNER
README = "README.md"
START = "<!-- PROJECT_STATUS:START -->"
END = "<!-- PROJECT_STATUS:END -->"
API = "https://api.github.com"


def github_get(path: str) -> dict | list:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "Sharon-profile-project-monitor",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(f"{API}{path}", headers=headers)
    with urlopen(request, timeout=20) as response:
        return json.load(response)


def markdown_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\r", " ").replace("\n", " ")


def workflow_for(repo: dict) -> tuple[str, dict | None, dict | None]:
    full_name = repo["full_name"]
    workflows = github_get(f"/repos/{full_name}/actions/workflows?per_page=100")["workflows"]
    active = [workflow for workflow in workflows if workflow.get("state") == "active"]
    if not active:
        return "No CI configured", None, None

    priorities = {"ci": 0, "test": 1, "tests": 1, "build": 2, "codeql advanced": 3}
    active.sort(key=lambda workflow: priorities.get(workflow["name"].strip().lower(), 4))
    workflow = active[0]
    params = urlencode({"branch": repo["default_branch"], "per_page": 1})
    runs = github_get(f"/repos/{full_name}/actions/workflows/{workflow['id']}/runs?{params}")["workflow_runs"]
    return workflow["name"], workflow, (runs[0] if runs else None)


def ci_label(workflow_name: str, run: dict | None) -> str:
    if workflow_name == "No CI configured":
        return "No CI configured"
    if run is None:
        return f"{workflow_name}: awaiting first run"

    state = run.get("status")
    conclusion = run.get("conclusion")
    if state != "completed":
        label = "Running"
    elif conclusion == "success":
        label = "Passing"
    elif conclusion == "failure":
        label = "Failing"
    elif conclusion == "cancelled":
        label = "Cancelled"
    elif conclusion:
        label = conclusion.replace("_", " ").title()
    else:
        label = "Unknown"

    return f"[{label} ({markdown_cell(workflow_name)})]({run['html_url']})"


def utc_date(value: str) -> str:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    return parsed.strftime("%Y-%m-%d")


def generate_table() -> str:
    repositories = github_get(f"/users/{OWNER}/repos?{urlencode({'type': 'owner', 'per_page': 100, 'sort': 'updated'})}")
    originals = [
        repo for repo in repositories
        if repo.get("owner", {}).get("login", "").lower() == OWNER.lower()
        and not repo.get("fork")
        and not repo.get("private")
        and not repo.get("archived")
        and repo.get("name") != PROFILE_REPOSITORY
    ]
    originals.sort(key=lambda repo: repo["name"].lower())

    rows = [
        "| Project | CI / checks | Last push (UTC) | Open issues / PRs |",
        "| --- | --- | --- | ---: |",
    ]
    for repo in originals:
        workflow_name, _, run = workflow_for(repo)
        project = markdown_cell(repo["name"])
        project_link = f"[{project}]({repo['html_url']})"
        rows.append(
            f"| {project_link} | {ci_label(workflow_name, run)} | "
            f"{utc_date(repo['pushed_at'])} | {repo.get('open_issues_count', 0)} |"
        )

    if not originals:
        rows.append("| No original public repositories found | -- | -- | -- |")
    return "\n".join(rows)


def main() -> None:
    readme = open(README, encoding="utf-8").read()
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.DOTALL)
    replacement = f"{START}\n{generate_table()}\n{END}"
    updated, count = pattern.subn(lambda _: replacement, readme, count=1)
    if count != 1:
        raise RuntimeError("Could not find exactly one project status marker pair in README.md")
    with open(README, "w", encoding="utf-8", newline="\n") as output:
        output.write(updated)


if __name__ == "__main__":
    main()
