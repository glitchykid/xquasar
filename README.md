[English](README.md) · [Русский](README.ru.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [简体中文](README.zh-CN.md)

# XQuasar

XQuasar automatically finds regenerable caches and confirmed APT, Snap and Flatpak leftovers in your Linux home. Open it to preview the plan. Unknown app folders and personal files stay in place.

## Install on Linux Mint, Ubuntu or Debian

[Download XQuasar (.deb)](https://github.com/glitchykid/xquasar/releases/latest/download/xquasar.deb) · [Published versions](https://github.com/glitchykid/xquasar/releases)

Open the downloaded file and click **Install**. Launch **XQuasar** from the applications menu. The package manager installs the desktop components. A distribution with Python 3.12 or newer is required.

The dark preview shows the total size of recognised cache files and the categories found on this scan. **All checks (38)** opens the rule catalog, including categories with zero matches. **Show paths** opens the file list. Choose **Clean up…** to review the actions and confirm. **Open recovery folder** takes you to saved profiles and launchers.

If you have a source checkout, create the installer with

```sh
sh packaging/build-deb.sh 0.7.0 ./xquasar.deb
```

## Run the CLI from source

Use Linux and Python 3.12 or newer. Install Git to clone the source. Flatpak is optional and enables automatic detection of its leftover data. Run as the owner of the home directory.

```sh
git clone https://github.com/glitchykid/xquasar.git
cd xquasar
python3 -m xquasar
```

The first command only previews the plan. Run the command below and type `yes` to apply it, or press Enter to cancel.

```sh
python3 -m xquasar --clean
```

## What gets cleaned

- **Package profiles and KDE settings** — XQuasar recognises profile directories for 23 applications, including Blender, OBS Studio, GIMP, Transmission and Neovim. For 24 more KDE applications it checks individual settings files such as `.config/kcalcrc` and `.config/spectaclerc`. A profile move requires evidence of removal, a check for another installation and a fresh activity check. Settings and profiles go to recovery intact. It checks completed APT transactions or dpkg’s residual-configuration state against the current inventory. For Snap, a recorded removal and the absence of all installed revisions identify an instance under `~/snap` or `~/.snap/data`. An expired history can leave old profiles unidentified.
- **Desktop and development caches** — The 38 categories include Qt QML bytecode, darktable thumbnails, Thunderbird HTTP and startup caches, Chromium graphics entries, and caches for Go, Gradle, Electron, pip, RubyGems, Cabal, Helm, Composer and NuGet. XQuasar also checks recognised cache formats inside installed Flatpak and Snap apps. Offline builds may need to download packages again. Go outputs and Gradle archives are checked by digest up to 64 MiB per file.
- **Running applications** — XQuasar checks user processes during preview and again during cleanup. It skips profiles and caches it can associate with a running app, including Firefox HTTP cache. Close the app and scan again to include its cache. Confirmed leftover profiles move intact to recovery.
- **Regenerable caches** — XQuasar checks standard thumbnail PNGs in the four size folders under `$XDG_CACHE_HOME/thumbnails` and binary files under `$XDG_CACHE_HOME/fontconfig`. Both the name and file header must match. The default cache root is `~/.cache`.
- **Application caches** — XQuasar recognises Chromium and Electron disk and code cache entries inside app directories in `.config`, `.local/share`, `.local/state` and `.cache`. It checks the file header and name. It also checks old thumbnails in `~/.thumbnails` and Python bytecode in `~/.local/lib/python3.*/site-packages` when the matching source exists. A recognised browser or Python cache folder is removed if cleaning its files leaves it empty.
- **Flatpak profiles** — XQuasar compares `~/.var/app` with the installed app list and checks again after confirmation. If the inventory fails, it skips these profiles. Other caches and unidentified app folders are left in place.
- **Flatpak launchers** — Menu entries in `.local/share/applications` and startup entries in `.config/autostart` move to recovery when the filename, Flatpak marker and launch command identify the same uninstalled app. XQuasar rechecks the installed apps before moving anything from Flatpak.
- **Other app leftovers** — add one known app directory per `--leftover` option. Use a path relative to home, directly under `.config`, `.cache`, `.local/share` or `.local/state`. Example: `python3 -m xquasar --clean --leftover .config/OldEditor`.
- **Firefox and desktop caches** — HTTP entries, startup data, compiled scripts, URL and extension startup caches are identified in supported Firefox profiles. Other checks recognise failed thumbnail records, the GStreamer plugin registry and Matplotlib font lists.
- **Development tools** — XQuasar recognises pip wheels, npm and Cargo package archives, Composer ZIPs, NuGet HTTP package downloads and Go build action records in their standard cache directories. An offline build may need the network again after cached packages are removed.

App folders move intact to `~/.xquasar-recovery/<run>/<original-path>`. This preserves profiles and saves. To recover one, close the app and move the folder back to its original location if that location is free. Disk space from these folders is reclaimed when you delete their recovery copies yourself.

## Development and help

```sh
docker build -t xquasar-dev .
docker run --rm --network=none xquasar-dev
```

The container runs the tests in temporary homes. For a partial scan, read the `Skipped` messages. If Flatpak is mentioned, run `flatpak list --app --columns=application:f` as the same user and retry. [Cleanup and recovery guide](docs/wiki/Guide-EN.md) · [Report an issue](https://github.com/glitchykid/xquasar/issues)
