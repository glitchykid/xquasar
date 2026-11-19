"""Locate recognised cache layouts and read Flatpak desktop entry metadata."""

import configparser
import importlib.util
import os
from pathlib import Path
import re
import stat
import sys


BROWSER_ENTRY = re.compile(r"[0-9a-f]{16}_[01]")
BROWSER_HEADER = (0xFCFB6D1BA7725C30).to_bytes(8, sys.byteorder)
PYTHON_ENTRY = re.compile(r"(.+)\." + re.escape(sys.implementation.cache_tag) + r"(?:\.opt-[12])?\.pyc")
PYTHON_HEADER = importlib.util.MAGIC_NUMBER
PROFILE = re.compile(r"Default|Profile [0-9]+")
SYSTEM_DIRS = {"Trash", "flatpak", "keyrings", "applications", "autostart", "icons", "fonts"}


def directories(home, path, warnings):
    try:
        with home.directory(path) as fd, os.scandir(fd) as entries:
            return [entry.name for entry in entries
                    if not entry.name.startswith(".") and entry.is_dir(follow_symlinks=False)]
    except (FileNotFoundError, NotADirectoryError):
        return []
    except OSError as exc:
        warnings.append(f"{str(path)!r}: {exc}")
        return []


def browser_cache_folders(home, roots, warnings):
    for root in roots:
        for name in directories(home, root, warnings):
            if name in SYSTEM_DIRS:
                continue
            app = root / name
            bases = [app]
            if name == "BraveSoftware":
                bases = [app / child for child in directories(home, app, warnings)
                         if child.startswith("Brave-Browser")]
            for base in bases:
                children = directories(home, base, warnings)
                profiles = [base / child for child in children if PROFILE.fullmatch(child)]
                if "Cache" in children or "Code Cache" in children:
                    profiles.append(base)
                for profile in profiles:
                    for suffix in ("Cache/Cache_Data", "Code Cache/js", "Code Cache/wasm"):
                        yield profile / suffix, "browser", BROWSER_ENTRY


def python_cache_folders(home, warnings):
    lib = Path(".local/lib")
    stack = [lib / name / "site-packages" for name in directories(home, lib, warnings)
             if re.fullmatch(r"python3\.[0-9]+t?", name)]
    while stack:
        path = stack.pop()
        for name in directories(home, path, warnings):
            if name == "__pycache__":
                yield path / name, "bytecode", PYTHON_ENTRY
            elif name.isidentifier():
                stack.append(path / name)


def has_python_source(home, cache_path):
    match = PYTHON_ENTRY.fullmatch(cache_path.name)
    if not match or cache_path.parent.name != "__pycache__":
        return False
    with home.directory(cache_path.parent.parent) as fd:
        try:
            info = os.stat(match[1] + ".py", dir_fd=fd, follow_symlinks=False)
        except FileNotFoundError:
            return False
        return stat.S_ISREG(info.st_mode)


def is_flatpak_launcher(data, app_id):
    desktop = configparser.ConfigParser(interpolation=None, delimiters=("=",))
    desktop.optionxform = str
    try:
        desktop.read_string(data.decode("utf-8"))
        entry = desktop["Desktop Entry"]
        command = entry["Exec"].split()
        if (desktop.defaults() or entry["Type"] != "Application" or entry["X-Flatpak"] != app_id
                or command[:2] not in (["flatpak", "run"], ["/usr/bin/flatpak", "run"])):
            return False
        # Recognise the unquoted command form emitted by Flatpak. Complex user
        # launchers and wrappers have no sufficiently certain automatic action.
        target = next((word for word in command[2:] if not word.startswith("--")), None)
        return target == app_id
    except (ValueError, configparser.Error, KeyError):
        return False
