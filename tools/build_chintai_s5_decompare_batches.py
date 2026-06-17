#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CSV + chintai_s5_decompare_overrides から batch 生成・検証・適用。"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.apply_guide_rewrite_batch import apply_rewrites, load_rewrites_module  # noqa: E402
from tools.chintai_s5_decompare_overrides import OVERRIDES, scrub_meta, scrub_user_intent  # noqa: E402
from tools.validate_guide_hand_batch import validate_rewrites  # noqa: E402

PATCH_KEYS = (
    "title",
    "meta_description",
    "lead",
    "user_intent",
    "action_items",
    "related_links",
    "key_points",
    "revision_note",
    *(f"section_{n}_heading" for n in range(1, 6)),
    *(f"section_{n}_body" for n in range(1, 6)),
    *(f"faq_{n}_question" for n in range(1, 5)),
    *(f"faq_{n}_answer" for n in range(1, 5)),
)

BATCH_SIZE = 8
BATCH_PREFIX = "chintai_rewrite_batch_gsc"


def row_to_patch(row: dict[str, str], override: dict[str, str]) -> dict[str, str]:
    patch = {k: (row.get(k) or "").strip() for k in PATCH_KEYS}
    patch["meta_description"] = scrub_meta(patch.get("meta_description", ""))
    patch["user_intent"] = scrub_user_intent(patch.get("user_intent", ""))
    patch.update(override)
    return patch


def build_rewrites(csv_path: Path, slugs: list[str]) -> dict[str, dict[str, str]]:
    rows = {r["slug"]: r for r in csv.DictReader(csv_path.open(encoding="utf-8-sig"))}
    return {slug: row_to_patch(rows[slug], OVERRIDES[slug]) for slug in slugs}


def write_batch(path: Path, rewrites: dict[str, dict[str, str]], *, label: str) -> None:
    lines = [
        "#!/usr/bin/env python3",
        "# -*- coding: utf-8 -*-",
        f'"""{label}"""',
        "",
        "from __future__ import annotations",
        "",
        "REWRITES: dict[str, dict[str, str]] = {",
    ]
    for slug, patch in rewrites.items():
        lines.append(f'    "{slug}": {{')
        for key in PATCH_KEYS:
            if key not in patch or not patch[key]:
                continue
            lines.append(f"        {key!r}: {patch[key]!r},")
        lines.append("    },")
    lines.append("}")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def chunked(items: list[str], size: int) -> list[list[str]]:
    return [items[i : i + size] for i in range(0, len(items), size)]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument("--write-only", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--start", type=int, default=1, help="batch number start")
    args = ap.parse_args()
    root = args.root.resolve()
    csv_path = root / "data" / "guide_articles.csv"
    slugs = list(OVERRIDES.keys())
    batches = chunked(slugs, BATCH_SIZE)
    all_errors: list[str] = []
    batch_paths: list[Path] = []

    for bi, group in enumerate(batches):
        num = args.start + bi
        rewrites = build_rewrites(csv_path, group)
        non_aff = {k: v for k, v in rewrites.items() if not k.startswith("affiliate-")}
        aff = {k: v for k, v in rewrites.items() if k.startswith("affiliate-")}
        errs: list[str] = []
        if non_aff:
            errs = validate_rewrites(non_aff, root=root)
            all_errors.extend(errs)
        path = root / "tools" / f"{BATCH_PREFIX}{num}_s5fix.py"
        write_batch(path, rewrites, label=f"GSC s5fix batch {num}")
        batch_paths.append(path)
        print(f"wrote {path.name} slugs={len(group)} validate_errors={len(errs)} affiliate={len(aff)}")

    if all_errors:
        print(f"VALIDATION FAILED: {len(all_errors)}")
        for e in all_errors[:40]:
            print(" ", e)
        return 1

    if args.apply and not args.write_only:
        for path in batch_paths:
            mod = load_rewrites_module(path)
            n = apply_rewrites(csv_path, mod.REWRITES)
            print(f"applied {path.name}: {n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
