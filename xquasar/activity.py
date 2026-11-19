"""Read Linux process identities and home-relative paths used by this user."""

from functools import lru_cache
import os
from pathlib import Path
import re

from .native import PROFILES


PROC = Path("/proc")
ALIASES = (
    {"firefox", "firefox-esr", "firefox-bin", "mozilla", "org.mozilla.firefox"},
    {"chrome", "google-chrome", "google-chrome-stable", "com.google.Chrome"},
    {"chromium", "chromium-browser", "org.chromium.Chromium"},
    {"brave", "brave-browser", "BraveSoftware", "com.brave.Browser"},
    *({*names, flatpak, *(Path(template).name for template in templates)}
      for names, flatpak, templates in PROFILES),
    {"bitwarden", "bitwarden-app", "com.bitwarden.desktop"},
    {"Code", "code-oss", "com.visualstudio.code"}, {"npm", "npm-cli.js", "npx", "npx-cli.js"},
    {"nuget", "dotnet"}, {"go", "go-build"}, {"gstreamer", "gstreamer-1.0", "gst-launch-1.0"},
)


@lru_cache(maxsize=4096)
def key(name):
    name = name.lower().removesuffix(" (deleted)").removesuffix(".appimage").removesuffix("-bin")
    return "".join(c for c in name if c.isalnum())


FAMILIES = {key(n): key(min(group)) for group in ALIASES for n in group}


def identity(name):
    token = key(name)
    return FAMILIES.get(token, token)


def owner(path, roots):
    for base in (Path(".var/app"), Path(".snap/data"), Path("snap"), *roots):
        if path.is_relative_to(base):
            parts = path.relative_to(base).parts
            if parts:
                if parts[:2] == ("data", "qBittorrent"):
                    return parts[1]
                return parts[0]
    return path.parts[0] if path.parts else ""


class Activity:
    def __init__(self, home, roots):
        self.home = str(home) + "/"
        self.roots = tuple(sorted((r for r in roots.values() if r), key=lambda r: -len(r.parts)))
        self.names = set()
        self.paths = set()

    def reference(self, location):
        if location.startswith(self.home):
            path = Path(location[len(self.home):].removesuffix(" (deleted)"))
            if path.parts and ".." not in path.parts:
                self.paths.add(path)
                self.names.add(identity(owner(path, self.roots)))
        elif location.startswith(("/snap/", "/var/lib/snapd/snap/")):
            parts = location.split("/snap/", 1)[1].split("/")
            if len(parts) >= 2:
                self.names.add(identity(parts[0]))

    def busy(self, item):
        app = item.flatpak_id or owner(item.path, self.roots)
        names = {identity(app)}
        if item.flatpak_id:
            names.add(identity(app.rsplit(".", 1)[-1]))
        if item.kind.startswith("firefox_"):
            names.add(identity("firefox"))
        if "_" in app and item.path.parts[0] in ("snap", ".snap"):
            names.add(identity(app.split("_")[0]))
        if item.is_cache:
            names.add(identity(item.kind))
        return bool(self.names & names or item.path in self.paths)


def read_process(pid, state):
    # comm and argv identify apps even when their hardened helpers restrict fd access.
    comm = ""
    try:
        comm = (pid / "comm").read_text(errors="replace").strip()
        state.names.add(identity(comm))
        args = (pid / "cmdline").read_bytes().decode(errors="replace").split("\0")
    except FileNotFoundError:
        return
    except PermissionError:
        if not comm:
            raise OSError("Could not identify a user process")
        args = []
    if args and args[0]:
        state.names.add(identity(os.path.basename(args[0])))
        for arg in args[1:]:
            if arg.startswith(("--user-data-dir=", "--profile=")):
                state.reference(arg.partition("=")[2])
            elif arg.startswith("/"):
                state.reference(arg)
                if arg.endswith((".js", ".py", ".AppImage")):
                    state.names.add(identity(os.path.basename(arg)))
    for field in ("exe", "cwd"):
        try:
            location = os.readlink(pid / field)
            state.reference(location)
            if field == "exe":
                state.names.add(identity(os.path.basename(location)))
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            continue
    try:
        with os.scandir(pid / "fd") as entries:
            for entry in entries:
                try:
                    state.reference(os.readlink(entry.path))
                except (FileNotFoundError, PermissionError, ProcessLookupError):
                    continue
    except (FileNotFoundError, PermissionError, ProcessLookupError):
        pass
    try:
        with (pid / "maps").open(errors="replace") as maps:
            for line in maps:
                if state.home in line:
                    fields = line.rstrip("\n").split(maxsplit=5)
                    if len(fields) == 6:
                        state.reference(fields[-1])
    except (FileNotFoundError, PermissionError, ProcessLookupError):
        pass
    try:
        for line in (pid / "cgroup").read_text(errors="replace").splitlines():
            match = re.search(r"(?:/|app[.-])snap\.([a-z0-9_-]+)\.", line)
            if match:
                state.names.add(identity(match[1]))
            flatpak = re.search(r"/app-flatpak-([A-Za-z0-9_.]+)-[^/]+\.scope", line)
            if flatpak:
                state.names.add(identity(flatpak[1]))
                state.names.add(identity(flatpak[1].rsplit(".", 1)[-1]))
    except (FileNotFoundError, PermissionError, ProcessLookupError):
        pass


def same_user(pid):
    if pid.stat().st_uid == os.getuid():
        return True
    # Linux can assign root ownership to the proc directory of a hardened user app.
    try:
        with (pid / "status").open() as status:
            for line in status:
                if line.startswith("Uid:"):
                    return str(os.getuid()) in line.split()[1:3]
    except PermissionError:
        pass
    return False


def snapshot(home, roots):
    state = Activity(home.path, roots)
    state.reference(os.getcwd())
    seen_self = False
    for pid in PROC.iterdir():
        if not pid.name.isdecimal():
            continue
        try:
            if not same_user(pid):
                continue
            if int(pid.name) == os.getpid():
                seen_self = True
                continue
            read_process(pid, state)
        except (FileNotFoundError, ProcessLookupError):
            continue
    if not seen_self:
        raise OSError("User process inventory unavailable")
    return state
