#!/usr/bin/env python3
"""
Sync approved candidates from Vault_skynet/20_Cards/20.7_Publish into this
Quartz site's content/ folder.

Only files whose frontmatter has publish_status: approved or published are
copied. Everything else (candidate, missing status) is skipped. This is the
last automated gate before content becomes public — it does not replace
human judgement, it backs it up:

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

SKIP_FILENAMES = {"00_MoC_Publish.md"}

INTERNAL_LINK_PATTERNS = [
    re.compile(r"bitrix24", re.IGNORECASE),
    re.compile(r"\b(?:10\.|192\.168\.|172\.(?:1[6-9]|2\d|3[0-1])\.)\d+\.\d+"),  # private IPs
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
    r"^##\s*(Возможные связи|Связи)\s*\n.*?(?=\n##\s|\Z)",
    re.DOTALL | re.MULTILINE,
)


def strip_links_sections(body: str) -> str:
    """Drop internal-linking sections entirely — public pages don't carry
    vault backlinks (feedback_html_no_internal_links): connections belong in
    the vault note, not in what gets published."""
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

    for path in sorted(VAULT_PUBLISH_DIR.glob("*.md")):
        if path.name in SKIP_FILENAMES:
            continue

        text = path.read_text(encoding="utf-8")
        fm, body = parse_frontmatter(text)

        if is_confidential(fm, body):
            print(f"SKIP (confidential): {path.name}")
            skipped_confidential += 1
            continue

        status = fm.get("publish_status", "")
        if status not in ("approved", "published"):
            print(f"SKIP (status={status or 'missing'}): {path.name}")
            skipped_status += 1
            continue

        leak = has_internal_links(body)
        if leak:
            print(f"SKIP (internal link '{leak}' found): {path.name}")
            skipped_internal_link += 1
            continue

        clean_body = unwrap_wikilinks(strip_links_sections(body))
        new_frontmatter = build_quartz_frontmatter(fm, fallback_title=path.stem)
        out_text = f"{new_frontmatter}\n{clean_body}"

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
