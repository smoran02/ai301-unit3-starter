#!/usr/bin/env python3
"""Mirror every packages/*.md bundle as packages/*.json.

The markdown bundles are the canonical snapshots (captured on the date
stamped in each file); this script derives a structured JSON view of the
same frozen content so the packages can be read programmatically. It
never touches the network: the live issues have moved on since capture,
and re-fetching would desynchronize the snapshots from the gold labels.

Usage: python3 packages_to_json.py   (from this directory; rewrites *.json)
"""

import json
import re
from pathlib import Path

PACKAGES_DIR = Path(__file__).parent / "packages"

META_RE = re.compile(r"^- (source|captured|calibration): (.+)$")
TITLE_RE = re.compile(r"^### (.+) \(#(\d+)\)$")
OPENED_RE = re.compile(
    r"^opened by (\S+) \((\w+)\) on (\d{4}-\d{2}-\d{2}), "
    r"state (\w+), labels: (.+)$"
)
HIGHLIGHTS_HDR_RE = re.compile(r"^## Thread highlights \((\d+) comments? total\)$")
HIGHLIGHT_RE = re.compile(r"^- (\d{4}-\d{2}-\d{2}) (\S+) \((\w+)\): (.+)$")

SECTION_STARTS = {
    "## Repo facts": "repo_facts",
    "## Issue": "issue",
    "## Repro evidence": "repro_evidence",
    "## Candidate plan comment": "plan_comment",
    "## Candidate plan": "plan",
}


def split_sections(lines):
    """Group lines per structural heading, fence-aware."""
    sections = {"meta": [], "repo_facts": [], "issue": [],
                "highlights": [], "repro_evidence": [], "plan": [],
                "plan_comment": []}
    current = "meta"
    fenced = False
    for line in lines:
        if line.startswith("```"):
            fenced = not fenced
            sections[current].append(line)
            continue
        if line.startswith("## "):
            # A quoted excerpt can end with a fence that its source closed
            # implicitly; a structural heading therefore closes any fence
            # still open rather than being swallowed by it.
            fenced = False
        if not fenced:
            m = HIGHLIGHTS_HDR_RE.match(line)
            if m:
                sections["highlights_header"] = line
                current = "highlights"
                continue
            # Longest prefix wins: "## Candidate plan comment" must not be
            # swallowed by "## Candidate plan".
            hit = max((k for k in SECTION_STARTS if line.startswith(k)),
                      key=len, default=None)
            if hit:
                current = SECTION_STARTS[hit]
                continue
        sections[current].append(line)
    return sections


def parse_bundle(path):
    lines = path.read_text().splitlines()
    out = {"id": path.stem, "calibration": False}

    sections = split_sections(lines)

    for line in sections["meta"]:
        m = META_RE.match(line)
        if m:
            key, val = m.groups()
            out[key] = True if val == "true" else \
                (False if val == "false" else val)

    out["repo_facts"] = {
        "raw_markdown": "\n".join(sections["repo_facts"]).strip()}

    issue = {}
    body_start = 0
    for i, line in enumerate(sections["issue"]):
        m = TITLE_RE.match(line)
        if m and "title" not in issue:
            issue["title"], issue["number"] = m.group(1), int(m.group(2))
            continue
        m = OPENED_RE.match(line)
        if m:
            issue["author"], issue["author_association"] = \
                m.group(1), m.group(2)
            issue["opened"], issue["state"] = m.group(3), m.group(4)
            labels = m.group(5).strip()
            issue["labels"] = [] if labels == "none" else labels.split(", ")
            body_start = i + 1
            break
    issue["body_markdown"] = "\n".join(sections["issue"][body_start:]).strip()
    out["issue"] = issue

    hdr = sections.get("highlights_header")
    highlights = []
    if hdr:
        out["comments_total"] = int(HIGHLIGHTS_HDR_RE.match(hdr).group(1))
        for line in sections["highlights"]:
            m = HIGHLIGHT_RE.match(line)
            if m:
                highlights.append({
                    "date": m.group(1),
                    "author": m.group(2),
                    "author_association": m.group(3),
                    "summary_markdown": m.group(4),
                })
    else:
        out["comments_total"] = 0
    out["thread_highlights"] = highlights

    out["repro_evidence_markdown"] = \
        "\n".join(sections["repro_evidence"]).strip()
    out["plan_markdown"] = "\n".join(sections["plan"]).strip()
    out["plan_comment_markdown"] = \
        "\n".join(sections["plan_comment"]).strip()
    return out


def main():
    bundles = sorted(PACKAGES_DIR.glob("*.md"))
    for path in bundles:
        data = parse_bundle(path)
        dest = path.with_suffix(".json")
        dest.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
        print(
            f"{dest.name}: #{data['issue'].get('number', '?')} "
            f"{data['comments_total']} comments "
            f"({len(data['thread_highlights'])} highlighted)"
        )
    print(f"{len(bundles)} bundles mirrored")


if __name__ == "__main__":
    main()
