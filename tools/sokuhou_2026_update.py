#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
令和8年度(2026年) 賃貸不動産経営管理士試験 解答速報
TAC(資格の学校TAC)の解答速報ページをクロールし、判明している解答を
kaitou-sokuhou/2026/index.html に反映する。

マージ方針（問ごと）:
  1. TACが正答番号を公表していれば TAC を最優先。
  2. TACが未公表(ー)なら、kaitou-sokuhou/2026/answers-known.json の判明分を使う。
  3. どちらも無ければ「ー」(保留)。

使い方:
  python3 tools/sokuhou_2026_update.py --check
      取得・マージ状況を表示するだけ(ファイルは変更しない)。
      判明が1問以上あれば終了コード0、全く無ければ2。

  python3 tools/sokuhou_2026_update.py --apply
      判明分を index.html に反映(何度実行しても同じ結果になる冪等処理)。
      - 解答一覧の表は判明分を数字、未判明は「ー」で常に表示。
      - 全50問が判明したときだけ自己採点ツールを有効化(解答JSONを投入)。
        部分的な間は自己採点は「準備中」のまま(誤った自己採点を避けるため)。
      - TACのHTMLスナップショットを tools/snapshots/ に保存(gitignore済み)。
      - 没問・複数正解など想定外値があれば REVIEW REQUIRED を表示。

このスクリプトはページを書き換えるだけで、公開(mainへのマージ)はしない。
必ず人間が差分を確認してから公開すること。
"""
import argparse
import datetime
import html
import json
import os
import re
import subprocess
import sys

TAC_URL = "https://www.tac-school.co.jp/kouza_chintai/sokuhou.html"
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET = os.path.join(REPO_ROOT, "kaitou-sokuhou", "2026", "index.html")
KNOWN_JSON = os.path.join(REPO_ROOT, "kaitou-sokuhou", "2026", "answers-known.json")
SNAP_DIR = os.path.join(REPO_ROOT, "tools", "snapshots")

TOTAL_Q = 50
TAC_PUBLISHED_THRESHOLD = 45  # TAC側でこれ以上数字が入っていたら「TAC本公開」とみなす

UNPUB_TOKENS = {"ー", "―", "−", "—", "-", "–", "", "？", "?"}


# ----------------------------------------------------------------------------
def fetch(url):
    try:
        out = subprocess.run(["curl", "-sS", "-L", "--max-time", "60", url],
                             capture_output=True, timeout=90)
        if out.returncode != 0:
            sys.stderr.write("curl failed: " + out.stderr.decode("utf-8", "replace") + "\n")
            return None
        return out.stdout.decode("utf-8", "replace")
    except Exception as e:  # noqa
        sys.stderr.write("fetch error: %r\n" % e)
        return None


def parse_meta(t):
    meta = {}
    for m in re.finditer(
        r'<p>(公開予定日時|更新日時|次の更新予定)</p>\s*</div>\s*'
        r'<p class="DTLcontentList__text">(.*?)</p>', t, re.S):
        meta[m.group(1)] = html.unescape(re.sub(r'<[^>]+>', '', m.group(2))).strip()
    return meta


def parse_tac_answers(t):
    """問1〜問50 の正答セル生テキストを dict{int:str} で返す。"""
    pairs = re.findall(
        r'<div class="cell question">\s*問\s*(\d+)\s*</div>\s*'
        r'<div class="cell answer">\s*(.*?)\s*</div>', t, re.S)
    return {int(n): html.unescape(re.sub(r'<[^>]+>', '', a)).strip() for n, a in pairs}


def classify(raw):
    v = (raw or "").strip()
    if re.fullmatch(r'[1-4]', v):
        return ("num", int(v))
    if v in UNPUB_TOKENS:
        return ("unpub", None)
    if re.search(r'(没問|全員正解|全て正解|すべて正解|正解なし|全選択肢)', v):
        return ("allcorrect", v)
    return ("special", v)


def load_known():
    if not os.path.exists(KNOWN_JSON):
        return {}
    try:
        with open(KNOWN_JSON, encoding="utf-8") as f:
            data = json.load(f)
        ans = data.get("answers", {})
        out = {}
        for k, v in ans.items():
            out[int(k)] = v
        return out
    except Exception as e:  # noqa
        sys.stderr.write("known.json 読み込み失敗: %r\n" % e)
        return {}


def merge(tac_vals, known):
    """問ごとにマージ。各問について dict を返す:
       {no, kind, value, disp, source, flag}
       kind: 'num' / 'allcorrect' / 'special' / 'unpub'
       source: 'TAC' / 'known' / ''
    """
    merged = []
    for no in range(1, TOTAL_Q + 1):
        kind, value = classify(tac_vals.get(no, ""))
        source, flag = "", None
        if kind == "num":
            source = "TAC"
            disp = str(value)
        elif kind == "allcorrect":
            source = "TAC"
            disp = "※"
            flag = "問%d: 全員正解扱い (TAC表記: %r)" % (no, tac_vals.get(no, ""))
        elif kind == "special":
            source = "TAC"
            disp = "※"
            flag = "問%d: TAC想定外の値 %r (複数正解の可能性・要確認)" % (no, tac_vals.get(no, ""))
        else:  # TAC未公表 → 判明分でフォールバック
            kv = known.get(no, None)
            if kv is None:
                kind, value, disp, source = "unpub", None, "ー", ""
            else:
                kk, vv = classify(str(kv))
                if kk == "num":
                    kind, value, disp, source = "num", vv, str(vv), "known"
                elif kk in ("allcorrect", "special"):
                    kind, value, disp, source = "allcorrect", str(kv), "※", "known"
                    flag = "問%d: 判明分で全員正解/複数扱い (%r) 要確認" % (no, kv)
                else:
                    kind, value, disp, source = "unpub", None, "ー", ""
        merged.append({"no": no, "kind": kind, "value": value,
                       "disp": disp, "source": source, "flag": flag})
    return merged


def determined_count(merged):
    return sum(1 for m in merged if m["kind"] != "unpub")


# ----------------------------------------------------------------------------
def answer_section_body(merged, tac_meta, tac_full):
    determined = determined_count(merged)
    complete = determined == TOTAL_Q

    if complete:
        note = ('<p class="sokuhou-answer-note">自己採点用の参考解答です。'
                '公式の正解ではありません。</p>')
    else:
        note = ('<p class="sokuhou-answer-note">現在判明している問から順次掲載しています'
                '（%d/%d問）。「ー」は判明待ちです。自己採点用の参考解答で、'
                '公式の正解ではありません。</p>'
                % (determined, TOTAL_Q))

    rows = []
    for start in range(1, TOTAL_Q + 1, 10):
        cells = []
        for no in range(start, start + 10):
            cells.append('<span class="sokuhou-ans-pair">問%d<b>%s</b></span>'
                         % (no, merged[no - 1]["disp"]))
        rows.append('<tr><th>問%d〜問%d</th><td>%s</td></tr>'
                    % (start, start + 9, "".join(cells)))
    table = ('<table class="seo-info-table sokuhou-ans-table"><thead><tr><th>問</th>'
             '<th>解答</th></tr></thead><tbody>%s</tbody></table>' % "".join(rows))

    foot = ""
    if any(m["disp"] == "※" for m in merged):
        foot += ('<p class="sokuhou-answer-note">※ は出題団体の判断等により複数正解・'
                 '全員正解として扱われた可能性がある問題です。正式には公式の発表でご確認ください。</p>')
    if not complete:
        foot += ('<p class="sokuhou-answer-note">自己採点ツールは全50問が判明してから'
                 'ご利用いただけます（現在は判明分のみ掲載）。</p>')
    return note + table + foot


def records_json(merged):
    out = []
    for m in merged:
        d = {"no": m["no"], "label": "問%d" % m["no"], "points": 1, "choices": 4}
        if m["kind"] == "num":
            d["correct"] = m["value"]
        else:  # allcorrect / special → 全員正解扱い
            d["correct"] = "-"
            d["allCorrect"] = True
        d["field"] = ""
        out.append(d)
    return json.dumps(out, ensure_ascii=False)


def apply_to_page(merged, tac_meta, tac_full):
    with open(TARGET, encoding="utf-8") as f:
        src = f.read()
    orig = src
    complete = determined_count(merged) == TOTAL_Q

    # (1) 解答一覧セクションの本文を差し替え(冪等)
    body = answer_section_body(merged, tac_meta, tac_full)
    new, n1 = re.subn(
        r'(<h2 id="sokuhou-sec-answers">解答一覧</h2>)(.*?)(</section>)',
        lambda mm: mm.group(1) + body + mm.group(3), src, count=1, flags=re.S)
    if n1 != 1:
        return ("error", "解答一覧セクションが見つかりません。ページ構造が変わった可能性があります。", orig == src)
    src = new

    # (2) 自己採点JSON: 全問判明のときだけ投入。未完なら空([])のまま=準備中。
    json_payload = records_json(merged) if complete else "[]"
    src, n2 = re.subn(
        r'(<script type="application/json" id="sokuhou-answers">)(.*?)(</script>)',
        lambda mm: mm.group(1) + json_payload + mm.group(3), src, count=1, flags=re.S)
    if n2 != 1:
        return ("error", "sokuhou-answers が見つかりません。", orig == src)

    # (3) 最終更新日
    today = datetime.date.today().isoformat()
    src = re.sub(r'最終更新日：\d{4}-\d{2}-\d{2}', '最終更新日：' + today, src)
    src = re.sub(r'(<th>最終更新日</th><td>)\d{4}-\d{2}-\d{2}(</td>)',
                 lambda mm: mm.group(1) + today + mm.group(2), src)

    changed = src != orig
    if changed:
        with open(TARGET, "w", encoding="utf-8") as f:
            f.write(src)
    status = "ok-complete" if complete else "ok-partial"
    msg = "全50問を反映し自己採点を有効化" if complete else "判明分を反映(自己採点は準備中のまま)"
    return (status, msg + ("" if changed else "／変更なし"), not changed)


def save_snapshot(raw, meta, tac_vals, merged):
    os.makedirs(SNAP_DIR, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    with open(os.path.join(SNAP_DIR, "tac-sokuhou-%s.html" % stamp), "w",
              encoding="utf-8") as f:
        f.write(raw)
    summary = {
        "fetched_at": stamp, "meta": meta,
        "tac_answers": {str(n): tac_vals.get(n, "") for n in range(1, TOTAL_Q + 1)},
        "merged": {str(m["no"]): {"disp": m["disp"], "source": m["source"]} for m in merged},
    }
    with open(os.path.join(SNAP_DIR, "tac-sokuhou-%s.json" % stamp), "w",
              encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    return stamp


def print_status(tac_vals, tac_meta, merged):
    tac_pub = sum(1 for n in range(1, TOTAL_Q + 1) if classify(tac_vals.get(n, ""))[0] == "num")
    det = determined_count(merged)
    print("=== 取得・マージ結果 ===")
    print("TAC 公開予定日時 :", tac_meta.get("公開予定日時", "(なし)"))
    print("TAC 更新日時     :", tac_meta.get("更新日時", "(なし)"))
    print("TACで数字が入っている問数 :", tac_pub, "/", TOTAL_Q)
    print("マージ後の判明問数        :", det, "/", TOTAL_Q, "(全問判明=%s)" % (det == TOTAL_Q))
    print("マージ結果 :", " ".join(
        "%d:%s%s" % (m["no"], m["disp"], ("" if not m["source"] else "(%s)" % m["source"][0]))
        for m in merged))
    return tac_pub, det


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    if not (args.check or args.apply):
        ap.error("--check か --apply を指定してください")

    raw = fetch(TAC_URL)
    if raw is None:
        print("FETCH FAILED: TACページを取得できませんでした。")
        sys.exit(4)

    tac_meta = parse_meta(raw)
    tac_vals = parse_tac_answers(raw)
    known = load_known()
    merged = merge(tac_vals, known)
    tac_pub, det = print_status(tac_vals, tac_meta, merged)
    tac_full = tac_pub >= TAC_PUBLISHED_THRESHOLD
    flags = [m["flag"] for m in merged if m["flag"]]

    if args.check:
        print("STATUS:", "COMPLETE" if det == TOTAL_Q else ("PARTIAL(%d)" % det if det else "NONE"))
        if flags:
            print("---- REVIEW REQUIRED ----")
            for a in flags:
                print(" *", a)
        sys.exit(0 if det > 0 else 2)

    # --apply
    stamp = save_snapshot(raw, tac_meta, tac_vals, merged)
    print("スナップショット保存:", stamp)
    if det == 0:
        print("STATUS: NONE — 判明ゼロのためページは変更しませんでした。")
        sys.exit(2)

    status, msg, nochange = apply_to_page(merged, tac_meta, tac_full)
    print("APPLY:", status, "-", msg)
    if flags:
        print("---- REVIEW REQUIRED (要確認) ----")
        for a in flags:
            print(" *", a)
    if status == "error":
        sys.exit(5)
    sys.exit(0)


if __name__ == "__main__":
    main()
