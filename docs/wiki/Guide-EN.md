[English](Guide-EN.md) · [Русский](Guide-RU.md) · [日本語](Guide-JA.md) · [한국어](Guide-KO.md) · [简体中文](Guide-ZH.md)

# Automatic cleanup and recovery

1. The dark preview shows the total size of recognised cache files and the categories found on this scan. **All checks (20)** opens the rule catalog, including categories with zero matches.
2. Choose **Show paths** to inspect the candidates. **Clean up…** shows the number of cache files to delete and items to move before asking for confirmation.
3. After cleanup, choose **Open recovery folder** to find a saved launcher or profile. To restore it, close the affected app and move the item back to its original path. If a replacement already exists, keep both copies and compare them first.

**Firefox and desktop caches** — HTTP entries, startup data, compiled scripts, URL and extension startup caches are identified in supported Firefox profiles. Other checks recognise failed thumbnail records, the GStreamer plugin registry and Matplotlib font lists.

**Development tools** — XQuasar recognises pip wheels, npm and Cargo package archives, Composer ZIPs, NuGet HTTP package downloads and Go build action records in their standard cache directories. An offline build may need the network again after cached packages are removed.

**Application caches** — XQuasar recognises Chromium and Electron disk and code cache entries inside app directories in `.config`, `.local/share`, `.local/state` and `.cache`. It checks the file header and name. It also checks old thumbnails in `~/.thumbnails` and Python bytecode in `~/.local/lib/python3.*/site-packages` when the matching source exists. A recognised browser or Python cache folder is removed if cleaning its files leaves it empty.

**Flatpak launchers** — Menu entries in `.local/share/applications` and startup entries in `.config/autostart` move to recovery when the filename, Flatpak marker and launch command identify the same uninstalled app. XQuasar rechecks the installed apps before moving anything from Flatpak.

From a source checkout, `python3 -m xquasar` shows a preview. Run `python3 -m xquasar --clean` and type `yes` to apply it. A `Skipped` message identifies an incomplete check or action. Exit codes are 0 for success or cancellation, 1 for a partial result and 2 for invalid input or an inaccessible home.

[Installation and command examples](https://github.com/glitchykid/xquasar/blob/main/README.md)
