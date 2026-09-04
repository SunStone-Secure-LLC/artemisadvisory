#!/usr/bin/env python3
"""Watch the FedRAMP schemas CHANGELOG for entries that affect a schema we consume.

Fetches https://github.com/FedRAMP/schemas/blob/main/CHANGELOG.md, parses its
per-release headings, keeps the entries whose schema file matches a glob
(default: fedramp-advisor-information-schema*), and files one GitHub issue per
new entry in this repository. Each issue carries a hidden marker comment keyed
on ``<schema file>@<version>``; on later runs an entry whose marker already
appears in an existing issue (open or closed) is skipped, so the check is
idempotent and safe to run daily.

Requires the ``gh`` CLI, authenticated with a token that can read and create
issues in the target repository (GITHUB_TOKEN inside Actions).
"""

from __future__ import annotations

import argparse
import datetime as dt
import fnmatch
import json
import os
import re
import subprocess
import sys
import urllib.request
from dataclasses import dataclass
from pathlib import Path

CHANGELOG_RAW_URL = "https://raw.githubusercontent.com/FedRAMP/schemas/main/CHANGELOG.md"
CHANGELOG_HTML_URL = "https://github.com/FedRAMP/schemas/blob/main/CHANGELOG.md"
SCHEMA_REPO_BLOB_URL = "https://github.com/FedRAMP/schemas/blob/main/{file}"
SCHEMA_PUBLISHED_URL = "https://www.fedramp.gov/schemas/{file}"

MARKER_PREFIX = "fedramp-schema-watch:"
MARKER_RE = re.compile(r"<!--\s*fedramp-schema-watch:\s*(?P<key>\S+)\s*-->")

# "## 2026-08-11 — fedramp-advisor-information-schema-2026-06-24.json → 1.0.1 (patch)"
HEADING_RE = re.compile(
    r"^##\s+(?P<date>\d{4}-\d{2}-\d{2})\s+[—–-]+\s+"
    r"(?P<file>\S+\.json)\s+(?:→|->)\s+(?P<version>\S+)\s+\((?P<bump>[a-z]+)\)\s*$"
)


@dataclass
class ChangelogEntry:
    date: dt.date
    file: str
    version: str
    bump: str
    heading: str
    body: str

    @property
    def key(self) -> str:
        return f"{self.file}@{self.version}"

    @property
    def marker(self) -> str:
        return f"<!-- {MARKER_PREFIX} {self.key} -->"


def fetch_changelog(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "fedramp-schema-watch"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read().decode("utf-8")


def parse_changelog(markdown: str) -> list[ChangelogEntry]:
    entries: list[ChangelogEntry] = []
    current: ChangelogEntry | None = None
    body_lines: list[str] = []

    def flush() -> None:
        if current is not None:
            current.body = "\n".join(body_lines).strip()
            entries.append(current)

    for line in markdown.splitlines():
        if line.startswith("## "):
            flush()
            body_lines = []
            match = HEADING_RE.match(line)
            if match:
                current = ChangelogEntry(
                    date=dt.date.fromisoformat(match.group("date")),
                    file=match.group("file"),
                    version=match.group("version"),
                    bump=match.group("bump"),
                    heading=line[3:].strip(),
                    body="",
                )
            else:
                # Non-release headings (e.g. "Baseline frozen") are expected.
                # A heading that names a schema file but does not parse means
                # the format changed; surface it rather than dropping a change.
                if ".json" in line:
                    print(f"::warning::Unparsed CHANGELOG heading: {line}", file=sys.stderr)
                current = None
            continue
        if current is not None:
            body_lines.append(line)
    flush()
    return entries


def select_entries(
    entries: list[ChangelogEntry], pattern: str, since: dt.date | None
) -> list[ChangelogEntry]:
    selected = [e for e in entries if fnmatch.fnmatch(e.file, pattern)]
    if since is not None:
        selected = [e for e in selected if e.date >= since]
    # Oldest first so issue numbers ascend chronologically.
    return sorted(selected, key=lambda e: (e.date, e.version))


def run_gh(args: list[str], repo: str) -> str:
    command = ["gh", *args, "--repo", repo]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"gh {' '.join(args)} failed ({result.returncode}):\n{result.stderr.strip()}"
        )
    return result.stdout


def existing_keys(repo: str, label: str) -> set[str]:
    output = run_gh(
        [
            "issue",
            "list",
            "--label",
            label,
            "--state",
            "all",
            "--limit",
            "500",
            "--json",
            "body",
        ],
        repo,
    )
    keys: set[str] = set()
    for issue in json.loads(output or "[]"):
        for match in MARKER_RE.finditer(issue.get("body") or ""):
            keys.add(match.group("key"))
    return keys


def ensure_label(repo: str, label: str) -> None:
    run_gh(
        [
            "label",
            "create",
            label,
            "--description",
            "Automated notice of a FedRAMP schema CHANGELOG entry that affects this repo",
            "--color",
            "D93F0B",
            "--force",
        ],
        repo,
    )


def issue_title(entry: ChangelogEntry) -> str:
    return f"FedRAMP schema change: {entry.file} → {entry.version} ({entry.bump}) [{entry.date}]"


def issue_body(entry: ChangelogEntry, publish_workflow: str) -> str:
    breaking = ""
    if entry.bump == "major":
        breaking = (
            "> **Warning:** this is a major version bump. Documents published against the "
            "previous version are likely invalid until they are updated.\n\n"
        )
    quoted_body = "\n".join(f"> {line}" if line else ">" for line in entry.body.splitlines())
    return f"""{entry.marker}
The FedRAMP schemas CHANGELOG recorded a new release of a schema this repository publishes against.

{breaking}## CHANGELOG entry

> ### {entry.heading}
>
{quoted_body}

Source: [CHANGELOG.md]({CHANGELOG_HTML_URL})

## Schema

- Repository copy: {SCHEMA_REPO_BLOB_URL.format(file=entry.file)}
- Published copy: {SCHEMA_PUBLISHED_URL.format(file=entry.file)}

## Next steps

1. Read the entry above and decide whether `README.md` metadata or `scripts/build_fedramp_advisor_information.py` need to change.
2. Re-run the **{publish_workflow}** workflow (workflow_dispatch). It validates the generated JSON against the live schema and fails if the new version rejects it.
3. Close this issue once the published JSON validates against `{entry.version}`.

_Filed automatically by the FedRAMP schema CHANGELOG watch workflow._
"""


def create_issue(
    repo: str, entry: ChangelogEntry, label: str, assignee: str, publish_workflow: str
) -> str:
    args = [
        "issue",
        "create",
        "--title",
        issue_title(entry),
        "--body",
        issue_body(entry, publish_workflow),
        "--label",
        label,
    ]
    if assignee:
        args += ["--assignee", assignee]
    return run_gh(args, repo).strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo",
        default=os.environ.get("GITHUB_REPOSITORY", ""),
        help="owner/name of the repository to file issues in",
    )
    parser.add_argument(
        "--pattern",
        default=os.environ.get("SCHEMA_FILE_PATTERN", "fedramp-advisor-information-schema*"),
        help="fnmatch glob applied to the schema file name in each CHANGELOG heading",
    )
    parser.add_argument(
        "--since",
        default=os.environ.get("WATCH_SINCE") or None,
        help="ignore CHANGELOG entries dated before this ISO date (baseline)",
    )
    parser.add_argument("--label", default=os.environ.get("ISSUE_LABEL", "fedramp-schema-watch"))
    parser.add_argument("--assignee", default=os.environ.get("ISSUE_ASSIGNEE", ""))
    parser.add_argument(
        "--publish-workflow",
        default=os.environ.get("PUBLISH_WORKFLOW_NAME", "Publish FedRAMP Advisor Information"),
    )
    parser.add_argument(
        "--changelog",
        type=Path,
        help="read the CHANGELOG from a local file instead of fetching it (testing)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="report what would be filed without creating labels or issues",
    )
    args = parser.parse_args()

    if not args.repo:
        parser.error("--repo is required (or set GITHUB_REPOSITORY)")
    since = dt.date.fromisoformat(args.since) if args.since else None

    markdown = (
        args.changelog.read_text(encoding="utf-8")
        if args.changelog
        else fetch_changelog(CHANGELOG_RAW_URL)
    )
    entries = parse_changelog(markdown)
    matching = select_entries(entries, args.pattern, since)
    print(
        f"Parsed {len(entries)} CHANGELOG entries; {len(matching)} match "
        f"'{args.pattern}'" + (f" on/after {since}" if since else "")
    )

    known = existing_keys(args.repo, args.label)
    new_entries = [e for e in matching if e.key not in known]
    for entry in matching:
        status = "new" if entry in new_entries else "already filed"
        print(f"  - {entry.key} ({entry.date}, {entry.bump}): {status}")

    if not new_entries:
        print("No new CHANGELOG entries to file.")
        return 0

    if args.dry_run:
        print(f"Dry run: would file {len(new_entries)} issue(s).")
        for entry in new_entries:
            print("\n" + "=" * 72)
            print(issue_title(entry))
            print("-" * 72)
            print(issue_body(entry, args.publish_workflow))
        return 0

    ensure_label(args.repo, args.label)
    for entry in new_entries:
        url = create_issue(args.repo, entry, args.label, args.assignee, args.publish_workflow)
        print(f"Filed {url} for {entry.key}")

    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as summary:
            summary.write(
                f"Filed {len(new_entries)} FedRAMP schema change issue(s): "
                + ", ".join(e.key for e in new_entries)
                + "\n"
            )
    return 0


if __name__ == "__main__":
    sys.exit(main())
