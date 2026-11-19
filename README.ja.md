[English](README.md) · [Русский](README.ru.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [简体中文](README.zh-CN.md)

# XQuasar

XQuasar は Linux のホームにある再生成可能なキャッシュと、APT、Snap、Flatpak で削除したアプリの残存データを自動で検出します。起動すると整理の候補を確認できます。所有元を特定できないフォルダーと個人のファイルは保持します。

## Linux Mint・Ubuntu・Debian へのインストール

[XQuasar をダウンロード（.deb）](https://github.com/glitchykid/xquasar/releases/latest/download/xquasar.deb) · [公開済みバージョン](https://github.com/glitchykid/xquasar/releases)

ダウンロードしたファイルを開き、**インストール**を押します。アプリケーションメニューから **XQuasar** を起動してください。画面表示に必要なパッケージも一緒にインストールされます。Python 3.12 以降を提供するディストリビューションが必要です。

暗色の画面に、検出したキャッシュの合計サイズと該当する分類が表示されます。**すべての検査 (38)** で該当項目がない分類も確認できます。**パスを表示** で一覧を開き、**整理…** で内容を確認して実行します。退避したプロファイルやランチャーは **退避先を開く** から確認できます。

ソースからインストーラーを作成するコマンドは

```sh
sh packaging/build-deb.sh 0.7.0 ./xquasar.deb
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

- **アプリのプロファイルと KDE の設定** — Blender、OBS Studio、GIMP、Transmission、Neovim など 23 アプリのプロファイルディレクトリを検出します。さらに KDE の 24 アプリについて `.config/kcalcrc` や `.config/spectaclerc` などの設定ファイルを確認します。パッケージの削除記録と別形式でのインストールの有無を調べ、移動前に実行中のプロセスを再確認します。設定とプロファイルはそのまま退避します。 APT の削除完了記録または dpkg の設定ファイルのみが残る状態を、現在のパッケージ一覧と照合します。`~/snap` と `~/.snap/data` 内の候補には、対象インスタンスの削除記録があり、インストール済みのリビジョンが一つもないことを確認します。履歴の保存期間を過ぎたプロファイルは検出できない場合があります。
- **デスクトップと開発ツールのキャッシュ** — 全 38 分類に Qt QML バイトコード、darktable のサムネイル、Thunderbird の HTTP・起動キャッシュ、Chromium の描画キャッシュや Go、Gradle、Electron、pip、RubyGems、Cabal、Helm、Composer、NuGet のキャッシュが含まれます。インストール済みの Flatpak・Snap アプリ内でも既知の形式を調べます。オフラインビルドにはパッケージの再取得が必要になる場合があります。Go のビルド出力と Gradle アーカイブは 1 ファイル 64 MiB までハッシュを照合します。
- **実行中のアプリ** — プレビュー時と整理時にユーザーのプロセスを調べ、実行中のアプリと関連付けられたプロファイルとキャッシュを除外します。Firefox の HTTP キャッシュも対象です。アプリを閉じて再スキャンすると、そのキャッシュを確認できます。削除済みと確認したプロファイルはフォルダーごと退避します。
- **再生成できるキャッシュ** — `$XDG_CACHE_HOME/thumbnails` の 4 つのサイズ別フォルダーにある PNG と、`$XDG_CACHE_HOME/fontconfig` のキャッシュファイルが対象です。ファイル名とヘッダーの両方で形式を確認します。キャッシュの既定の場所は `~/.cache` です。
- **アプリのキャッシュ** — `.config`、`.local/share`、`.local/state`、`.cache` 内のアプリ用ディレクトリで、Chromium と Electron のディスクキャッシュやコードキャッシュをファイル名とヘッダーで識別します。`~/.thumbnails` の旧形式の保存先と、対応するソースがある `~/.local/lib/python3.*/site-packages` の Python バイトコードも対象です。これらのブラウザーまたは Python のキャッシュフォルダーが整理によって空になった場合は削除します。
- **Flatpak のプロファイル** — `~/.var/app` とインストール済みアプリの一覧を照合し、実行の確認後に再度照合します。一覧を取得できない場合はプロファイルをスキップします。その他のキャッシュや用途を特定できないアプリのフォルダーは保持します。
- **Flatpak のランチャー** — `.local/share/applications` のメニュー項目や `.config/autostart` の自動起動項目は、ファイル名、Flatpak の識別子、起動コマンドが同じ削除済みアプリを示す場合に退避します。移動の直前にインストール済みアプリを再確認します。
- **その他のアプリ** — 削除済みアプリのディレクトリが分かっている場合は、ホームからの相対パスを `--leftover` で指定できます。対象は `.config`、`.cache`、`.local/share`、`.local/state` の直下です。複数ある場合はオプションを繰り返します。例：`python3 -m xquasar --clean --leftover .config/OldEditor`。
- **Firefox とデスクトップ** — Firefox の HTTP、起動、スクリプト、URL、拡張機能起動のキャッシュを識別します。生成に失敗したサムネイルの記録、GStreamer のプラグインレジストリ、Matplotlib のフォント一覧も検査します。
- **開発ツール** — 標準のキャッシュディレクトリにある pip の wheel、npm・Cargo・Composer のアーカイブ、NuGet の HTTP パッケージ、Go のビルド記録を検出します。アーカイブを整理した後は、次のビルドで再ダウンロードが必要になる場合があります。

アプリのフォルダーはプロファイルやセーブデータごと `~/.xquasar-recovery/<実行ID>/<元のパス>` に移動します。復元するにはアプリを終了し、元のパスが空いていることを確認してから戻してください。ディスク容量が空くのは、退避したフォルダーを自分で削除した時点です。

## 開発とサポート

```sh
docker build -t xquasar-dev .
docker run --rm --network=none xquasar-dev
```

コンテナーは一時ホームでテストを実行します。走査が一部しか完了しなかった場合は `Skipped` の行を確認してください。Flatpak が原因なら、同じユーザーで `flatpak list --app --columns=application:f` を確認して再実行します。[整理と復元のガイド](docs/wiki/Guide-JA.md) · [問題を報告](https://github.com/glitchykid/xquasar/issues)
