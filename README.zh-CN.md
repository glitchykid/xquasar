[English](README.md) · [Русский](README.ru.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [简体中文](README.zh-CN.md)

# XQuasar

XQuasar 会在 Linux 主目录中自动查找可重新生成的缓存，以及通过 APT、Snap 或 Flatpak 卸载的应用留下的数据。打开应用即可预览清理计划。个人文件和用途不明的目录都会保留。

## 在 Linux Mint、Ubuntu 或 Debian 上安装

[下载 XQuasar（.deb）](https://github.com/glitchykid/xquasar/releases/latest/download/xquasar.deb) · [已发布版本](https://github.com/glitchykid/xquasar/releases)

打开下载的文件，点击**安装**，然后在应用程序菜单中启动 **XQuasar**。包管理器会一并安装图形界面所需的组件。需要发行版提供 Python 3.12 或更高版本。

深色窗口会显示已识别缓存的总大小和有结果的类别。点击**全部检查 (22)** 可查看完整目录，包括没有匹配项的类别。点击**查看路径**可打开文件列表。点击**清理…** 核对操作后确认。可以通过**打开恢复目录**找到已保存的配置和启动器。

也可以从源码目录运行以下命令生成安装包

```sh
sh packaging/build-deb.sh 0.6.0 ./xquasar.deb
```

## 从源码运行命令行工具

需要 Linux 和 Python 3.12 或更高版本。使用 Git 克隆源码。如果安装了 Flatpak，程序还能自动识别已卸载的 Flatpak 应用留下的数据。请使用主目录所属的用户账号运行。

```sh
git clone https://github.com/glitchykid/xquasar.git
cd xquasar
python3 -m xquasar
```

第一条命令只显示计划。要执行清理，请运行以下命令并输入 `yes`。直接按 Enter 即可取消。

```sh
python3 -m xquasar --clean
```

## 可以清理的内容

- **APT 和 Snap 应用配置** — 对于 qBittorrent、VLC、mpv、Inkscape、Audacity 和 FileZilla，XQuasar 会检查 `.config`、`.local`、`.cache` 及旧版隐藏目录中的已知路径。它会将 APT 成功卸载记录或 dpkg 的配置文件残留状态与当前软件包清单核对。对于 `~/snap` 和 `~/.snap/data` 中的 Snap 实例，必须有卸载记录，且所有已安装的修订版都已移除。历史记录过期后，某些旧配置可能无法识别。
- **正在运行的应用** — 预览和清理时都会检查用户进程。能与运行中应用关联的配置目录和缓存会被跳过，包括 Firefox 的 HTTP 缓存。关闭应用后重新扫描，即可查看它的缓存。已确认卸载的应用配置会整目录移入恢复目录。
- **可重新生成的缓存** — 程序检查 `$XDG_CACHE_HOME/thumbnails` 下四个尺寸目录中的 PNG 缩略图和 `$XDG_CACHE_HOME/fontconfig` 中的字体缓存。文件名和文件头都必须符合格式。缓存根目录默认为 `~/.cache`。
- **应用缓存** — 程序在 `.config`、`.local/share`、`.local/state` 和 `.cache` 下的应用目录中，根据文件名和文件头识别 Chromium 和 Electron 的磁盘缓存及代码缓存。它还检查 `~/.thumbnails` 中的旧缩略图，以及 `~/.local/lib/python3.*/site-packages` 中仍有对应源码的 Python 字节码。如果清理后相应的浏览器或 Python 缓存目录变空，也会将其移除。
- **Flatpak 配置目录** — 程序将 `~/.var/app` 与已安装的应用列表比对，确认清理后再核对一次。如果无法获取列表，就跳过这些目录。其他缓存和无法识别的应用目录都会保留。
- **Flatpak 启动器** — 如果文件名、Flatpak 标记和启动命令都指向同一个已卸载应用，程序会将 `.local/share/applications` 中的菜单项和 `.config/autostart` 中的自启动项移入恢复目录。移动前会再次核对已安装应用列表。
- **其他应用残留** — 用 `--leftover` 指定已卸载应用的目录。路径相对于主目录，且必须是 `.config`、`.cache`、`.local/share` 或 `.local/state` 的直接子目录。可重复使用该参数。例如 `python3 -m xquasar --clean --leftover .config/OldEditor`。
- **Firefox 与桌面缓存** — 程序可识别 Firefox 的 HTTP、启动、脚本、网址及扩展启动缓存，还会检查缩略图生成失败记录、GStreamer 插件注册表和 Matplotlib 字体列表。
- **开发工具** — 程序在标准缓存目录中识别 pip wheel、npm、Cargo 和 Composer 软件包归档、NuGet HTTP 下载包以及 Go 构建记录。清理归档后，下次构建可能需要联网重新下载。

应用目录会连同配置和存档完整移到 `~/.xquasar-recovery/<本次运行标识>/<原路径>`。如需恢复，请关闭应用，确认原路径未被占用，然后移回目录。手动删除恢复副本后，磁盘空间才会释放。

## 开发与帮助

```sh
docker build -t xquasar-dev .
docker run --rm --network=none xquasar-dev
```

容器会在临时主目录中运行测试。如果扫描未能全部完成，请查看 `Skipped` 提示。若提示与 Flatpak 有关，请以同一用户运行 `flatpak list --app --columns=application:f` 并重试。[清理与恢复指南](docs/wiki/Guide-ZH.md) · [反馈问题](https://github.com/glitchykid/xquasar/issues)
