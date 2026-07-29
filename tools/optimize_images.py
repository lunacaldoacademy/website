"""ルナカルドアカデミー 公式サイト用 画像最適化スクリプト

2つの素材置き場を読み取り、Web配信用に軽量化して HP/img/ に出力する。

  1. img-src/hero/        … トップのスライドショー画像（ユーザーが差し替える場所）
  2. ../パンフレット/assets/ … ロゴ・コースイラスト等（読み取りのみ。書き込まない）

トップ画像は img-src/hero/ の中身に合わせて index.html のスライド部分も自動で書き換える。

使い方:
    python tools/optimize_images.py

出力:
    HP/img/hero-01.webp / .jpg …  トップのスライド（ファイル名順）
    HP/img/*.webp / *.jpg       … その他の写真イラスト
    HP/img/*.svg                … コースアイコン等（無変換コピー）
    HP/img/logo.png / favicon.png / ogp.png
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
SRC = HP.parent / "パンフレット" / "assets"
HERO_SRC = HP / "img-src" / "hero"
OUT = HP / "img"
INDEX = HP / "index.html"

MAX_EDGE = 1200          # 写真の長辺上限
WEBP_QUALITY = 82
JPEG_QUALITY = 85

# トップのスライド。4:3 に切り抜いて統一する
HERO_W, HERO_H = 1200, 900
HERO_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif"}

# パンフレット素材名 -> サイト側での名前
PHOTOS = {
    "photo_kid_smile.png": "kid-smile",
    "photo_classroom.png": "classroom",
    "photo_minecraft.png": "minecraft",
    "photo_msg.png": "msg",
}

SVGS = {
    "scene_scratch.svg": "course-scratch.svg",
    "scene_minecraft.svg": "course-minecraft.svg",
    "scene_roblox.svg": "course-roblox.svg",
    "scene_pcgen.svg": "course-pcgen.svg",
    "illust_map.svg": "map.svg",
    "illust_avatar.svg": "avatar.svg",
}

# ブランドカラー
C_YELLOW = (255, 201, 60)
C_PINK = (255, 122, 156)
C_TEAL = (93, 194, 208)
C_INK = (26, 26, 26)
C_PAPER = (255, 255, 255)
C_CREAM = (255, 244, 210)

# 日本語フォント候補（Windows標準）
FONT_CANDIDATES = [
    r"C:\Windows\Fonts\YuGothB.ttc",
    r"C:\Windows\Fonts\meiryob.ttc",
    r"C:\Windows\Fonts\meiryo.ttc",
    r"C:\Windows\Fonts\msgothic.ttc",
]


def load_font(size: int) -> ImageFont.FreeTypeFont:
    for path in FONT_CANDIDATES:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    return ImageFont.load_default()


def fit(img: Image.Image, max_edge: int = MAX_EDGE) -> Image.Image:
    """長辺を max_edge に収める（拡大はしない）。"""
    w, h = img.size
    scale = min(1.0, max_edge / max(w, h))
    if scale >= 1.0:
        return img
    return img.resize((round(w * scale), round(h * scale)), Image.LANCZOS)


def flatten(img: Image.Image) -> Image.Image:
    """アルファを白背景に合成して RGB 化（JPEG 出力用）。"""
    if img.mode in ("RGBA", "LA", "P"):
        img = img.convert("RGBA")
        bg = Image.new("RGB", img.size, C_PAPER)
        bg.paste(img, mask=img.split()[-1])
        return bg
    return img.convert("RGB")


def export_photos() -> None:
    for src_name, stem in PHOTOS.items():
        src = SRC / src_name
        if not src.exists():
            print(f"  [skip] {src_name} が見つかりません")
            continue
        img = flatten(fit(Image.open(src)))
        webp = OUT / f"{stem}.webp"
        jpg = OUT / f"{stem}.jpg"
        img.save(webp, "WEBP", quality=WEBP_QUALITY, method=6)
        img.save(jpg, "JPEG", quality=JPEG_QUALITY, optimize=True, progressive=True)
        print(
            f"  {stem}: {img.size[0]}x{img.size[1]} "
            f"webp {webp.stat().st_size // 1024}KB / jpg {jpg.stat().st_size // 1024}KB"
        )


def crop_cover(img: Image.Image, w: int, h: int) -> Image.Image:
    """中央基準で w:h の比率に切り抜き、w×h にそろえる（object-fit: cover 相当）。"""
    src_ratio = img.width / img.height
    dst_ratio = w / h
    if src_ratio > dst_ratio:                    # 元のほうが横長 -> 左右を削る
        new_w = round(img.height * dst_ratio)
        left = (img.width - new_w) // 2
        img = img.crop((left, 0, left + new_w, img.height))
    elif src_ratio < dst_ratio:                  # 元のほうが縦長 -> 上下を削る
        new_h = round(img.width / dst_ratio)
        top = (img.height - new_h) // 2
        img = img.crop((0, top, img.width, top + new_h))
    return img.resize((w, h), Image.LANCZOS)


def alt_from_filename(path: Path) -> str:
    """`01_パソコンに向かう子ども.jpg` -> `パソコンに向かう子ども`"""
    stem = path.stem
    if "_" in stem:
        stem = stem.split("_", 1)[1]
    stem = stem.strip()
    return stem or "ルナカルドアカデミーのレッスンの様子"


def escape_html(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;")
             .replace(">", "&gt;").replace('"', "&quot;"))


def collect_hero_sources() -> list[Path]:
    if not HERO_SRC.exists():
        return []
    files, skipped = [], []
    for f in sorted(HERO_SRC.iterdir(), key=lambda p: unicodedata.normalize("NFC", p.name)):
        if not f.is_file():
            continue
        ext = f.suffix.lower()
        if ext not in HERO_EXTS:
            continue
        if ext in (".heic", ".heif") and not HEIF_OK:
            skipped.append(f.name)
            continue
        files.append(f)
    if skipped:
        print("  [注意] HEIC形式のため読み込めませんでした:", ", ".join(skipped))
        print("         `pip install pillow-heif` を一度実行すると読めるようになります")
    return files


def export_hero() -> list[dict]:
    """img-src/hero/ をトップのスライド用に書き出し、スライド情報を返す。"""
    sources = collect_hero_sources()
    if not sources:
        print("  [skip] img-src/hero/ に画像がありません。トップ画像は変更しません")
        return []

    # 前回の書き出しを消してから作り直す（減らしたときに残骸が出ないように）
    for old in OUT.glob("hero-*.webp"):
        old.unlink()
    for old in OUT.glob("hero-*.jpg"):
        old.unlink()

    slides = []
    for i, src in enumerate(sources, start=1):
        img = crop_cover(flatten(Image.open(src)), HERO_W, HERO_H)
        stem = f"hero-{i:02d}"
        webp = OUT / f"{stem}.webp"
        jpg = OUT / f"{stem}.jpg"
        img.save(webp, "WEBP", quality=WEBP_QUALITY, method=6)
        img.save(jpg, "JPEG", quality=JPEG_QUALITY, optimize=True, progressive=True)
        slides.append({"stem": stem, "alt": alt_from_filename(src)})
        print(f"  {stem}: {src.name} -> webp {webp.stat().st_size // 1024}KB "
              f"/ jpg {jpg.stat().st_size // 1024}KB")
    return slides


def update_hero_slides(slides: list[dict]) -> None:
    """index.html のスライド部分（マーカーの間）を書き換える。"""
    if not slides:
        return
    if not INDEX.exists():
        print("  [skip] index.html が見つかりません")
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
        # 1枚目だけ先に読み込み、2枚目以降は後回しにして表示を速くする
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


def export_svgs() -> None:
    for src_name, dst_name in SVGS.items():
        src = SRC / src_name
        if not src.exists():
            print(f"  [skip] {src_name} が見つかりません")
            continue
        shutil.copyfile(src, OUT / dst_name)
        print(f"  {dst_name}")


def cut_out_background(img: Image.Image) -> Image.Image:
    """四隅から連結した白地だけを透過にする。

    文字の白フチなど内側の白は連結していないので残る。
    """
    rgb = img.convert("RGB")
    marker = (255, 0, 255)
    w, h = rgb.size
    for corner in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)):
        if rgb.getpixel(corner) == marker:
            continue
        ImageDraw.floodfill(rgb, corner, marker, thresh=24)
    alpha = Image.new("L", rgb.size, 255)
    px_rgb = rgb.load()
    px_a = alpha.load()
    for y in range(h):
        for x in range(w):
            if px_rgb[x, y] == marker:
                px_a[x, y] = 0
    out = img.convert("RGBA")
    out.putalpha(alpha)
    return out


def export_logo() -> Image.Image:
    """ロゴを長辺600px・背景透過で書き出し、透過版（RGBA）を返す。"""
    img = cut_out_background(Image.open(SRC / "logo.png"))
    small = fit(img, 600)
    small.save(OUT / "logo.png", "PNG", optimize=True)
    print(f"  logo.png: {small.size[0]}x{small.size[1]} "
          f"{(OUT / 'logo.png').stat().st_size // 1024}KB")
    return img


def export_favicon(logo: Image.Image) -> None:
    """ロゴ上部のシンボル（月＋カップ）部分を正方形に切り出してファビコン化。"""
    w, h = logo.size
    # ロゴは上70%がシンボル、下がテキスト。シンボル部を中央正方形でクロップ。
    sym = logo.crop((int(w * 0.10), int(h * 0.12), int(w * 0.90), int(h * 0.72)))
    side = max(sym.size)
    canvas = Image.new("RGBA", (side, side), (255, 255, 255, 255))
    canvas.paste(sym, ((side - sym.width) // 2, (side - sym.height) // 2), sym)
    canvas.resize((180, 180), Image.LANCZOS).save(OUT / "favicon.png", "PNG", optimize=True)
    print("  favicon.png: 180x180")


def export_ogp(logo: Image.Image) -> None:
    """SNS共有用 OGP 画像（1200x630）を合成。"""
    W, H = 1200, 630
    canvas = Image.new("RGB", (W, H), C_PAPER)
    d = ImageDraw.Draw(canvas)

    # 上下のブランドカラー帯
    d.rectangle([0, 0, W, 14], fill=C_YELLOW)
    d.rectangle([0, H - 74, W, H], fill=C_INK)
    # フッター帯の上に3色ライン
    seg = W // 3
    for i, color in enumerate((C_YELLOW, C_PINK, C_TEAL)):
        d.rectangle([i * seg, H - 82, (i + 1) * seg, H - 74], fill=color)

    # 背景の淡いクリーム面（右側）
    d.rectangle([W - 420, 14, W, H - 82], fill=C_CREAM)

    # ロゴ
    lg = logo.copy()
    lg.thumbnail((360, 360), Image.LANCZOS)
    canvas.paste(lg, (W - 420 + (420 - lg.width) // 2, 150), lg)

    # テキスト
    f_lead = load_font(34)
    f_main = load_font(58)
    f_sub = load_font(30)

    d.text((70, 130), "小学1年生からのこどもプログラミング教室", font=f_lead, fill=C_PINK)
    d.text((70, 200), "ルナカルドアカデミー", font=f_main, fill=C_INK)
    d.text((70, 300), "堺市美原区・東区／無料体験会 受付中", font=f_sub, fill=C_INK)

    # コースチップ
    x = 70
    chip_font = load_font(26)
    for label, color in (
        ("Scratch", C_YELLOW),
        ("Minecraft教育版", C_PINK),
        ("Roblox", C_TEAL),
        ("PC総合", C_YELLOW),
    ):
        bbox = d.textbbox((0, 0), label, font=chip_font)
        tw = bbox[2] - bbox[0]
        d.rounded_rectangle([x, 380, x + tw + 40, 434], radius=27, fill=color)
        d.text((x + 20, 392), label, font=chip_font, fill=C_INK)
        x += tw + 56

    # フッター帯のテキスト
    f_foot = load_font(28)
    d.text((70, H - 58), "@lunacaldo_academy", font=f_foot, fill=C_PAPER)
    d.text((W - 400, H - 58), "TEL 080-4249-3221", font=f_foot, fill=C_YELLOW)

    canvas.save(OUT / "ogp.png", "PNG", optimize=True)
    print(f"  ogp.png: 1200x630 {(OUT / 'ogp.png').stat().st_size // 1024}KB")


def main() -> None:
    if not SRC.exists():
        raise SystemExit(f"素材フォルダが見つかりません: {SRC}")
    OUT.mkdir(parents=True, exist_ok=True)

    print("トップのスライド:")
    update_hero_slides(export_hero())
    print("その他の写真イラスト:")
    export_photos()
    print("SVG:")
    export_svgs()
    print("ロゴ・アイコン:")
    logo = export_logo()
    export_favicon(logo)
    export_ogp(logo)
    print(f"\n完了 -> {OUT}")


if __name__ == "__main__":
    main()
