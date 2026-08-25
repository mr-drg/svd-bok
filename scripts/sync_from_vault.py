#!/usr/bin/env python3
"""
Sync approved candidates from Vault_skynet/20_Cards/20.7_Publish into this
Quartz site's content/ folder.

Folder location is the primary status signal: only files physically inside
20.7_Publish/approved/ or 20.7_Publish/published/ are scanned at all —
20.7_Publish/candidate/ is never touched. The frontmatter publish_status
field is checked too and must agree with the folder; a mismatch is treated
as a stop signal rather than guessed at. This is the last automated gate
before content becomes public — it does not replace human judgement, it
backs it up:

- files tagged #конфиденциально or with category: Личное are never copied,
  even if publish_status says approved (defensive double-check of dlp-guard);
- files whose body contains an internal-looking link (Bitrix24, internal
  dashboards, etc.) are skipped with a warning instead of being silently
  published;
- dangling Obsidian wikilinks ([[Note]]) are unwrapped to plain text, since
  the linked note does not exist in the public site and a broken/leaking
  internal link is worse than no link.

Usage:
    python3 scripts/sync_from_vault.py [--dry-run]
"""
from __future__ import annotations

import argparse
import datetime
import re
import shutil
import sys
from pathlib import Path

VAULT_PUBLISH_DIR = Path(
    "/Users/dr/Yandex.Disk.localized/Vault_skynet/20_Cards/20.7_Publish"
)
CONTENT_DIR = Path(__file__).resolve().parent.parent / "content"

# Only these subfolders are ever scanned — candidate/ is deliberately excluded.
SCANNED_SUBDIRS = ("approved", "published")

SKIP_FILENAMES = {"00_MoC_Publish.md"}

INTERNAL_LINK_PATTERNS = [
    re.compile(r"bitrix24", re.IGNORECASE),
    # Private IPs. Octets capped at \d{1,3}\b (not \d+) so a DD.MM.YYYY date
    # like "10.06.2021" doesn't false-positive as a 10.x.x address — a real
    # last octet is always <=3 digits and ends at a word boundary, a year
    # doesn't.
    re.compile(r"\b(?:10\.|192\.168\.|172\.(?:1[6-9]|2\d|3[0-1])\.)\d{1,3}\.\d{1,3}\b"),
]

WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|([^\]]+))?\]\]")

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.DOTALL)


def parse_frontmatter(text: str) -> tuple[dict, str]:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}, text
    raw, body = match.group(1), match.group(2)
    fm: dict = {}
    for line in raw.splitlines():
        line = line.rstrip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        if value.startswith("[") and value.endswith("]"):
            items = [v.strip().strip('"').strip("'") for v in value[1:-1].split(",")]
            fm[key] = [v for v in items if v]
        else:
            fm[key] = value.strip('"').strip("'")
    return fm, body


def is_confidential(fm: dict, body: str) -> bool:
    tags = fm.get("tags", [])
    if isinstance(tags, str):
        tags = [tags]
    if any("конфиденциально" in t.lower() for t in tags):
        return True
    if "#конфиденциально" in body:
        return True
    if fm.get("category", "").strip().lower() == "личное":
        return True
    return False


def has_internal_links(body: str) -> str | None:
    for pattern in INTERNAL_LINK_PATTERNS:
        m = pattern.search(body)
        if m:
            return m.group(0)
    return None


LINKS_SECTION_RE = re.compile(
    r"^##\s*(Возможные связи|Связи|История обновлений)\s*\n.*?(?=\n##\s|\Z)",
    re.DOTALL | re.MULTILINE,
)


def strip_links_sections(body: str) -> str:
    """Drop service sections entirely — public pages carry neither vault
    backlinks (feedback_html_no_internal_links) nor the editorial changelog
    («История обновлений» — служебный раздел для сопровождения статьи в
    Vault, не для читателя сайта): both belong in the vault note, not in
    what gets published."""
    return LINKS_SECTION_RE.sub("", body)


def humanize_path(path: str) -> str:
    basename = path.rsplit("/", 1)[-1]
    basename = re.sub(r"\.md$", "", basename)
    return basename.replace("-", " ").replace("_", " ")


def unwrap_wikilinks(body: str) -> str:
    def _repl(m: re.Match) -> str:
        target, alias = m.group(1), m.group(2)
        return alias if alias else humanize_path(target)

    return WIKILINK_RE.sub(_repl, body)


def build_quartz_frontmatter(fm: dict, fallback_title: str) -> str:
    title = fm.get("title", fallback_title)
    tags = fm.get("tags", [])
    if isinstance(tags, str):
        tags = [tags]
    created = fm.get("created", datetime.date.today().isoformat())
    lines = ["---", f'title: "{title}"']
    description = fm.get("description")
    if description:
        lines.append(f'description: "{description}"')
    if tags:
        lines.append("tags:")
        lines.extend(f"  - {t}" for t in tags)
    lines.append(f"date: {created}")
    lines.append("---")
    return "\n".join(lines)


def sync(dry_run: bool = False) -> int:
    if not VAULT_PUBLISH_DIR.exists():
        print(f"Vault publish dir not found: {VAULT_PUBLISH_DIR}", file=sys.stderr)
        return 1

    CONTENT_DIR.mkdir(parents=True, exist_ok=True)

    copied, skipped_status, skipped_confidential, skipped_internal_link = 0, 0, 0, 0

    paths = [
        path
        for subdir in SCANNED_SUBDIRS
        for path in sorted((VAULT_PUBLISH_DIR / subdir).glob("*.md"))
    ]

    for path in paths:
        if path.name in SKIP_FILENAMES:
            continue

        expected_status = path.parent.name  # "approved" or "published"
        text = path.read_text(encoding="utf-8")
        fm, body = parse_frontmatter(text)

        if is_confidential(fm, body):
            print(f"SKIP (confidential): {path.name}")
            skipped_confidential += 1
            continue

        status = fm.get("publish_status", "")
        if status != expected_status:
            print(
                f"SKIP (frontmatter publish_status={status or 'missing'} "
                f"!= folder {expected_status}/): {path.name}"
            )
            skipped_status += 1
            continue

        leak = has_internal_links(body)
        if leak:
            print(f"SKIP (internal link '{leak}' found): {path.name}")
            skipped_internal_link += 1
            continue

        clean_body = unwrap_wikilinks(strip_links_sections(body))
        new_frontmatter = build_quartz_frontmatter(fm, fallback_title=path.stem)
        slug = path.stem.lower()
        cover = f"![Обложка](./{slug}-og-image.webp)\n\n"
        out_text = f"{new_frontmatter}\n\n{cover}{clean_body.lstrip(chr(10))}"

        out_path = CONTENT_DIR / path.name
        print(f"COPY: {path.name} -> {out_path.relative_to(CONTENT_DIR.parent)}")
        if not dry_run:
            out_path.write_text(out_text, encoding="utf-8")
        copied += 1

    print(
        f"\nDone. copied={copied} "
        f"skipped_not_approved={skipped_status} "
        f"skipped_confidential={skipped_confidential} "
        f"skipped_internal_link={skipped_internal_link}"
    )
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Print actions without writing files")
    args = parser.parse_args()
    sys.exit(sync(dry_run=args.dry_run))
