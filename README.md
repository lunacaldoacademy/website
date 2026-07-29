# ルナカルドアカデミー 公式サイト

堺市美原区・東区のこどもプログラミング教室「ルナカルドアカデミー」の公式ホームページ（1ページ完結LP）。
ビルドツールは使いません。HTML / CSS / バニラJS のみで、ファイルをそのまま GitHub Pages に置いています。

## ファイル構成

| パス | 役割 |
|---|---|
| `index.html` | ページ本体。**文章の修正はここだけ** |
| `css/style.css` | 色・余白・レイアウト |
| `js/main.js` | スクロール表示・FAQ開閉・ナビのハイライト |
| `img/` | 画像一式（`tools/optimize_images.py` の出力） |
| `tools/optimize_images.py` | `../パンフレット/assets/` の素材をWeb用に軽量化するスクリプト |
| `sitemap.xml` / `robots.txt` | 検索エンジン向け |
| `.nojekyll` | GitHub Pages の Jekyll 処理を無効化 |

## ローカルで確認する

```bash
python -m http.server 8000 --directory HP
```

ブラウザで `http://localhost:8000/` を開きます。
（`index.html` をダブルクリックして直接開いても見られますが、地図の表示など一部が実環境と変わります）

## 画像を作り直す

パンフレット側のイラストを差し替えたあと、以下を実行すると `img/` が更新されます。

```bash
python tools/optimize_images.py
```

`../パンフレット/assets/` は読み取るだけで、書き換えません。

## GitHub Pages への公開

初回のみ:

1. github.com で `lunacaldoacademy/website` を Public・空の状態で作成
2. このフォルダで以下を実行

```bash
git init
git add .
git commit -m "ルナカルドアカデミー公式サイト 初版"
git branch -M main
git remote add origin https://github.com/lunacaldoacademy/website.git
git push -u origin main
```

3. リポジトリの **Settings → Pages** で Source を `Deploy from a branch` / `main` / `/ (root)` に設定
4. 数分後 `https://lunacaldoacademy.github.io/website/` で公開されます

2回目以降の更新:

```bash
git add . && git commit -m "内容を更新" && git push
```

独自ドメインを取得した場合は、このフォルダに `CNAME` ファイル（中身はドメイン名1行）を追加し、
`index.html` の `og:url` / `canonical`、`sitemap.xml`、`robots.txt` のURLを書き換えてください。

## よく差し替える項目

| 項目 | `index.html` 内の場所 |
|---|---|
| 受講料金 | `<section id="fee">` の `.fee__list` |
| 体験会の日程・内容 | `<section id="trial">` の `.trial__dl` |
| よくあるご質問 | `<section id="faq">` の `<details>`。**同じ内容を `<head>` の FAQPage 構造化データにも反映すること** |
| 電話番号・メール | `tel:` / `mailto:` のリンク（ヘッダー・アクセス・体験会・フッター・固定CTAの5箇所）と `<head>` の構造化データ |
| 生徒・保護者の声 | `<figure class="voice">` |

## ブランド表現ルール（編集時に必ず守る）

- **「月替わり」は使わない**。代わりに「幅広いコンテンツに取り組み、極められる」「多彩なジャンルを継続して深められる」
- コースは **Scratch / Minecraft教育版 / ロブロックスプログラミング / PC総合** の4種で固定
- **一人称は「わたし」**。「わたしたち」「私たち」は使わない
- 「すごい」「天才」など大げさな表現を使わない
- カフェルナカルド（1階）の言及は **保護者の待ち時間の実利** と **防犯上の安心感** に限定する。子どもの学習体験のメリットとしては書かない
- SNS表記は `@lunacaldo_academy` のみ（地名を併記しない）
- 体験会の日程は **「平日16:20〜 / 18:00〜（ご希望の日時を伺います）」** で固定。土日開催や特定日の形式にはしない

## 掲載写真について

`img/` のイラストはすべて生成AIで作成したもので、実在の生徒は写っていません。
実際の教室写真に差し替える場合は、**保護者の同意を取得したうえで** 使用してください
（同意書ひな型: `../SNS/保護者同意書_ひな型.docx`）。

## 未設定の項目

- **郵便番号**: 正確な番号が確認できていないため、住所表記から省いています。確認できたら `index.html` の住所2箇所と構造化データの `PostalAddress` に `postalCode` を追加してください
- **地図**: Googleマップの住所検索埋め込みを使用しています。Googleビジネスプロフィールを作成した場合は、その埋め込みコードに差し替えると精度が上がります
