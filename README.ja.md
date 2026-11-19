[English](README.md) · [Русский](README.ru.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [简体中文](README.zh-CN.md)

# XQuasar

XQuasar は Linux のホームディレクトリを調べ、整理できる項目を一覧表示します。各行のパスと処理内容を確認してから、対象を選べます。

## Linux Mint・Ubuntu・Debian へのインストール

[XQuasar をダウンロード（.deb）](https://github.com/glitchykid/xquasar/releases/latest/download/xquasar.deb)

ダウンロードしたファイルを開き、**インストール**を押します。アプリケーションメニューから **XQuasar** を起動してください。画面表示に必要なパッケージも一緒にインストールされます。Python 3.12 以降を提供するディストリビューションが必要です。

起動すると候補が表示されます。項目にチェックを入れ、**選択した項目を整理…** を押して、完全に削除する件数と退避する件数を確認してから確定します。アプリのプロファイルを退避した場合は **退避先を開く** で内容を確認できます。

## ソースから CLI を実行する

Linux と Python 3.12 以降が必要です。ソースの取得には Git を使います。Flatpak をインストールしている場合は、削除済みアプリのデータも自動検出できます。ホームディレクトリの所有者として実行してください。

```sh
git clone https://github.com/glitchykid/xquasar.git
cd xquasar
python3 -m xquasar
```

初回のコマンドは一覧表示のみです。次のコマンドで項目番号を空白区切りで入力するか、全件なら `all` を入力し、最後に `yes` で確定します。空のまま Enter を押すと中止します。

```sh
python3 -m xquasar --clean
```

## 整理の対象

- **サムネイル** — `$XDG_CACHE_HOME/thumbnails`（既定は `~/.cache/thumbnails`）の4つのサイズ別ディレクトリから、32桁の16進数を名前に持つ標準形式の PNG キャッシュを選んで削除します。
- **空のフォルダー** — 選択したフォルダーが空であれば削除します。隠しディレクトリ、Git の作業ツリー、別のマウント先は走査対象外です。標準および XDG で設定したユーザーディレクトリは保護します。処理後に空になった親フォルダーは次回の候補になります。
- **Flatpak の残存データ** — `~/.var/app` とインストール済みアプリの一覧を照合し、確定後にも再確認します。一覧を取得できない場合は対象フォルダーをスキップします。
- **その他のアプリ** — 削除済みアプリのディレクトリが分かっている場合は、ホームからの相対パスを `--leftover` で指定できます。対象は `.config`、`.cache`、`.local/share`、`.local/state` の直下です。複数ある場合はオプションを繰り返します。例：`python3 -m xquasar --clean --leftover .config/OldEditor`。

アプリのフォルダーはプロファイルやセーブデータごと `~/.xquasar-recovery/<実行ID>/<元のパス>` に移動します。復元するにはアプリを終了し、元のパスが空いていることを確認してから戻してください。ディスク容量が空くのは、退避したフォルダーを自分で削除した時点です。

## 開発とサポート

```sh
docker build -t xquasar-dev .
docker run --rm --network=none xquasar-dev
```

コンテナーは一時ホームでテストを実行します。走査が一部しか完了しなかった場合は `Skipped` の行を確認してください。Flatpak が原因なら、同じユーザーで `flatpak list --app --columns=application:f` を確認して再実行します。[整理と復元のガイド](docs/wiki/Guide-JA.md) · [問題を報告](https://github.com/glitchykid/xquasar/issues)
