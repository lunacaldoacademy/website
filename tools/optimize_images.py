"""ルナカルドアカデミー 公式サイト用 画像最適化スクリプト

img-src/ に置いた元画像を読み取り、Web配信用に軽量化して img/ に書き出す。

  img-src/hero/ … トップのスライドショー（ファイル名順に表示。枚数自由）
  img-src/lib/  … コース紹介・代表写真・背景など、決まった場所で使う画像

トップのスライドは img-src/hero/ の中身に合わせて index.html も自動で書き換える。

使い方:
    python tools/optimize_images.py

出力:
    img/hero-01.webp / .jpg …  トップのスライド（ファイル名順）
    img/<lib名>.webp / .jpg  …  その他の画像
    img/ig-qr.png            …  QRコードだけは無変換（読み取り精度のため）
    img/logo.png / favicon.png / ogp.jpg
"""
from __future__ import annotations

import re
import shutil
import unicodedata
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# iPhoneのHEICも読めるようにする（入っていなければ黙って諦める）
try:
    import pillow_heif

    pillow_heif.register_heif_opener()
    HEIF_OK = True
except ImportError:
    HEIF_OK = False

HERE = Path(__file__).resolve().parent
HP = HERE.parent
HERO_SRC = HP / "img-src" / "hero"
LIB_SRC = HP / "img-src" / "lib"
LOGO_SRC = HP / "img-src" / "lib" / "_logo-source.png"
OUT = HP / "img"
INDEX = HP / "index.html"

WEBP_QUALITY = 82
JPEG_QUALITY = 85
LIB_MAX_EDGE = 1000       # ライブラリ画像の長辺上限

# トップのスライド。4:3 に切り抜いて統一する
HERO_W, HERO_H = 1400, 1050
PHOTO_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif"}

# 変換せずそのままコピーするもの（QRは劣化させない）
COPY_AS_IS = {"ig-qr.png"}
# アンダーバー始まりのファイルは lib の一括処理から除外する（ロゴなど個別に扱うもの）

# ブランドカラー（黒基調・高級感）
C_INK = (10, 10, 12)
C_PAPER = (242, 240, 236)
C_CRIMSON = (165, 19, 58)
C_GOLD = (201, 167, 92)
C_MUTED = (150, 150, 158)

FONT_CANDIDATES = [
    r"C:\Windows\Fonts\YuGothM.ttc",
    r"C:\Windows\Fonts\YuGothR.ttc",
    r"C:\Windows\Fonts\meiryo.ttc",
    r"C:\Windows\Fonts\YuGothB.ttc",
    r"C:\Windows\Fonts\msgothic.ttc",
]
FONT_BOLD = [
    r"C:\Windows\Fonts\YuGothB.ttc",
    r"C:\Windows\Fonts\meiryob.ttc",
    r"C:\Windows\Fonts\msgothic.ttc",
]


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    for path in (FONT_BOLD if bold else FONT_CANDIDATES):
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    return ImageFont.load_default()


# ---------------------------------------------------------------- 共通処理

def flatten(img: Image.Image) -> Image.Image:
    """アルファを白背景に合成して RGB 化（JPEG 出力用）。"""
    if img.mode in ("RGBA", "LA", "P"):
        img = img.convert("RGBA")
        bg = Image.new("RGB", img.size, (255, 255, 255))
        bg.paste(img, mask=img.split()[-1])
        return bg
    return img.convert("RGB")


def fit(img: Image.Image, max_edge: int) -> Image.Image:
    """長辺を max_edge に収める（拡大はしない）。"""
    w, h = img.size
    scale = min(1.0, max_edge / max(w, h))
    if scale >= 1.0:
        return img
    return img.resize((round(w * scale), round(h * scale)), Image.LANCZOS)


def crop_cover(img: Image.Image, w: int, h: int) -> Image.Image:
    """中央基準で w:h の比率に切り抜き、w×h にそろえる（object-fit: cover 相当）。"""
    src_ratio = img.width / img.height
    dst_ratio = w / h
    if src_ratio > dst_ratio:
        new_w = round(img.height * dst_ratio)
        left = (img.width - new_w) // 2
        img = img.crop((left, 0, left + new_w, img.height))
    elif src_ratio < dst_ratio:
        new_h = round(img.width / dst_ratio)
        top = (img.height - new_h) // 2
        img = img.crop((0, top, img.width, top + new_h))
    return img.resize((w, h), Image.LANCZOS)


def save_pair(img: Image.Image, stem: str) -> tuple[int, int]:
    webp = OUT / f"{stem}.webp"
    jpg = OUT / f"{stem}.jpg"
    img.save(webp, "WEBP", quality=WEBP_QUALITY, method=6)
    img.save(jpg, "JPEG", quality=JPEG_QUALITY, optimize=True, progressive=True)
    return webp.stat().st_size // 1024, jpg.stat().st_size // 1024


def sorted_photos(folder: Path) -> list[Path]:
    if not folder.exists():
        return []
    files, skipped = [], []
    for f in sorted(folder.iterdir(), key=lambda p: unicodedata.normalize("NFC", p.name)):
        if not f.is_file():
            continue
        ext = f.suffix.lower()
        if ext not in PHOTO_EXTS:
            continue
        if ext in (".heic", ".heif") and not HEIF_OK:
            skipped.append(f.name)
            continue
        files.append(f)
    if skipped:
        print("  [注意] HEIC形式のため読み込めませんでした:", ", ".join(skipped))
        print("         `pip install pillow-heif` を一度実行すると読めるようになります")
    return files


# ---------------------------------------------------------------- トップのスライド

def alt_from_filename(path: Path) -> str:
    """`01_教室の様子.jpg` -> `教室の様子`"""
    stem = path.stem
    if "_" in stem:
        stem = stem.split("_", 1)[1]
    return stem.strip() or "ルナカルドアカデミーのレッスンの様子"


def escape_html(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;")
             .replace(">", "&gt;").replace('"', "&quot;"))


def export_hero() -> list[dict]:
    sources = sorted_photos(HERO_SRC)
    if not sources:
        print("  [skip] img-src/hero/ に画像がありません。トップ画像は変更しません")
        return []

    for pattern in ("hero-*.webp", "hero-*.jpg"):
        for old in OUT.glob(pattern):
            old.unlink()

    slides = []
    for i, src in enumerate(sources, start=1):
        img = crop_cover(flatten(Image.open(src)), HERO_W, HERO_H)
        stem = f"hero-{i:02d}"
        kb_webp, kb_jpg = save_pair(img, stem)
        slides.append({"stem": stem, "alt": alt_from_filename(src)})
        print(f"  {stem}: {src.name} -> webp {kb_webp}KB / jpg {kb_jpg}KB")
    return slides


def update_hero_slides(slides: list[dict]) -> None:
    """index.html のスライド部分（マーカーの間）を書き換える。"""
    if not slides or not INDEX.exists():
        return

    start = "<!-- HERO-SLIDES:START"
    end = "<!-- HERO-SLIDES:END -->"
    html = INDEX.read_text(encoding="utf-8")
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.S)
    if not pattern.search(html):
        print("  [skip] index.html にスライドのマーカーが見つかりません")
        return

    lines = [start + " ここから img-src/hero/ をもとに tools/optimize_images.py が"
                     "自動生成します。手で書き換えないでください -->"]
    for i, s in enumerate(slides):
        current = " is-current" if i == 0 else ""
        loading = ' fetchpriority="high"' if i == 0 else ' loading="lazy"'
        alt = escape_html(s["alt"])
        lines += [
            f'        <figure class="hero__slide{current}">',
            '          <picture>',
            f'            <source srcset="img/{s["stem"]}.webp" type="image/webp">',
            f'            <img src="img/{s["stem"]}.jpg" width="{HERO_W}" height="{HERO_H}"'
            f' alt="{alt}"{loading}>',
            '          </picture>',
            '        </figure>',
        ]
    lines.append("        " + end)

    INDEX.write_text(pattern.sub("\n".join(lines), html), encoding="utf-8")
    print(f"  index.html のスライドを {len(slides)} 枚に更新しました")


# ---------------------------------------------------------------- ライブラリ画像

def export_lib() -> None:
    if not LIB_SRC.exists():
        print("  [skip] img-src/lib/ がありません")
        return
    for src in sorted(LIB_SRC.iterdir(), key=lambda p: p.name):
        if not src.is_file() or src.name.startswith("_"):
            continue
        if src.name in COPY_AS_IS:
            shutil.copyfile(src, OUT / src.name)
            print(f"  {src.name}（無変換コピー）")
            continue
        if src.suffix.lower() not in PHOTO_EXTS:
            continue
        img = fit(flatten(Image.open(src)), LIB_MAX_EDGE)
        kb_webp, kb_jpg = save_pair(img, src.stem)
        print(f"  {src.stem}: {img.size[0]}x{img.size[1]} "
              f"-> webp {kb_webp}KB / jpg {kb_jpg}KB")


# ---------------------------------------------------------------- ロゴ・アイコン

def cut_out_background(img: Image.Image) -> Image.Image:
    """四隅から連結した白地だけを透過にする（文字の白フチは残る）。"""
    rgb = img.convert("RGB")
    marker = (255, 0, 255)
    w, h = rgb.size
    for corner in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)):
        if rgb.getpixel(corner) == marker:
            continue
        ImageDraw.floodfill(rgb, corner, marker, thresh=24)
    alpha = Image.new("L", rgb.size, 255)
    px_rgb, px_a = rgb.load(), alpha.load()
    for y in range(h):
        for x in range(w):
            if px_rgb[x, y] == marker:
                px_a[x, y] = 0
    out = img.convert("RGBA")
    out.putalpha(alpha)
    return out


def export_logo() -> Image.Image | None:
    """白背景を透過にし、余白を詰めたロゴを書き出す。"""
    if not LOGO_SRC.exists():
        print("  [skip] ロゴが見つかりません:", LOGO_SRC)
        return None
    img = cut_out_background(Image.open(LOGO_SRC))
    bbox = img.getchannel("A").getbbox()      # 透明な余白を切り落とす
    if bbox:
        img = img.crop(bbox)
    fit(img, 600).save(OUT / "logo.png", "PNG", optimize=True)
    print(f"  logo.png: {img.size[0]}x{img.size[1]} "
          f"{(OUT / 'logo.png').stat().st_size // 1024}KB")
    return img


def export_favicon(logo: Image.Image) -> None:
    """余白を詰めたロゴを正方形の黒地に置いてファビコンにする。"""
    pad = round(max(logo.size) * 0.08)
    side = max(logo.size) + pad * 2
    canvas = Image.new("RGBA", (side, side), (*C_INK, 255))
    canvas.paste(logo, ((side - logo.width) // 2, (side - logo.height) // 2), logo)
    canvas.resize((180, 180), Image.LANCZOS).save(OUT / "favicon.png", "PNG", optimize=True)
    print("  favicon.png: 180x180")


def export_ogp() -> None:
    """SNS共有用 OGP 画像（1200x630）。黒基調でサイトの世界観に合わせる。"""
    W, H = 1200, 630
    canvas = Image.new("RGB", (W, H), C_INK)

    # 背景に1枚目のトップ画像を薄く敷く
    hero = OUT / "hero-01.jpg"
    if hero.exists():
        bg = crop_cover(Image.open(hero).convert("RGB"), W, H)
        overlay = Image.new("RGB", (W, H), C_INK)
        canvas = Image.blend(bg, overlay, 0.74)

    d = ImageDraw.Draw(canvas)
    d.rectangle([0, 0, W, 5], fill=C_CRIMSON)

    f_kicker = load_font(26)
    f_main = load_font(62, bold=True)
    f_sub = load_font(28)
    f_foot = load_font(24)

    d.text((80, 128), "キッズプログラミングスクール", font=f_kicker, fill=C_GOLD)
    d.text((80, 196), "ゲームの遊びが", font=f_main, fill=C_PAPER)
    d.text((80, 284), "学びに変わる瞬間を", font=f_main, fill=C_PAPER)

    d.line([(80, 404), (176, 404)], fill=C_CRIMSON, width=3)
    d.text((80, 428), "ルナカルドアカデミー ／ 堺美原校・富田林喜志校",
           font=f_sub, fill=C_PAPER)
    d.text((80, 522), "小学1年生〜　月2回・1コマ90分　無料体験 受付中",
           font=f_foot, fill=C_MUTED)

    canvas.save(OUT / "ogp.jpg", "JPEG", quality=88, optimize=True, progressive=True)
    print(f"  ogp.jpg: 1200x630 {(OUT / 'ogp.jpg').stat().st_size // 1024}KB")


# ---------------------------------------------------------------- 実行

def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    print("トップのスライド:")
    update_hero_slides(export_hero())
    print("ライブラリ画像:")
    export_lib()
    print("ロゴ・アイコン:")
    logo = export_logo()
    if logo is not None:
        export_favicon(logo)
    export_ogp()
    print(f"\n完了 -> {OUT}")


if __name__ == "__main__":
    main()
