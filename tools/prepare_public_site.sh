#!/usr/bin/env bash
# GitHub Pages 用: SPA（index.html）＋用語静的ページ等を public_site/ に配置する。
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
  eisei1-master-data.js \
  eisei1-data-glossary.js \
  eisei1-data-original.js \
  eisei1-data-ichimon.js
do
  if [[ ! -e "$f" ]]; then
    echo "prepare_public_site.sh: 必須ファイルがありません: $f" >&2
    echo "先に python3 tools/csv_to_chintaikan_eisei_master.py と glossary_csv_to_eisei_embed_js.py を実行してください。" >&2
    exit 1
  fi
  cp "$f" "$OUT/"
done
# レガシー互換・参照用（存在すればコピー）
if [[ -e "$ROOT/chintaikanrishi-master-data.js" ]]; then
  cp "$ROOT/chintaikanrishi-master-data.js" "$OUT/"
fi
if [[ -d "$ROOT/q" ]]; then
  cp -R "$ROOT/q" "$OUT/"
fi
if [[ -d "$ROOT/terms" ]]; then
  cp -R "$ROOT/terms" "$OUT/"
fi
n="$(find "$OUT" -type f | wc -l | tr -d ' ')"
echo "prepare_public_site.sh: $OUT に $n ファイルを配置しました。"
