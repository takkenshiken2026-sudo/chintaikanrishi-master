# -*- coding: utf-8 -*-
"""静的 HTML 用フッター（相対パス付き）と GA4 共通タグ。

- 測定IDを変えるときは GA4_MEASUREMENT_ID と site-analytics.js 内の DEFAULT_MID を揃える。
- 新規の手書き HTML では </body> 直前に analytics_snippet(Path('相対パス')) と同等の2行を置くか、
  生成ページでは static_footer_block の直後に analytics が付くので head に GA を書かない。
"""

from __future__ import annotations

import html
from pathlib import Path

FORM_URL = "https://forms.gle/duTebNY1vKqV6A816"

# GA4 測定ID（site-analytics.js の DEFAULT_MID と揃えること）
GA4_MEASUREMENT_ID = "G-NYSHQLECDS"

# フッター注記・著作権（共通フッター・静的ガイドの表記揃え）
FOOTER_DISCLAIMER = "学習用のコンテンツです。出題・法令の正確な内容は公式情報で必ず確認してください。"
SITE_COPYRIGHT = "© 2026 賃管マスター学習支援（非公式）・chintaikanrishi-master.jp"


def footer_href(rel_path: Path, site_rel: str) -> str:
    """rel_path: ROOT からの相対パス（例 q/past/y2025/q01/index.html）。site_rel: index.html / q/index.html 等。"""
    site_rel = site_rel.lstrip("/")
    parent = rel_path.parent
    parts = parent.parts
    if parent.as_posix() == "q" and site_rel == "q/index.html":
        return "index.html"
    if site_rel == "terms/index.html" and parts and parts[0] == "terms":
        return "index.html"
    up = len(parts)
    if len(parts) >= 3 and parts[0] == "q" and parts[1] == "past" and site_rel.startswith("q/") and site_rel.count("/") == 1:
        up = len(parts) - 1
    prefix = "/".join([".."] * up)
    if not prefix:
        return site_rel
    return prefix + "/" + site_rel


def analytics_snippet(rel_path: Path) -> str:
    """全静的ページ共通: フッター直後（</body> 直前想定）に置く GA4 タグ。相対パスで site-analytics.js を読む。"""
    src = html.escape(footer_href(rel_path, "site-analytics.js"))
    mid = html.escape(GA4_MEASUREMENT_ID)
    return (
        "<!-- GA4: tools/html_footer.analytics_snippet（測定IDは GA4_MEASUREMENT_ID） -->\n"
        f'<script>window.__GA4_MEASUREMENT_ID__="{mid}";</script>\n'
        f'<script defer src="{src}"></script>'
    )


def static_footer_block(rel_path: Path) -> str:
    def h(dest: str) -> str:
        return html.escape(footer_href(rel_path, dest))

    return f"""<footer class="q-static-footer">
  <nav class="q-static-footer-nav" aria-label="サイトの他ページ">
    <a href="{h("index.html")}">トップ</a>
    <a href="{h("about.html")}">このサイトについて</a>
    <a href="{h("q/index.html")}">過去問一覧</a>
    <a href="{h("terms/index.html")}">用語集</a>
    <a href="{h("articles/index.html")}">試験ガイド</a>
    <a href="{h("related-sites.html")}">関連リンク</a>
    <a href="{h("privacy.html")}">プライバシー</a>
    <a href="{html.escape(FORM_URL)}" target="_blank" rel="noopener noreferrer">お問い合わせ</a>
  </nav>
  <p><small>{html.escape(FOOTER_DISCLAIMER)}</small></p>
  <p><small>{html.escape(SITE_COPYRIGHT)}</small></p>
</footer>
{analytics_snippet(rel_path)}"""
