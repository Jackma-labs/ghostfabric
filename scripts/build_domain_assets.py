#!/usr/bin/env python3
"""
Generic script for turning markdown docs into structured expert assets.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def clean_line(line: str) -> str:
    return re.sub(r"\s+", " ", line.replace("\u200b", "")).strip()


def extract_code_blocks(text: str) -> list[dict[str, str]]:
    blocks = []
    for match in re.finditer(r"```(\w+)?\n(.*?)```", text, flags=re.S):
        blocks.append({"language": (match.group(1) or "text").strip(), "content": match.group(2).strip()})
    return blocks


def build_record(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    title_match = re.search(r"^#\s+(.+)$", text, flags=re.M)
    title = clean_line(title_match.group(1)) if title_match else path.stem
    excerpt = []
    for line in text.splitlines():
        normalized = clean_line(line)
        if normalized:
            excerpt.append(normalized)
        if len(excerpt) >= 16:
            break
    return {
        "title": title,
        "path": str(path),
        "answer_excerpt": "\n".join(excerpt),
        "code_blocks": extract_code_blocks(text),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    root = Path(args.input)
    records = [build_record(path) for path in sorted(root.rglob("*.md"))]
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"documents": records}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {output}")
    print(f"documents={len(records)}")


if __name__ == "__main__":
    main()
