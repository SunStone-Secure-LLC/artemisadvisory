#!/usr/bin/env python3
"""Build FedRAMP Advisor Information JSON from README.md."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
HEADING_RE = re.compile(r"^##\s+(?P<title>.+?)\s*$", re.MULTILINE)

SERVICE_DESCRIPTION_SECTION = "General description of the consulting or advisory service"
CONTACT_INFORMATION_SECTION = "Contact information"
SERVICES_OFFERED_SECTION = "Types of consulting or advisory services offered"
CUSTOMER_REFERENCES_SECTION = (
    "Optional: Positive attestations from customers or customer references"
)


def normalize_space(value: str) -> str:
    return " ".join(value.split())


def read_sections(markdown: str) -> dict[str, str]:
    visible_markdown = COMMENT_RE.sub("", markdown)
    matches = list(HEADING_RE.finditer(visible_markdown))
    sections: dict[str, str] = {}

    for index, match in enumerate(matches):
        start = match.end()
        end = (
            matches[index + 1].start()
            if index + 1 < len(matches)
            else len(visible_markdown)
        )
        sections[match.group("title").strip()] = visible_markdown[start:end].strip()

    return sections


def require_section(sections: dict[str, str], title: str) -> str:
    section = sections.get(title, "").strip()
    if not section:
        raise ValueError(f"README.md is missing required section: {title}")
    return section


def parse_contact_information(section: str) -> list[str]:
    contacts = [normalize_space(line) for line in section.splitlines() if line.strip()]
    if not contacts:
        raise ValueError("README.md contact information section did not contain any contacts")
    return contacts


def parse_services_offered(section: str) -> list[dict[str, str]]:
    services: list[dict[str, str]] = []
    service_name: str | None = None
    bullets: list[str] = []

    def append_current_service() -> None:
        if service_name is None:
            return
        if not bullets:
            raise ValueError(f"Service '{service_name}' does not include a description")
        services.append(
            {
                "serviceName": service_name,
                "serviceDescription": " ".join(bullets),
            }
        )

    for raw_line in section.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        if line.endswith(":") and not line.startswith("-"):
            append_current_service()
            service_name = line[:-1].strip()
            bullets = []
            continue

        if service_name is None:
            raise ValueError(f"Unexpected text before any service is defined: {line}")

        if line.startswith("-"):
            bullets.append(normalize_space(line[1:]))
            continue

        if bullets:
            bullets[-1] = normalize_space(f"{bullets[-1]} {line}")
        else:
            raise ValueError(
                f"Unexpected text before first bullet point in service '{service_name}': "
                f"{line}"
            )

    append_current_service()

    if not services:
        raise ValueError("README.md services offered section did not contain any services")
    return services


def build_advisor_information(readme_path: Path) -> dict[str, object]:
    sections = read_sections(readme_path.read_text(encoding="utf-8"))

    document: dict[str, object] = {
        "serviceDescription": normalize_space(
            require_section(sections, SERVICE_DESCRIPTION_SECTION)
        ),
        "contactInformation": parse_contact_information(
            require_section(sections, CONTACT_INFORMATION_SECTION)
        ),
        "servicesOffered": parse_services_offered(
            require_section(sections, SERVICES_OFFERED_SECTION)
        ),
    }

    customer_references = normalize_space(sections.get(CUSTOMER_REFERENCES_SECTION, ""))
    if customer_references:
        document["customerReferences"] = [customer_references]

    return document


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--readme", default="README.md", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    advisor_information = build_advisor_information(args.readme)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(advisor_information, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
