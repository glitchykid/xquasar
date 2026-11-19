"""Bounded, format-specific rules for regenerable application caches."""

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import struct
import zipfile

from .app_data import directories


@dataclass(frozen=True)
class Rule:
    label: str
    folder: str
    filename: str
    signature: bytes = b""


# Templates start at an in-home XDG root or at a fixed home-relative location.
# Each variable consumes exactly one directory component.
PROFILE = "{profiles}/{profile}/"
STARTUP = PROFILE + "startupCache"
ZIP = b"PK\x03\x04"
GZIP = b"\x1f\x8b\x08"
RULES = {
    "firefox_http": Rule("Firefox HTTP", PROFILE + "cache2/entries", r"[A-F0-9]{40}"),
    "firefox_startup": Rule("Firefox startup", STARTUP, r"startupCache\.[48]\.(?:little|big)", b"startupcache0002\0"),
    "firefox_script": Rule("Firefox scripts", STARTUP, r"scriptCache(?:-child)?(?:-current)?\.bin", b"mozXDRcachev003\0"),
    "firefox_url": Rule("Firefox URL cache", STARTUP, r"urlCache(?:-current)?\.bin", b"mozURLcachev003\0"),
    "firefox_webext": Rule("Firefox extension startup", STARTUP, r"webext\.sc\.lz4", b"mozJSSCLz40v001\0"),
    "failed_thumbnail": Rule("Failed thumbnails", "{cache}/thumbnails/fail/{app}", r"[a-f0-9]{32}\.png", b"\x89PNG\r\n\x1a\n"),
    "gstreamer": Rule("GStreamer registry", "{cache}/gstreamer-1.0", r"registry\.[a-zA-Z0-9_-]+\.bin", b"\xc0\xde\xf0\x0d"),
    "matplotlib": Rule("Matplotlib fonts", "{cache}/matplotlib", r"fontlist-v([0-9]+)\.json"),
    "pip": Rule("pip wheels", "{cache}/pip/wheels/{hh}/{hh}/{hh}/{wheelhash}",
                r"[\w.]+-[\w.!+]+-(?:[\w.]+-)?[\w.]+-[\w.]+-[\w.]+\.whl", ZIP),
    "npm": Rule("npm package archives", ".npm/_cacache/content-v2/sha512/{hh}/{hh}", r"[a-f0-9]{124}", GZIP),
    "cargo": Rule("Cargo crate archives", ".cargo/registry/cache/{crates}",
                 r"[A-Za-z0-9_-]+-[0-9]+\.[0-9]+\.[0-9]+(?:[-+][\w.+-]+)?\.crate", GZIP),
    "composer": Rule("Composer archives", "{cache}/composer/files/{package}/{package}", r"[a-f0-9]{40}\.zip", ZIP),
    "nuget": Rule("NuGet HTTP", "{data}/NuGet/v3-cache/{feed}", r"nupkg_[\w.-]+\.[0-9][\w.+-]*\.dat", ZIP),
    "go": Rule("Go build actions", "{cache}/go-build/{hh}", r"[a-f0-9]{64}-a"),
}
COMPONENTS = {
    "{profile}": r"[^./][^/]*", "{app}": r"[\w.-]+", "{hh}": r"[a-f0-9]{2}",
    "{wheelhash}": r"[a-f0-9]{50}", "{crates}": r"(?:index\.crates\.io|github\.com)-[0-9a-f]{16}",
    "{package}": r"[a-z0-9][a-z0-9_.-]*", "{feed}": r"[a-fA-F0-9]{40}\$[^/]+",
}


def folders(home, roots, warnings):
    cache = roots["cache"]
    profiles = [Path(".var/app/org.mozilla.firefox/cache/mozilla/firefox"),
                Path("snap/firefox/common/.cache/mozilla/firefox")]
    if cache is not None:
        profiles.append(cache / "mozilla/firefox")
    starts = {"{profiles}": profiles, "{cache}": [cache], "{data}": [roots["data"]]}
    listings = {}
    for kind, rule in RULES.items():
        first, *parts = rule.folder.split("/")
        paths = [p for p in starts.get(first, [Path(first)]) if p is not None]
        for part in parts:
            if part not in COMPONENTS:
                paths = [path / part for path in paths]
                continue
            children = []
            for path in paths:
                if path not in listings:
                    listings[path] = directories(home, path, warnings)
                children.extend(path / name for name in listings[path] if re.fullmatch(COMPONENTS[part], name))
            paths = children
        for path in paths:
            yield path, kind, re.compile(rule.filename)


def firefox_http(fd, size, name):
    if size < 41:
        return False
    data_end = int.from_bytes(os.pread(fd, 4, size - 4), "big")
    # cache2 plaintext v4: data, metadata hash, one uint16 per 256 KiB,
    # eight big-endian header words, NUL-terminated key, metadata, trailer.
    header_pos = data_end + 4 + 2 * ((data_end + 262143) // 262144)
    header = os.pread(fd, 32, header_pos)
    if len(header) != 32:
        return False
    version, _, _, _, _, _, length, _ = struct.unpack(">8I", header)
    if version != 4 or not 0 < length <= 16384 or header_pos + 32 + length + 1 > size - 4:
        return False
    key = os.pread(fd, length + 1, header_pos + 32)
    return key.endswith(b"\0") and hashlib.sha1(key[:-1], usedforsecurity=False).hexdigest().upper() == name


def matches(kind, fd, info, folder, match):
    if kind == "firefox_http":
        return firefox_http(fd, info.st_size, match[0])
    if kind == "go":
        action = match[0][:-2].encode()
        return (folder.name == match[0][:2] and info.st_size == 175 and
                re.fullmatch(b"v1 " + action + rb" [0-9a-f]{64} +[0-9]+ +[0-9]+\n", os.pread(fd, 175, 0)) is not None)
    if kind == "matplotlib":
        if info.st_size > 4 * 1024 * 1024:
            return False
        try:
            data = json.loads(os.pread(fd, info.st_size, 0))
        except (ValueError, RecursionError):
            return False
        return (isinstance(data, dict) and data.get("__class__") == "FontManager"
                and str(data.get("_version")) == match[1] and isinstance(data.get("ttflist"), list)
                and isinstance(data.get("afmlist"), list))
    signature = RULES[kind].signature
    if os.pread(fd, len(signature), 0) != signature:
        return False
    if signature == ZIP:
        with os.fdopen(os.dup(fd), "rb") as stream:
            return zipfile.is_zipfile(stream)
    return True
