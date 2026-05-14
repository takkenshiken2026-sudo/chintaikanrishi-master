#!/usr/bin/env bash
# GitHub Pages 用: リポジトリ直下をそのまま public_site/ にミラーする（過去問のみ構成）。
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/public_site"
rm -rf "$OUT"
mkdir -p "$OUT"
cd "$ROOT"
for f in \
  index.html \
  about.html \
  privacy.html \
  site-pages.css \
  site-analytics.js \
  CNAME \
  robots.txt \
  sitemap.xml \
  .nojekyll \
  chintaikanrishi-master-data.js
do
  if [[ ! -e "$f" ]]; then
    echo "prepare_public_site.sh: 必須ファイルがありません: $f" >&2
    exit 1
  fi
  cp "$f" "$OUT/"
done
if [[ ! -d q ]]; then
  echo "prepare_public_site.sh: q/ がありません。python3 tools/build_past_question_pages.py を先に実行してください。" >&2
  exit 1
fi
cp -R q "$OUT/"
if [[ -d "$ROOT/terms" ]]; then
  cp -R "$ROOT/terms" "$OUT/terms"
fi
n="$(find "$OUT" -type f | wc -l | tr -d ' ')"
echo "prepare_public_site.sh: $OUT に $n ファイルを配置しました。"
