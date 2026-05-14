# -*- coding: utf-8 -*-
"""静的 HTML 用フッター（相対パス付き）。"""

from __future__ import annotations

import html
from pathlib import Path

FORM_URL = "https://forms.gle/duTebNY1vKqV6A816"


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
  <p><small>学習用の非公式コンテンツです。出題・法令の正確な内容は公式情報で必ず確認してください。</small></p>
  <p><small>© 2026 賃管マスター</small></p>
</footer>"""
