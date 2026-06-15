#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""affiliate-a8-registry.chintai.yaml の A8 URL を brief・CSV に反映し講座記事を published へ。"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path
from urllib.parse import unquote

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAML が必要です: pip install pyyaml") from exc

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "data" / "affiliate-a8-registry.chintai.yaml"
CSV_PATH = ROOT / "data" / "guide_articles.csv"
BRIEFS_DIR = ROOT / "data" / "affiliate-briefs"


def _norm(url: str) -> str:
    return (url or "").strip()


def _is_a8(url: str) -> bool:
    return "px.a8.net" in _norm(url).lower()


def _label_from_url(url: str, fallback: str) -> str:
    m = re.search(r"a8ejpredirect=([^&]+)", url)
    if m:
        dest = unquote(m.group(1))
        host = dest.split("/")[2] if "://" in dest else dest
        return f"{fallback}（{host}）"
    return fallback


def _append_related(value: str, token: str) -> str:
    parts = [x.strip() for x in (value or "").split(";") if x.strip()]
    slug = token.split(":", 1)[0]
    if any(p.split(":", 1)[0] == slug for p in parts):
        return ";".join(parts)
    parts.append(token)
    return ";".join(parts)


def load_registry(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def update_brief(slug: str, products_cfg: list[dict], *, dry_run: bool) -> list[str]:
    brief_path = BRIEFS_DIR / f"{slug}.yaml"
    if not brief_path.exists():
        print(f"WARN: brief missing: {brief_path}", file=sys.stderr)
        return []
    brief = yaml.safe_load(brief_path.read_text(encoding="utf-8"))
    if not isinstance(brief, dict):
        return []
    asp_urls: list[str] = []
    by_rank = {int(p.get("rank") or 0): p for p in brief.get("products") or [] if isinstance(p, dict)}
    for item in products_cfg:
        rank = int(item.get("rank") or 0)
        a8_url = _norm(str(item.get("a8_url") or ""))
        if not a8_url:
            continue
        if not _is_a8(a8_url):
            print(f"WARN: not A8 URL rank={rank} in {slug}", file=sys.stderr)
            continue
        prod = by_rank.get(rank)
        if not prod:
            continue
        prod["a8_url"] = a8_url
        prod["affiliate_url"] = a8_url
        label = str(item.get("label") or prod.get("name") or f"rank{rank}")
        asp_urls.append(f"{a8_url}:{_label_from_url(a8_url, label)}")
    if asp_urls and not dry_run:
        brief_path.write_text(
            yaml.safe_dump(brief, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
    return asp_urls


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--registry", type=Path, default=REGISTRY)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    registry = load_registry(args.registry.resolve())
    if not registry:
        print("registry empty", file=sys.stderr)
        return 1

    with CSV_PATH.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)
    if not fieldnames:
        print("CSV header missing", file=sys.stderr)
        return 1

    by_slug = {r["slug"]: r for r in rows}
    published: list[str] = []
    pending: list[str] = []

    for slug, cfg in registry.items():
        products_cfg = cfg.get("products") or []
        required = [p for p in products_cfg if True]
        filled = [p for p in products_cfg if _is_a8(str(p.get("a8_url") or ""))]
        if len(filled) < len(required):
            pending.append(slug)
            print(f"SKIP {slug}: A8 URL {len(filled)}/{len(required)}")
            continue
        asp_urls = update_brief(slug, products_cfg, dry_run=args.dry_run)
        row = by_slug.get(slug)
        if not row:
            print(f"WARN: CSV row missing: {slug}", file=sys.stderr)
            continue
        new_rl = row.get("related_links", "")
        for token in asp_urls:
            new_rl = _append_related(new_rl, token)
        if not args.dry_run:
            row["related_links"] = new_rl
            row["content_status"] = "published"
            note = row.get("revision_note") or ""
            if "A8公開" not in note:
                row["revision_note"] = (note + " A8公開").strip()
        published.append(slug)
        print(f"OK {slug}: {len(asp_urls)} ASP link(s)")

    if args.dry_run:
        print(f"DRY-RUN: would publish {len(published)}, pending {len(pending)}")
        return 0

    with CSV_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    print(f"Published: {', '.join(published) if published else '(none)'}")
    if pending:
        print(f"Pending A8: {', '.join(pending)}")
    return 0 if not pending or published else 0


if __name__ == "__main__":
    raise SystemExit(main())
