[English](Guide-EN.md) · [Русский](Guide-RU.md) · [日本語](Guide-JA.md) · [한국어](Guide-KO.md) · [简体中文](Guide-ZH.md)

# 自动清理与恢复应用配置

1. 深色窗口会显示已识别缓存的总大小和有结果的类别。点击**全部检查 (20)** 可查看完整目录，包括没有匹配项的类别。
2. 点击**查看路径**可以查看清单。点击**清理…**，核对要删除的缓存文件和要移动的项目数量，然后确认或取消。
3. 如需恢复，请在清理后点击**打开恢复目录**。关闭相关应用，将保存的启动器或配置移回原路径。如果已有同名项目，请保留两份并先比较内容。

**Firefox 与桌面缓存** — 程序可识别 Firefox 的 HTTP、启动、脚本、网址及扩展启动缓存，还会检查缩略图生成失败记录、GStreamer 插件注册表和 Matplotlib 字体列表。

**开发工具** — 程序在标准缓存目录中识别 pip wheel、npm、Cargo 和 Composer 软件包归档、NuGet HTTP 下载包以及 Go 构建记录。清理归档后，下次构建可能需要联网重新下载。

**应用缓存** — 程序在 `.config`、`.local/share`、`.local/state` 和 `.cache` 下的应用目录中，根据文件名和文件头识别 Chromium 和 Electron 的磁盘缓存及代码缓存。它还检查 `~/.thumbnails` 中的旧缩略图，以及 `~/.local/lib/python3.*/site-packages` 中仍有对应源码的 Python 字节码。如果清理后相应的浏览器或 Python 缓存目录变空，也会将其移除。

**Flatpak 启动器** — 如果文件名、Flatpak 标记和启动命令都指向同一个已卸载应用，程序会将 `.local/share/applications` 中的菜单项和 `.config/autostart` 中的自启动项移入恢复目录。移动前会再次核对已安装应用列表。

在源码目录中运行 `python3 -m xquasar` 可以预览。要执行计划，请运行 `python3 -m xquasar --clean` 并输入 `yes`。`Skipped` 提示表示某项检查或操作被跳过。退出码 0 表示成功或取消，1 表示部分完成，2 表示输入有误或无法访问主目录。

[安装步骤和命令示例](https://github.com/glitchykid/xquasar/blob/main/README.zh-CN.md)
