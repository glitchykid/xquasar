[English](README.md) · [Русский](README.ru.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [简体中文](README.zh-CN.md)

# XQuasar

XQuasar previews cleanup candidates in your Linux home directory. Each row shows the path and the action. You choose which items to clean.

## Quick start

Use Linux and Python 3.12 or newer. Install Git to clone the source. Flatpak is optional and enables automatic detection of its leftover data. Run as the owner of the home directory.

```sh
git clone https://github.com/glitchykid/xquasar.git
cd xquasar
python3 -m xquasar
```

The first run only previews. To clean, run the following command, enter item numbers separated by spaces or `all`, then type `yes`. Press Enter to cancel.

```sh
python3 -m xquasar --clean
```

## What gets cleaned

- **Thumbnails** — deletes selected cache files with standard 32-digit hexadecimal PNG names in the four thumbnail size directories under `$XDG_CACHE_HOME/thumbnails` (default `~/.cache/thumbnails`).
- **Empty folders** — removes selected, currently empty folders. The scan skips hidden trees, Git working trees and separate mounts. Standard and configured XDG user directories are preserved. A parent that becomes empty can appear on the next scan.
- **Flatpak leftovers** — compares `~/.var/app` with the installed app list and checks it again after confirmation. If the inventory is unavailable, the affected folders are skipped.
- **Other app leftovers** — add one known app directory per `--leftover` option. Use a path relative to home, directly under `.config`, `.cache`, `.local/share` or `.local/state`. Example: `python3 -m xquasar --clean --leftover .config/OldEditor`.

App folders move intact to `~/.xquasar-recovery/<run>/<original-path>`. This preserves profiles and saves. To recover one, close the app and move the folder back to its original location if that location is free. Disk space from these folders is reclaimed when you delete their recovery copies yourself.

## Development and help

```sh
docker build -t xquasar-dev .
docker run --rm --network=none xquasar-dev
```

The container runs the tests in temporary homes. For a partial scan, read the `Skipped` messages. If Flatpak is mentioned, run `flatpak list --app --columns=application:f` as the same user and retry. [Cleanup and recovery guide](docs/wiki/Guide-EN.md) · [Report an issue](https://github.com/glitchykid/xquasar/issues)
