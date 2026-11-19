[English](README.md) · [Русский](README.ru.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [简体中文](README.zh-CN.md)

# XQuasar

XQuasar automatically finds regenerable caches and confirmed Flatpak leftovers in your Linux home. Open it to preview the plan. Unknown app folders and personal files stay in place.

## Install on Linux Mint, Ubuntu or Debian

[Download XQuasar (.deb)](https://github.com/glitchykid/xquasar/releases/latest/download/xquasar.deb) · [Published versions](https://github.com/glitchykid/xquasar/releases)

Open the downloaded file and click **Install**. Launch **XQuasar** from the applications menu. The package manager installs the desktop components. A distribution with Python 3.12 or newer is required.

The preview shows file counts and cache sizes. Choose **Show paths** for details, or **Clean up…** to review the totals and confirm. If XQuasar moved any profiles, **Open recovery folder** opens their saved location.

If you have a source checkout, create the installer with

```sh
sh packaging/build-deb.sh 0.4.0 ./xquasar.deb
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

- **Regenerable caches** — XQuasar checks standard thumbnail PNGs in the four size folders under `$XDG_CACHE_HOME/thumbnails` and binary files under `$XDG_CACHE_HOME/fontconfig`. Both the name and file header must match. The default cache root is `~/.cache`.
- **Application caches** — XQuasar recognises Chromium and Electron disk and code cache entries inside app directories in `.config`, `.local/share`, `.local/state` and `.cache`. It checks the file header and name. It also checks old thumbnails in `~/.thumbnails` and Python bytecode in `~/.local/lib/python3.*/site-packages` when the matching source exists. A recognised browser or Python cache folder is removed if cleaning its files leaves it empty.
- **Flatpak profiles** — XQuasar compares `~/.var/app` with the installed app list and checks again after confirmation. If the inventory fails, it skips these profiles. Other caches and unidentified app folders are left in place.
- **Flatpak launchers** — Menu entries in `.local/share/applications` and startup entries in `.config/autostart` move to recovery when the filename, Flatpak marker and launch command identify the same uninstalled app. XQuasar rechecks the installed apps before moving anything from Flatpak.
- **Other app leftovers** — add one known app directory per `--leftover` option. Use a path relative to home, directly under `.config`, `.cache`, `.local/share` or `.local/state`. Example: `python3 -m xquasar --clean --leftover .config/OldEditor`.

App folders move intact to `~/.xquasar-recovery/<run>/<original-path>`. This preserves profiles and saves. To recover one, close the app and move the folder back to its original location if that location is free. Disk space from these folders is reclaimed when you delete their recovery copies yourself.

## Development and help

```sh
docker build -t xquasar-dev .
docker run --rm --network=none xquasar-dev
```

The container runs the tests in temporary homes. For a partial scan, read the `Skipped` messages. If Flatpak is mentioned, run `flatpak list --app --columns=application:f` as the same user and retry. [Cleanup and recovery guide](docs/wiki/Guide-EN.md) · [Report an issue](https://github.com/glitchykid/xquasar/issues)
