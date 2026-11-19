"""Linux home cleanup rules and filesystem operations."""

from contextlib import contextmanager
from dataclasses import dataclass
import errno
import os
from pathlib import Path
import re
import stat
import subprocess
import time
from uuid import uuid4

from . import activity, app_data, catalog, native


DIRECTORY = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
RECOVERY = Path(".xquasar-recovery")
APP_DATA = Path(".var/app")
MANUAL_ROOTS = {Path(p) for p in (".config", ".cache", ".local/share", ".local/state")}
SHARED = {Path(p) for p in (".cache/thumbnails", ".cache/fontconfig", ".local/share/flatpak",
                            ".local/share/Trash", ".local/share/keyrings")}
APP_ID = re.compile(r"(?:[A-Za-z_][A-Za-z_0-9]*\.){2,}[A-Za-z_][A-Za-z_0-9-]*")
THUMBNAIL = re.compile(r"[a-f0-9]{32}\.png")
FONT_CACHE = re.compile(r"[a-f0-9]{32}-(le|be)(?:32|64)\.cache-([1-9][0-9]{0,2})")
PNG_HEADER = b"\x89PNG\r\n\x1a\n"


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
    size: int

    @property
    def is_cache(self):
        return self.kind in {"thumbnail", "fontconfig", "browser", "bytecode"} or self.kind in catalog.RULES

    @property
    def flatpak_id(self):
        if self.kind == "flatpak":
            return self.path.name
        if self.kind == "launcher":
            return self.path.stem
        return None

    @classmethod
    def from_stat(cls, kind, path, info):
        return cls(kind, path, (info.st_dev, info.st_ino, info.st_ctime_ns), info.st_size)


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
    relative = value.relative_to(home.path)
    if not relative.parts or relative.is_relative_to(RECOVERY):
        return None
    return relative


def identify_cache(home, parent, folder, entry, kind, pattern):
    match = pattern.fullmatch(entry.name)
    if not match or not entry.is_file(follow_symlinks=False):
        return None
    if kind in catalog.RULES:
        header = None
    elif kind == "fontconfig":
        order = "little" if match[1] == "le" else "big"
        header = (0xFC02FC04).to_bytes(4, order) + int(match[2]).to_bytes(4, order)
    elif kind == "browser":
        header = app_data.BROWSER_HEADER
    elif kind == "bytecode":
        if not app_data.has_python_source(home, folder / entry.name):
            return None
        header = app_data.PYTHON_HEADER
    else:
        header = PNG_HEADER
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
    fd = os.open(entry.name, flags, dir_fd=parent)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or mount_id(fd) != home.mount:
            return None
        matched = (catalog.matches(kind, fd, info, folder, match) if header is None
                   else os.read(fd, len(header)) == header)
        if matched and os.fstat(fd).st_ctime_ns == info.st_ctime_ns:
            return Candidate.from_stat(kind, folder / entry.name, info)
    finally:
        os.close(fd)
    return None


def cache_files(home, roots, found, warnings):
    cache = roots["cache"]
    thumbnail_roots = [Path(".thumbnails")]
    folders = []
    if cache is not None:
        thumbnail_roots.append(cache / "thumbnails")
        folders.append((cache / "fontconfig", "fontconfig", FONT_CACHE))
    for root in thumbnail_roots:
        folders.extend((root / size, "thumbnail", THUMBNAIL)
                       for size in ("normal", "large", "x-large", "xx-large"))
    app_roots = {root for root in roots.values() if root is not None}
    folders.extend(app_data.browser_cache_folders(home, app_roots, warnings))
    folders.extend(app_data.python_cache_folders(home, warnings))
    folders.extend(catalog.folders(home, roots, warnings))
    for folder, kind, pattern in folders:
        try:
            with home.directory(folder) as parent, os.scandir(parent) as entries:
                for entry in entries:
                    try:
                        item = identify_cache(home, parent, folder, entry, kind, pattern)
                        if item:
                            found.append(item)
                    except FileNotFoundError:
                        continue
                    except OSError as exc:
                        warnings.append(f"{str(folder / entry.name)!r}: {exc}")
        except (FileNotFoundError, NotADirectoryError):
            continue
        except OSError as exc:
            warnings.append(f"{str(folder)!r}: {exc}")


def launcher_candidates(home, folder, warnings):
    try:
        with home.directory(folder) as parent, os.scandir(parent) as entries:
            for entry in entries:
                name = entry.name
                if not name.endswith(".desktop") or not APP_ID.fullmatch(name[:-8]):
                    continue
                try:
                    if not entry.is_file(follow_symlinks=False):
                        continue
                    fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
                    with os.fdopen(fd, "rb", buffering=0) as stream:
                        info = os.fstat(fd)
                        if not stat.S_ISREG(info.st_mode) or info.st_size > 65536 or mount_id(fd) != home.mount:
                            continue
                        if app_data.is_flatpak_launcher(stream.read(65537), name[:-8]) and os.fstat(fd).st_ctime_ns == info.st_ctime_ns:
                            yield Candidate.from_stat("launcher", folder / name, info)
                except FileNotFoundError:
                    continue
                except OSError as exc:
                    warnings.append(f"{str(folder / name)!r}: {exc}")
    except (FileNotFoundError, NotADirectoryError):
        return
    except OSError as exc:
        warnings.append(f"{str(folder)!r}: {exc}")


def flatpak_items(home, roots, found, warnings):
    possible = []
    for root, subdir in ((roots["config"], "autostart"), (roots["data"], "applications")):
        if root is not None:
            possible.extend(launcher_candidates(home, root / subdir, warnings))
    for name in app_data.directories(home, APP_DATA, warnings):
        if APP_ID.fullmatch(name):
            path = APP_DATA / name
            try:
                with home.directory(path) as fd:
                    possible.append(Candidate.from_stat("flatpak", path, os.fstat(fd)))
            except FileNotFoundError:
                continue
            except OSError as exc:
                warnings.append(f"{str(path)!r}: {exc}")
    if possible:
        installed = installed_apps()
        found.extend(item for item in possible if item.flatpak_id not in installed)


def xdg_roots(home):
    return {key: xdg_relative(home, "XDG_" + key.upper() + "_HOME", default)
            for key, default in (("config", ".config"), ("cache", ".cache"),
                                 ("data", ".local/share"), ("state", ".local/state"))}


def native_items(home, roots, warnings):
    return [Candidate.from_stat(kind, path, info)
            for kind, path, info in native.profiles(home, roots, warnings, installed_apps)]


def scan(home, manual=()):
    found, warnings = [], []
    roots = xdg_roots(home)
    cache_files(home, roots, found, warnings)
    found.extend(native_items(home, roots, warnings))
    try:
        flatpak_items(home, roots, found, warnings)
    except OSError as exc:
        warnings.append(f"Flatpak: {exc}")
    for path in set(manual) - {item.path for item in found}:
        try:
            with home.directory(path) as fd:
                found.append(Candidate.from_stat("manual", path, os.fstat(fd)))
        except OSError as exc:
            warnings.append(f"{str(path)!r}: {exc}")
    moved_dirs = {item.path for item in found if not item.is_cache}
    plan = [item for item in found if moved_dirs.isdisjoint(item.path.parents)]
    if plan:
        try:
            running = activity.snapshot(home, roots)
        except OSError as exc:
            return [], warnings + [str(exc)]
        plan = [item for item in plan if not running.busy(item)]
    return sorted(set(plan), key=lambda item: item.path), warnings


def prune_cache_dir(home, folder, opened, warnings):
    # rmdir is atomic with respect to entries created since the preview.
    try:
        with home.directory(folder.parent) as fd:
            current = os.stat(folder.name, dir_fd=fd, follow_symlinks=False)
            if os.path.samestat(current, os.fstat(opened)):
                os.rmdir(folder.name, dir_fd=fd)
    except OSError as exc:
        if exc.errno not in (errno.ENOTEMPTY, errno.EEXIST, errno.ENOENT):
            warnings.append(f"{str(folder)!r}: {exc}")


def apply(home, selected):
    warnings, completed = [], []
    installed = None
    if any(item.flatpak_id for item in selected):
        try:
            installed = installed_apps()
        except OSError as exc:
            warnings.append(str(exc))
    session = RECOVERY / uuid4().hex
    roots = xdg_roots(home)
    refresh = 0
    for item in selected:
        path = item.path
        try:
            if item.kind in ("apt", "snap") and item not in native_items(home, roots, warnings):
                raise OSError("package removal could not be confirmed again")
            if not item.is_cache or time.monotonic() >= refresh:
                try:
                    running = activity.snapshot(home, roots)
                except OSError as exc:
                    warnings.append(str(exc))
                    break
                refresh = time.monotonic() + 0.5
            if running.busy(item):
                raise OSError("application is in use")
            with home.directory(path.parent) as parent:
                info = os.stat(path.name, dir_fd=parent, follow_symlinks=False)
                if Candidate.from_stat(item.kind, path, info) != item:
                    raise OSError("changed since preview")
                if item.is_cache:
                    if item.kind == "bytecode" and not app_data.has_python_source(home, path):
                        raise OSError("Python source no longer available")
                    os.unlink(path.name, dir_fd=parent)
                    if item.kind in {"bytecode", "browser"}:
                        prune_cache_dir(home, path.parent, parent, warnings)
                elif item.kind in {"manual", "apt", "snap"} or item.flatpak_id:
                    if item.flatpak_id and (installed is None or item.flatpak_id in installed):
                        raise OSError("Flatpak removal could not be confirmed")
                    with home.directory(session / path.parent, private=True, create=True) as dest:
                        os.rename(path.name, path.name, src_dir_fd=parent, dst_dir_fd=dest)
                else:
                    raise OSError("unrecognized cleanup rule")
            completed.append(item)
        except OSError as exc:
            warnings.append(f"{str(path)!r}: {exc}")
    return completed, warnings, session
