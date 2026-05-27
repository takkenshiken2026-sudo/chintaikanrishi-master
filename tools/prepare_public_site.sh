#!/usr/bin/env bash
# GitHub Pages 用: SPA（index.html）＋生成済みデータ・静的ページを public_site/ に配置する。
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
  related-sites.html \
  site-config.json \
  site-config.js \
  site-pages.css \
  site-theme.css \
  site-q-index.js \
  site-terms-index.js \
  site-analytics.js \
  CNAME \
  robots.txt \
  sitemap.xml \
  .nojekyll \
  exam-site-data-past.js \
  exam-site-data-practice.js \
  exam-site-data-ichimondou.js
do
  if [[ ! -e "$f" ]]; then
    echo "prepare_public_site.sh: 必須ファイルがありません: $f" >&2
    echo "先に python3 tools/csv_to_exam_site_past_js.py と各生成スクリプトを実行してください。" >&2
    exit 1
  fi
  cp "$f" "$OUT/"
done
for d in articles q terms; do
  if [[ -d "$ROOT/$d" ]]; then
    cp -R "$ROOT/$d" "$OUT/"
  fi
done
# サイト固有 SPA データ（eisei1 / eisei2 など）。無ければスキップ。
for f in eisei1-*.js eisei2-*.js; do
  if [[ -f "$ROOT/$f" ]]; then
    cp "$ROOT/$f" "$OUT/"
  fi
done
if [[ -f "$ROOT/privacy-terms.html" ]]; then
  cp "$ROOT/privacy-terms.html" "$OUT/"
fi
if [[ -f "$ROOT/docs/glossary-article-slugs.json" ]]; then
  mkdir -p "$OUT/docs"
  cp "$ROOT/docs/glossary-article-slugs.json" "$OUT/docs/"
fi
# Cloudflare 等 CDN 向けキャッシュヒント（GitHub Pages 単体では無視される）
cat > "$OUT/_headers" <<'EOF'
/eisei1-*.js
  Cache-Control: public, max-age=604800, stale-while-revalidate=86400
/site-*.js
  Cache-Control: public, max-age=86400, stale-while-revalidate=3600
/site-theme.css
  Cache-Control: public, max-age=86400, stale-while-revalidate=3600
/site-pages.css
  Cache-Control: public, max-age=86400, stale-while-revalidate=3600
EOF
# 静的アセットにビルド版クエリを付与（デプロイごとに更新）
ASSET_VER="${GITHUB_SHA:-$(git -C "$ROOT" rev-parse --short HEAD 2>/dev/null || echo dev)}"
ASSET_VER="${ASSET_VER:0:8}"
python3 - "$OUT/index.html" "$ASSET_VER" <<'PY'
import re, sys
path, ver = sys.argv[1], sys.argv[2]
text = open(path, encoding="utf-8").read()
assets = [
    "eisei1-data-original.js", "eisei1-master-data.js",
    "eisei1-data-glossary.js", "eisei1-data-ichimon.js",
    "site-config.js", "site-theme.css", "site-analytics.js",
]
for name in assets:
    text = re.sub(
        rf'((?:src|href)=["\']){re.escape(name)}(?:\?[^"\']*)?(["\'])',
        rf"\1{name}?v={ver}\2",
        text,
    )
    text = re.sub(
        rf"loadLazyScript\(['\"]{re.escape(name)}(?:\?[^'\']*)?['\"]\)",
        f"loadLazyScript('{name}?v={ver}')",
        text,
    )
open(path, "w", encoding="utf-8").write(text)
PY
n="$(find "$OUT" -type f | wc -l | tr -d ' ')"
echo "prepare_public_site.sh: $OUT に $n ファイルを配置しました。"
