"""Linux home cleanup rules and filesystem operations."""

from contextlib import contextmanager
from dataclasses import dataclass
import os
from pathlib import Path
import re
import stat
import subprocess
from uuid import uuid4


DIRECTORY = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
RECOVERY = Path(".xquasar-recovery")
APP_DATA = Path(".var/app")
MANUAL_ROOTS = {Path(p) for p in (".config", ".cache", ".local/share", ".local/state")}
SHARED = {Path(p) for p in (".cache/thumbnails", ".local/share/flatpak",
                            ".local/share/Trash", ".local/share/keyrings")}
USER_DIRS = {"Desktop", "Documents", "Downloads", "Music", "Pictures", "Public",
             "Templates", "Videos"}
APP_ID = re.compile(r"(?:[A-Za-z_][A-Za-z_0-9]*\.){2,}[A-Za-z_][A-Za-z_0-9-]*")
THUMBNAIL = re.compile(r"[a-f0-9]{32}\.png")


def manual_path(value):
    path = Path(value)
    if (path.parent not in MANUAL_ROOTS or path.name.startswith(".")
            or path in SHARED or ".." in path.parts):
        raise ValueError(f"Expected an app directory directly under .config, .cache, "
                         f".local/share or .local/state, got {value!r}")
    return path


def mount_id(fd):
    with open(f"/proc/self/fdinfo/{fd}", encoding="ascii") as info:
        for line in info:
            if line.startswith("mnt_id:"):
                return int(line.split()[1])
    raise OSError("Linux mount information unavailable")


class BoundaryError(OSError):
    pass


class Home:
    def __init__(self, fd, path):
        self.fd = fd
        self.path = path
        self.mount = mount_id(fd)

    @contextmanager
    def directory(self, relative, *, private=False, create=False):
        """Anchor each component at an open directory. Reject links and mounts."""
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError(f"Outside home: {relative!r}")
        fd = os.dup(self.fd)
        try:
            for name in relative.parts:
                if create:
                    try:
                        os.mkdir(name, mode=0o700, dir_fd=fd)
                    except FileExistsError:
                        pass
                child = os.open(name, DIRECTORY, dir_fd=fd)
                os.close(fd)
                fd = child
                if mount_id(fd) != self.mount:
                    raise BoundaryError("separate mount")
                if private:
                    info = os.fstat(fd)
                    if info.st_uid != os.getuid() or info.st_mode & 0o077:
                        raise PermissionError("recovery directory must be private (0700)")
            yield fd
        finally:
            os.close(fd)


@contextmanager
def open_home(path):
    if not path.is_absolute() or path.resolve() == Path("/"):
        raise ValueError("Expected an absolute user home directory")
    fd = os.open(path, DIRECTORY)
    try:
        if os.fstat(fd).st_uid != os.getuid():
            raise PermissionError("home directory belongs to another user")
        yield Home(fd, path)
    finally:
        os.close(fd)


@dataclass(frozen=True)
class Candidate:
    kind: str
    path: Path
    identity: tuple

    @classmethod
    def from_stat(cls, kind, path, info):
        return cls(kind, path, (info.st_dev, info.st_ino, info.st_ctime_ns))


def installed_apps():
    try:
        result = subprocess.run(
            ["flatpak", "list", "--app", "--columns=application:f"],
            capture_output=True, check=True, timeout=10, encoding="utf-8",
            env={**os.environ, "LC_ALL": "C"},
        )
        apps = set(result.stdout.splitlines())
        if result.stderr.strip() or not all(APP_ID.fullmatch(app) for app in apps):
            raise ValueError("incomplete inventory")
        return apps
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        raise OSError("Flatpak inventory unavailable or incomplete") from exc


def xdg_relative(home, setting, default):
    value = Path(os.environ.get(setting) or home.path / default)
    if not value.is_absolute():
        return Path(default)
    if ".." in value.parts or not value.is_relative_to(home.path):
        return None
    return value.relative_to(home.path)


def protected_dirs(home):
    protected = {Path(name) for name in USER_DIRS}
    config = xdg_relative(home, "XDG_CONFIG_HOME", ".config")
    if config is None:
        # Locations may be customized in an external config file.
        raise OSError("XDG_CONFIG_HOME is outside home")
    try:
        with home.directory(config) as fd:
            flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
            source = os.open("user-dirs.dirs", flags, dir_fd=fd)
            with os.fdopen(source, encoding="utf-8", errors="surrogateescape") as file:
                if not stat.S_ISREG(os.fstat(source).st_mode):
                    raise OSError("invalid user-dirs.dirs")
                for line in file:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    match = re.fullmatch(r'XDG_\w+_DIR="((?:[^"\\]|\\.)*)"\s*(?:#.*)?', line)
                    if not match:
                        raise OSError("unrecognized user-dirs.dirs assignment")
                    value = re.sub(r'\\(["\\$`])', r'\1', match[1])
                    if value == "$HOME" or value.startswith("$HOME/"):
                        value = str(home.path) + value[len("$HOME"):]
                    path = Path(os.path.normpath(value))
                    if not path.is_absolute():
                        raise OSError("unrecognized path in user-dirs.dirs")
                    if path.is_relative_to(home.path):
                        protected.add(path.relative_to(home.path))
    except FileNotFoundError:
        pass
    return protected


def empty_dirs(home, found, warnings):
    protected = protected_dirs(home)
    app_roots = {
        xdg_relative(home, variable, default) for variable, default in (
            ("XDG_CACHE_HOME", ".cache"), ("XDG_CONFIG_HOME", ".config"),
            ("XDG_DATA_HOME", ".local/share"), ("XDG_STATE_HOME", ".local/state"),
        )
    }
    pending = [Path(".")]
    while pending:
        path = pending.pop()
        if path in app_roots:
            continue
        try:
            with home.directory(path) as fd, os.scandir(fd) as entries:
                empty = True
                children = []
                for entry in entries:
                    empty = False
                    if entry.name == ".git":
                        children.clear()
                        break
                    if not entry.name.startswith(".") and entry.is_dir(follow_symlinks=False):
                        children.append(path / entry.name)
                if empty and path.parts and path not in protected:
                    found.append(Candidate.from_stat("empty", path, os.fstat(fd)))
                pending.extend(children)
        except (BoundaryError, FileNotFoundError, NotADirectoryError):
            continue
        except OSError as exc:
            warnings.append(f"{str(path)!r}: {exc}")


def thumbnail_files(home, found):
    cache = xdg_relative(home, "XDG_CACHE_HOME", ".cache")
    if cache is None:
        return
    for size in ("normal", "large", "x-large", "xx-large"):
        path = cache / "thumbnails" / size
        try:
            with home.directory(path) as fd, os.scandir(fd) as entries:
                for entry in entries:
                    if THUMBNAIL.fullmatch(entry.name) and entry.is_file(follow_symlinks=False):
                        info = entry.stat(follow_symlinks=False)
                        found.append(Candidate.from_stat("thumbnail", path / entry.name, info))
        except FileNotFoundError:
            continue


def orphan_dirs(home, found):
    try:
        with home.directory(APP_DATA) as fd, os.scandir(fd) as entries:
            names = {entry.name for entry in entries if APP_ID.fullmatch(entry.name)
                     and entry.is_dir(follow_symlinks=False)}
    except FileNotFoundError:
        return
    if names:
        installed = installed_apps()
        for name in sorted(names - installed):
            path = APP_DATA / name
            with home.directory(path) as fd:
                found.append(Candidate.from_stat("flatpak", path, os.fstat(fd)))


def scan(home, manual):
    found, warnings = [], []
    for rule in (thumbnail_files, orphan_dirs):
        try:
            rule(home, found)
        except OSError as exc:
            warnings.append(f"{rule.__name__}: {exc}")
    try:
        empty_dirs(home, found, warnings)
    except OSError as exc:
        warnings.append(f"empty folders: {exc}")
    for path in set(manual):
        try:
            with home.directory(path) as fd:
                found.append(Candidate.from_stat("manual", path, os.fstat(fd)))
        except OSError as exc:
            warnings.append(f"{str(path)!r}: {exc}")
    return sorted(found, key=lambda item: item.path), warnings


def apply(home, selected):
    warnings, completed = [], []
    installed = None
    if any(item.kind == "flatpak" for item in selected):
        try:
            installed = installed_apps()
        except OSError as exc:
            warnings.append(str(exc))
    session = RECOVERY / uuid4().hex
    for item in selected:
        path = item.path
        try:
            with home.directory(path.parent) as parent:
                info = os.stat(path.name, dir_fd=parent, follow_symlinks=False)
                if Candidate.from_stat(item.kind, path, info) != item:
                    raise OSError("changed since preview")
                if item.kind == "empty":
                    os.rmdir(path.name, dir_fd=parent)
                elif item.kind == "thumbnail":
                    os.unlink(path.name, dir_fd=parent)
                else:
                    if item.kind == "flatpak" and (installed is None or path.name in installed):
                        raise OSError("Flatpak removal could not be confirmed")
                    with home.directory(session / path.parent, private=True, create=True) as dest:
                        os.rename(path.name, path.name, src_dir_fd=parent, dst_dir_fd=dest)
            completed.append(item)
        except OSError as exc:
            warnings.append(f"{str(path)!r}: {exc}")
    return completed, warnings, session
