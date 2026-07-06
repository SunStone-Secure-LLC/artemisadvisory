#!/usr/bin/env python3
"""Build FedRAMP Advisor Information JSON from README.md."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


METADATA_RE = re.compile(
    r"<!--\s*20x-MKT-CAS-WEB-(?P<key>[A-Za-z]+):\s*(?P<value>.*?)\s*-->",
    re.DOTALL,
)
REQUIRED_METADATA_FIELDS = (
    "serviceDescription",
    "contactInformation",
    "servicesOffered",
)


def normalize_space(value: str) -> str:
    return " ".join(value.split())


def quote_unquoted_object_keys(value: str) -> str:
    result: list[str] = []
    index = 0
    in_string = False
    escaped = False

    while index < len(value):
        char = value[index]

        if in_string:
            result.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            index += 1
            continue

        if char == '"':
            in_string = True
            result.append(char)
            index += 1
            continue

        if char not in "{,":
            result.append(char)
            index += 1
            continue

        result.append(char)
        index += 1

        while index < len(value) and value[index].isspace():
            result.append(value[index])
            index += 1

        key_start = index
        if index < len(value) and (value[index].isalpha() or value[index] == "_"):
            index += 1
            while index < len(value) and (
                value[index].isalnum() or value[index] == "_"
            ):
                index += 1

            lookahead = index
            while lookahead < len(value) and value[lookahead].isspace():
                lookahead += 1

            if lookahead < len(value) and value[lookahead] == ":":
                result.append(f'"{value[key_start:index]}"')
                result.extend(value[index:lookahead])
                result.append(":")
                index = lookahead + 1
                continue

        result.extend(value[key_start:index])

    return "".join(result)


def parse_metadata_value(key: str, raw_value: str) -> Any:
    normalized_value = quote_unquoted_object_keys(raw_value.strip())
    try:
        return json.loads(normalized_value)
    except json.JSONDecodeError as error:
        raise ValueError(f"README.md metadata field '{key}' is not valid JSON") from error


def read_metadata(markdown: str) -> dict[str, Any]:
    metadata: dict[str, Any] = {}

    for match in METADATA_RE.finditer(markdown):
        key = match.group("key")
        if key in metadata:
            raise ValueError(f"README.md contains duplicate metadata field: {key}")
        metadata[key] = parse_metadata_value(key, match.group("value"))

    missing_fields = [key for key in REQUIRED_METADATA_FIELDS if key not in metadata]
    if missing_fields:
        raise ValueError(
            "README.md is missing required metadata field(s): "
            + ", ".join(missing_fields)
        )

    return metadata


def require_string(metadata: dict[str, Any], key: str) -> str:
    value = metadata.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"README.md metadata field '{key}' must be a non-empty string")
    return normalize_space(value)


def require_string_list(metadata: dict[str, Any], key: str) -> list[str]:
    value = metadata.get(key)
    if not isinstance(value, list) or not value:
        raise ValueError(
            f"README.md metadata field '{key}' must be a non-empty string array"
        )

    strings: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            raise ValueError(
                f"README.md metadata field '{key}' item {index} must be "
                "a non-empty string"
            )
        strings.append(normalize_space(item))

    return strings


def normalize_service_description(value: str) -> str:
    return normalize_space(" ".join(part.strip() for part in value.split("|")))


def parse_services_offered(metadata: dict[str, Any]) -> list[dict[str, str]]:
    value = metadata.get("servicesOffered")
    if not isinstance(value, list) or not value:
        raise ValueError(
            "README.md metadata field 'servicesOffered' must be a non-empty array"
        )

    services: list[dict[str, str]] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise ValueError(
                f"README.md metadata field 'servicesOffered' item {index} "
                "must be an object"
            )

        unexpected_keys = set(item) - {
            "serviceName",
            "description",
            "serviceDescription",
        }
        if unexpected_keys:
            raise ValueError(
                f"README.md metadata field 'servicesOffered' item {index} "
                f"has unexpected key(s): {', '.join(sorted(unexpected_keys))}"
            )

        service_name = item.get("serviceName")
        if not isinstance(service_name, str) or not service_name.strip():
            raise ValueError(
                f"README.md metadata field 'servicesOffered' item {index} "
                "must include a non-empty serviceName"
            )

        service: dict[str, str] = {"serviceName": normalize_space(service_name)}
        service_description = item.get("serviceDescription", item.get("description"))
        if service_description is not None:
            if (
                not isinstance(service_description, str)
                or not service_description.strip()
            ):
                raise ValueError(
                    f"README.md metadata field 'servicesOffered' item {index} "
                    "description must be a non-empty string"
                )
            service["serviceDescription"] = normalize_service_description(
                service_description
            )

        services.append(service)

    return services


def build_advisor_information(readme_path: Path) -> dict[str, object]:
    metadata = read_metadata(readme_path.read_text(encoding="utf-8"))

    document: dict[str, object] = {
        "serviceDescription": require_string(metadata, "serviceDescription"),
        "contactInformation": require_string_list(metadata, "contactInformation"),
        "servicesOffered": parse_services_offered(metadata),
    }

    if "customerReferences" in metadata:
        document["customerReferences"] = require_string_list(
            metadata,
            "customerReferences",
        )

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
