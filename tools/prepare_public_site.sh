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
  404.html \
  about.html \
  privacy.html \
  related-sites.html \
  site-config.json \
  site-config.js \
  site-pages.css \
  site-theme.css \
  seo-editorial.css \
  site-q-index.js \
  site-terms-index.js \
  site-analytics.js \
  CNAME \
  robots.txt \
  sitemap.xml \
  .nojekyll \
  favicon.ico \
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
# AdSense サイト確認（site-config の adsenseClientId があるとき sync で必須生成）
if python3 - <<'PY'
import json, sys
from pathlib import Path
cfg = json.loads(Path("site-config.json").read_text(encoding="utf-8"))
sys.exit(0 if str(cfg.get("adsenseClientId") or "").strip() else 1)
PY
then
  if [[ ! -f "$ROOT/ads.txt" ]]; then
    echo "prepare_public_site.sh: adsenseClientId があるのに ads.txt がありません。先に python3 tools/site_config.py を実行してください。" >&2
    exit 1
  fi
  if ! grep -qE '^google\.com, pub-[0-9]+, DIRECT, f08c47fec0942fa0$' "$ROOT/ads.txt"; then
    echo "prepare_public_site.sh: ads.txt の形式が不正です（google.com, pub-…, DIRECT, f08c47fec0942fa0 の行が必要）。" >&2
    exit 1
  fi
  cp "$ROOT/ads.txt" "$OUT/ads.txt"
  # ルート配信を明示（GitHub Pages / AdSense クローラ向け）
  chmod 644 "$OUT/ads.txt"
fi
for d in articles q terms; do
  if [[ -d "$ROOT/$d" ]]; then
    cp -R "$ROOT/$d" "$OUT/"
  fi
done
# 開発用サンプル／プレビューページは公開サイトに含めない（AdSense 審査時の
# 「制作途中・低有用性コンテンツ」誤認を避ける）。noindex 済みだが配信自体も止める。
rm -rf \
  "$OUT/terms/samples" \
  "$OUT/terms/diagram-samples" \
  "$OUT/terms/g-writing-sample.html"
if [[ -f "$ROOT/privacy-terms.html" ]]; then
  cp "$ROOT/privacy-terms.html" "$OUT/"
fi
# SPA トップ（index.html）用。CSS/JS を index から分離したサイト向け。
for f in site-spa.css site-spa-fields.js site-app.css; do
  if [[ -f "$ROOT/$f" ]]; then
    cp "$ROOT/$f" "$OUT/"
  fi
done
if [[ -f "$ROOT/docs/glossary-article-slugs.json" ]]; then
  mkdir -p "$OUT/docs"
  cp "$ROOT/docs/glossary-article-slugs.json" "$OUT/docs/"
fi
if [[ -d "$ROOT/assets/brand" ]]; then
  mkdir -p "$OUT/assets"
  cp -R "$ROOT/assets/brand" "$OUT/assets/"
fi
if [[ -d "$ROOT/images/affiliate" ]]; then
  mkdir -p "$OUT/images"
  cp -R "$ROOT/images/affiliate" "$OUT/images/"
fi
if [[ -f "$ROOT/favicon.ico" ]]; then
  cp "$ROOT/favicon.ico" "$OUT/favicon.ico"
fi
n="$(find "$OUT" -type f | wc -l | tr -d ' ')"
if grep -q 'site-spa.css' "$OUT/index.html" 2>/dev/null && [[ ! -f "$OUT/site-spa.css" ]]; then
  echo "prepare_public_site.sh: index.html が site-spa.css を参照していますが public_site にありません。" >&2
  exit 1
fi
if grep -q 'site-spa-fields.js' "$OUT/index.html" 2>/dev/null && [[ ! -f "$OUT/site-spa-fields.js" ]]; then
  echo "prepare_public_site.sh: index.html が site-spa-fields.js を参照していますが public_site にありません。" >&2
  exit 1
fi
if grep -q 'site-app.css' "$OUT/index.html" 2>/dev/null && [[ ! -f "$OUT/site-app.css" ]]; then
  echo "prepare_public_site.sh: index.html が site-app.css を参照していますが public_site にありません。" >&2
  exit 1
fi
if grep -rq 'seo-editorial.css' "$OUT/terms" "$OUT/articles" 2>/dev/null && [[ ! -f "$OUT/seo-editorial.css" ]]; then
  echo "prepare_public_site.sh: 用語・ガイドが seo-editorial.css を参照していますが public_site にありません。" >&2
  exit 1
fi
echo "prepare_public_site.sh: $OUT に $n ファイルを配置しました。"
