"""CSS / JS の読み込みURLに、中身から計算した符号を付け直す。

ブラウザは一度読んだ CSS や JS をしばらく使い回すため、ファイルを更新しても
古いままの見た目が表示されることがある（キャッシュ）。
読み込みURLの末尾を `style.css?v=a1b2c3d4` のように変えると、ブラウザは
別のファイルだと判断して必ず読み直す。

日付ではなく中身のハッシュを使っているので、

  - 中身を変えたときだけ符号が変わる（更新し忘れが起きない）
  - 中身が同じなら符号も同じ（不要な再ダウンロードが起きない）

使い方（HP フォルダで実行）:

    python tools/bump_assets.py

CSS や JS を編集したあと、コミットする前に一度実行してください。
"""
from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

HP = Path(__file__).resolve().parent.parent
INDEX = HP / "index.html"

# 符号を付ける対象。(HTML内のパス, 実ファイル)
TARGETS = [
    ("css/style.css", HP / "css" / "style.css"),
    ("js/main.js", HP / "js" / "main.js"),
]


def short_hash(path: Path) -> str:
    """ファイルの中身から8桁の符号を作る。"""
    return hashlib.sha256(path.read_bytes()).hexdigest()[:8]


def main() -> None:
    if not INDEX.exists():
        sys.exit(f"index.html が見つかりません: {INDEX}")

    html = INDEX.read_text(encoding="utf-8")
    original = html
    changed: list[str] = []

    for url, path in TARGETS:
        if not path.exists():
            print(f"  [skip] {url} が見つかりません")
            continue

        digest = short_hash(path)
        # href="css/style.css" も href="css/style.css?v=旧い符号" も拾う
        pattern = re.compile(re.escape(url) + r"(\?v=[0-9a-f]+)?")

        found = pattern.search(html)
        if not found:
            print(f"  [skip] index.html に {url} の読み込みが見つかりません")
            continue

        before = found.group(1) or "（符号なし）"
        html = pattern.sub(f"{url}?v={digest}", html)

        if before == f"?v={digest}":
            print(f"  {url}: 変更なし（?v={digest}）")
        else:
            print(f"  {url}: {before} -> ?v={digest}")
            changed.append(url)

    if html == original:
        print("\n更新の必要はありませんでした")
        return

    INDEX.write_text(html, encoding="utf-8")
    print(f"\n完了 -> index.html を更新しました（{len(changed)}件）")


if __name__ == "__main__":
    main()
