[English](README.md) · [Русский](README.ru.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [简体中文](README.zh-CN.md)

# XQuasar

XQuasar は Linux のホームにあるサムネイルとフォントのキャッシュ、アンインストール済みの Flatpak アプリのプロファイルを自動で検出します。起動時に整理の候補を表示し、空のものも含めて個人用フォルダーを保持します。

## Linux Mint・Ubuntu・Debian へのインストール

[XQuasar をダウンロード（.deb）](https://github.com/glitchykid/xquasar/releases/latest/download/xquasar.deb) · [公開済みバージョン](https://github.com/glitchykid/xquasar/releases)

ダウンロードしたファイルを開き、**インストール**を押します。アプリケーションメニューから **XQuasar** を起動してください。画面表示に必要なパッケージも一緒にインストールされます。Python 3.12 以降を提供するディストリビューションが必要です。

画面にはファイル数とキャッシュのサイズが表示されます。詳細は **パスを表示** で確認できます。**整理…** を押し、件数を確認して実行します。プロファイルを退避した場合は **退避先を開く** で保存場所を開けます。

ソースからインストーラーを作成するコマンドは

```sh
sh packaging/build-deb.sh 0.3.0 ./xquasar.deb
```

## ソースから CLI を実行する

Linux と Python 3.12 以降が必要です。ソースの取得には Git を使います。Flatpak をインストールしている場合は、削除済みアプリのデータも自動検出できます。ホームディレクトリの所有者として実行してください。

```sh
git clone https://github.com/glitchykid/xquasar.git
cd xquasar
python3 -m xquasar
```

最初のコマンドでは候補を表示します。次のコマンドを実行して `yes` と入力すると整理を開始します。取り消すには Enter を押します。

```sh
python3 -m xquasar --clean
```

## 整理の対象

- **再生成できるキャッシュ** — `$XDG_CACHE_HOME/thumbnails` の 4 つのサイズ別フォルダーにある PNG と、`$XDG_CACHE_HOME/fontconfig` のキャッシュファイルが対象です。ファイル名とヘッダーの両方で形式を確認します。キャッシュの既定の場所は `~/.cache` です。
- **Flatpak のプロファイル** — `~/.var/app` とインストール済みアプリの一覧を照合し、実行の確認後に再度照合します。一覧を取得できない場合はプロファイルをスキップします。その他のキャッシュや用途を特定できないアプリのフォルダーは保持します。
- **その他のアプリ** — 削除済みアプリのディレクトリが分かっている場合は、ホームからの相対パスを `--leftover` で指定できます。対象は `.config`、`.cache`、`.local/share`、`.local/state` の直下です。複数ある場合はオプションを繰り返します。例：`python3 -m xquasar --clean --leftover .config/OldEditor`。

アプリのフォルダーはプロファイルやセーブデータごと `~/.xquasar-recovery/<実行ID>/<元のパス>` に移動します。復元するにはアプリを終了し、元のパスが空いていることを確認してから戻してください。ディスク容量が空くのは、退避したフォルダーを自分で削除した時点です。

## 開発とサポート

```sh
docker build -t xquasar-dev .
docker run --rm --network=none xquasar-dev
```

コンテナーは一時ホームでテストを実行します。走査が一部しか完了しなかった場合は `Skipped` の行を確認してください。Flatpak が原因なら、同じユーザーで `flatpak list --app --columns=application:f` を確認して再実行します。[整理と復元のガイド](docs/wiki/Guide-JA.md) · [問題を報告](https://github.com/glitchykid/xquasar/issues)
