[English](README.md) · [Русский](README.ru.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [简体中文](README.zh-CN.md)

# XQuasar

XQuasar 会扫描 Linux 主目录，列出可以清理的项目。每行都会显示路径和处理方式，由你选择要清理的内容。

## 在 Linux Mint、Ubuntu 或 Debian 上安装

**xquasar.deb** · [已发布版本](https://github.com/glitchykid/xquasar/releases)

打开下载的文件，点击**安装**，然后在应用程序菜单中启动 **XQuasar**。包管理器会一并安装图形界面所需的组件。需要发行版提供 Python 3.12 或更高版本。

启动后会先显示预览。勾选项目，点击**清理所选项…**，核对永久删除和移入恢复目录的数量后确认。如果移动了应用配置，可以点击**打开恢复目录**查看。

也可以从源码目录运行以下命令生成安装包

```sh
sh packaging/build-deb.sh 0.2.0 ./xquasar.deb
```

## 从源码运行命令行工具

需要 Linux 和 Python 3.12 或更高版本。使用 Git 克隆源码。如果安装了 Flatpak，程序还能自动识别已卸载的 Flatpak 应用留下的数据。请使用主目录所属的用户账号运行。

```sh
git clone https://github.com/glitchykid/xquasar.git
cd xquasar
python3 -m xquasar
```

首次运行只显示预览。要执行清理，请运行以下命令，用空格分隔要处理的项目编号，或输入 `all` 全选，再输入 `yes` 确认。直接按 Enter 即可取消。

```sh
python3 -m xquasar --clean
```

## 可以清理的内容

- **缩略图** — 从 `$XDG_CACHE_HOME/thumbnails`（默认为 `~/.cache/thumbnails`）下四个尺寸目录中，删除选中的标准 PNG 缓存文件。文件名由 32 位十六进制数字组成。
- **空文件夹** — 删除选中且仍为空的目录。扫描会跳过隐藏目录、Git 工作树和独立挂载点，并保留默认及通过 XDG 配置的用户目录。清理后变空的上级目录可在下次扫描时发现。
- **Flatpak 残留** — 将 `~/.var/app` 与已安装应用列表比对，确认清理后再核对一次。如果无法获取列表，就跳过这些目录。
- **其他应用残留** — 用 `--leftover` 指定已卸载应用的目录。路径相对于主目录，且必须是 `.config`、`.cache`、`.local/share` 或 `.local/state` 的直接子目录。可重复使用该参数。例如 `python3 -m xquasar --clean --leftover .config/OldEditor`。

应用目录会连同配置和存档完整移到 `~/.xquasar-recovery/<本次运行标识>/<原路径>`。如需恢复，请关闭应用，确认原路径未被占用，然后移回目录。手动删除恢复副本后，磁盘空间才会释放。

## 开发与帮助

```sh
docker build -t xquasar-dev .
docker run --rm --network=none xquasar-dev
```

容器会在临时主目录中运行测试。如果扫描未能全部完成，请查看 `Skipped` 提示。若提示与 Flatpak 有关，请以同一用户运行 `flatpak list --app --columns=application:f` 并重试。[清理与恢复指南](docs/wiki/Guide-ZH.md) · [反馈问题](https://github.com/glitchykid/xquasar/issues)
