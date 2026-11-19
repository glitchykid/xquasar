"""Match package-manager removal records to specific application profiles."""

import gzip
import http.client
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import zlib

from .app_data import directories


DPKG_DB = Path("/var/lib/dpkg")
APT_LOGS = Path("/var/log/apt")
SNAP_SOCKET = Path("/run/snapd.socket")
SNAP_ROOTS = (Path("snap"), Path(".snap/data"))
SNAP_NAME = re.compile(r"(?=.{1,51}$)(?=[a-z0-9-]*[a-z])[a-z0-9]+(?:-[a-z0-9]+)*(?:_[a-z0-9]{1,10})?")
PACKAGE = re.compile(r"[a-z0-9][a-z0-9+.-]+")
LOG = re.compile(r"history\.log(?:\.\d+(?:\.gz)?)?")

# Package aliases sharing one profile, Flatpak ID, and exact relative paths.
# Uppercase prefixes denote the corresponding in-home XDG directory.
PROFILES = (
    (("qbittorrent", "qbittorrent-nox"), "org.qbittorrent.qBittorrent",
     ("CONFIG/qBittorrent", "DATA/qBittorrent", "DATA/data/qBittorrent", "CACHE/qBittorrent")),
    (("vlc", "vlc-bin"), "org.videolan.VLC", ("CONFIG/vlc", "DATA/vlc", "CACHE/vlc")),
    (("mpv",), "io.mpv.Mpv", ("CONFIG/mpv", "STATE/mpv", "CACHE/mpv", ".mpv")),
    (("inkscape",), "org.inkscape.Inkscape", ("CONFIG/inkscape", "CACHE/inkscape", ".inkscape")),
    (("audacity",), "org.audacityteam.Audacity",
     ("CONFIG/audacity", "DATA/audacity", "CACHE/audacity", ".audacity-data")),
    (("filezilla",), "org.filezillaproject.Filezilla", ("CONFIG/filezilla", ".filezilla")),
)


def dpkg_states():
    try:
        result = subprocess.run(["dpkg-query", "--admindir=" + str(DPKG_DB), "-W", "-f=${Package}\\t${db:Status-Status}\\n"],
                                env={**os.environ, "LC_ALL": "C"}, text=True,
                                capture_output=True, timeout=8, check=True)
        if result.stderr.strip() or not result.stdout.strip():
            raise ValueError
        held, residual = set(), set()
        for line in result.stdout.splitlines():
            name, state = line.split("\t")
            if not PACKAGE.fullmatch(name):
                raise ValueError
            if state == "config-files":
                residual.add(name)
            elif state in {"installed", "unpacked", "half-configured", "half-installed",
                           "triggers-awaited", "triggers-pending"}:
                held.add(name)
            elif state != "not-installed":
                raise ValueError
        return held, residual - held
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        raise OSError("dpkg inventory unavailable or incomplete") from exc


def apt_history():
    removed = set()
    if not APT_LOGS.is_dir():
        return removed
    for file in APT_LOGS.iterdir():
        if not LOG.fullmatch(file.name):
            continue
        opener = gzip.open if file.suffix == ".gz" else open
        with opener(file, "rt", encoding="utf-8", errors="replace") as log:
            pending = None
            for line in log:
                field, _, value = line.partition(":")
                if field == "Start-Date":
                    pending = set()
                elif field == "Error" or not line.strip():
                    pending = None
                elif pending is not None:
                    if field in {"Remove", "Purge"}:
                        for entry in value.strip().split(", "):
                            match = re.fullmatch(r"([a-z0-9][a-z0-9+.-]+)(?::[a-z0-9-]+)? \([^()]+\)", entry)
                            if match:
                                pending.add(match[1])
                    elif field == "End-Date":
                        removed.update(pending)
                        pending = None
    return removed


class SnapConnection(http.client.HTTPConnection):
    def connect(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.settimeout(self.timeout)
        self.sock.connect(str(SNAP_SOCKET))


def snap_list(endpoint):
    connection = SnapConnection("localhost", timeout=3)
    try:
        connection.request("GET", "/v2/" + endpoint + "?select=all")
        response = connection.getresponse()
        raw = response.read(8 * 1024 * 1024 + 1)
        if response.status != 200 or len(raw) > 8 * 1024 * 1024:
            raise ValueError
        body = json.loads(raw)
        if (body["type"] != "sync" or body["status-code"] != 200
                or not isinstance(body["result"], list)):
            raise ValueError
        return body["result"]
    finally:
        connection.close()


def snap_state():
    if not SNAP_SOCKET.exists() and not shutil.which("snap") and not Path("/var/lib/snapd/state.json").exists():
        return set(), set()
    try:
        held, removed = set(), set()
        for snap in snap_list("snaps"):
            name = snap["name"]
            if not SNAP_NAME.fullmatch(name):
                raise ValueError
            held.add(name)
        for change in snap_list("changes"):
            ready, status, kind = change["ready"], change["status"], change["kind"]
            if not isinstance(ready, bool):
                raise ValueError
            if ready and (status != "Done" or kind != "remove-snap"):
                continue
            names = change.get("data", {}).get("snap-names", [])
            if not isinstance(names, list) or not all(SNAP_NAME.fullmatch(n) for n in names):
                raise ValueError
            if not ready:
                if not names:
                    raise ValueError
                held.update(names)
            else:
                removed.update(names)
        return held, removed - held
    except (ValueError, OSError, http.client.HTTPException, KeyError, TypeError, AttributeError) as exc:
        raise OSError("snapd inventory unavailable or incomplete") from exc


def available_command(names):
    return any(shutil.which(name) for name in names)


def mapped_folders(home, roots):
    for names, flatpak, templates in PROFILES:
        paths = {}
        for template in templates:
            key, _, tail = template.partition("/")
            if key.isupper():
                root = roots[key.lower()]
                if root is None:
                    continue
                path = root / tail
            else:
                path = Path(template)
            try:
                with home.directory(path) as fd:
                    paths[path] = os.fstat(fd)
            except (FileNotFoundError, NotADirectoryError):
                continue
        if paths:
            yield names, flatpak, paths


def profiles(home, roots, warnings, flatpaks):
    possible_snaps = {}
    for root in SNAP_ROOTS:
        for name in directories(home, root, warnings):
            if SNAP_NAME.fullmatch(name):
                possible_snaps[root / name] = name
    try:
        mapped = list(mapped_folders(home, roots))
    except OSError as exc:
        warnings.append(str(exc))
        mapped = []
    if not (possible_snaps or mapped):
        return
    try:
        snaps, removed_snaps = snap_state()
    except OSError as exc:
        warnings.append(str(exc))
        return
    for path, name in possible_snaps.items():
        if name in removed_snaps and name not in snaps:
            try:
                with home.directory(path) as fd, os.scandir(fd) as entries:
                    if any(re.fullmatch(r"common|x?[0-9]+", e.name) and e.is_dir(follow_symlinks=False)
                           for e in entries):
                        yield "snap", path, os.fstat(fd)
            except FileNotFoundError:
                continue
            except OSError as exc:
                warnings.append(str(exc))
    if not mapped:
        return
    try:
        held, residual = dpkg_states()
        removed = residual | apt_history()
        eligible = [(names, app, paths) for names, app, paths in mapped
                    if held.isdisjoint(names) and not available_command(names)
                    and all(n.split("_")[0] not in names for n in snaps)
                    and (not removed.isdisjoint(names) or not removed_snaps.isdisjoint(names))]
        if not eligible:
            return
        try:
            installed = flatpaks()
        except OSError as exc:
            if (not isinstance(exc.__cause__, FileNotFoundError) or Path("/var/lib/flatpak").exists()
                    or Path("/etc/flatpak/installations.d").is_dir()
                    or (roots["data"] and (home.path / roots["data"] / "flatpak").exists())
                    or os.environ.get("FLATPAK_USER_DIR")):
                raise
            installed = set()
        for names, app, paths in eligible:
            if app not in installed:
                kind = "apt" if not removed.isdisjoint(names) else "snap"
                for path, info in paths.items():
                    yield kind, path, info
    except (OSError, EOFError, zlib.error) as exc:
        warnings.append(str(exc))
