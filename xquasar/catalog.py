"""Bounded, format-specific rules for regenerable application caches."""

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import struct
import tarfile
import zlib
import zipfile

from .app_data import directories


@dataclass(frozen=True)
class Rule:
    label: str
    folder: str | tuple[str, ...]
    filename: str
    signature: bytes = b""


# Templates start at an in-home XDG root or at a fixed home-relative location.
# Each variable consumes exactly one directory component.
PROFILE = "{cache}/mozilla/firefox/{profile}/"
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
    "go_output": Rule("Go build outputs", "{cache}/go-build/{hh}", r"([a-f0-9]{64})-d"),
    "gradle": Rule("Gradle dependency archives", ".gradle/caches/modules-2/files-2.1/{coord}/{coord}/{coord}/{sha1}",
                   r"[A-Za-z0-9_.+-]+\.(?:jar|aar|war|zip|klib)", ZIP),
    "electron_download": Rule("Electron downloads", "{cache}/electron/{sha256}",
                              r"electron-(v[0-9]+\.[0-9]+\.[0-9]+)-linux-(?:x64|ia32|arm64|armv7l)\.zip", ZIP),
    "pip_http": Rule("pip HTTP archives", "{cache}/pip/http-v2/{h}/{h}/{h}/{h}/{h}",
                     r"([a-f0-9]{56})\.body", ZIP),
    "qml": Rule("Qt QML bytecode", ("{cache}/{app}/qmlcache", "{cache}/{app}/{app}/qmlcache"),
                r"[0-9a-f]{40}\.(?:qmlc|jsc|mjsc)", b"qv4cdata"),
    "darktable_thumb": Rule("darktable thumbnails", "{cache}/darktable/{mipmaps}/{level}",
                            r"[0-9]+\.jpg", b"\xff\xd8\xff"),
    "ruby_index": Rule("RubyGems package indexes", ("{cache}/gem/specs/{gemhost}", ".gem/specs/{gemhost}"),
                       r"(?:latest_|prerelease_)?specs\.4\.8", b"\x04\x08["),
    "ruby_spec": Rule("RubyGems specifications", ("{cache}/gem/specs/{gemhost}/quick/Marshal.4.8",
                       ".gem/specs/{gemhost}/quick/Marshal.4.8"), r"[\w.-]+-[0-9][\w.-]*\.gemspec",
                      b"\x04\x08u:\x17Gem::Specification"),
    "thunderbird_http": Rule("Thunderbird HTTP", "{cache}/thunderbird/{profile}/cache2/entries", r"[A-F0-9]{40}"),
    "thunderbird_startup": Rule("Thunderbird startup", "{cache}/thunderbird/{profile}/startupCache",
                                r"startupCache\.[48]\.(?:little|big)", b"startupcache0002\0"),
    "cabal": Rule("Cabal source archives", (".cabal/packages/hackage.haskell.org/{coord}/{version}",
                  "{cache}/cabal/packages/hackage.haskell.org/{coord}/{version}"), r"[A-Za-z0-9-]+-[0-9.]+\.tar\.gz", GZIP),
    "helm_index": Rule("Helm repository indexes", "{cache}/helm/repository", r"[A-Za-z0-9_.-]+-index\.yaml"),
    "composer_metadata": Rule("Composer package metadata", "{cache}/composer/repo/https---repo.packagist.org",
                              r"provider-([a-z0-9_.-]+)\$([a-z0-9_.-]+)(?:~dev)?\.json"),
    "nuget_versions": Rule("NuGet version lists", "{data}/NuGet/v3-cache/{feed}", r"list_[a-z0-9._-]+\.dat"),
}
TOOL_PROCESSES = {
    "cabal": ("cabal",), "helm_index": ("helm",), "composer_metadata": ("composer", "composer.phar"),
    "nuget_versions": ("dotnet", "nuget"), "go_output": ("go",), "gradle": ("gradle", "gradlew"), "electron_download": ("electron", "npm", "yarn", "pnpm", "node"),
    "pip_http": ("pip", "pip3"), "darktable_thumb": ("darktable", "darktable-generate-cache", "darktable-cli"),
    "ruby_index": ("gem", "bundle", "bundler", "ruby"), "ruby_spec": ("gem", "bundle", "bundler", "ruby"),
}
DOWNLOADS = {"pip", "cargo", "nuget", "npm", "composer", "gradle", "electron_download", "pip_http", "ruby_index", "ruby_spec",
             "cabal", "helm_index", "composer_metadata", "nuget_versions"}

COMPONENTS = {
    "{profile}": r"[^./][^/]*", "{app}": r"[\w.-]+", "{hh}": r"[a-f0-9]{2}",
    "{wheelhash}": r"[a-f0-9]{50}", "{crates}": r"(?:index\.crates\.io|github\.com)-[0-9a-f]{16}",
    "{package}": r"[a-z0-9][a-z0-9_.-]*", "{feed}": r"[a-fA-F0-9]{40}\$[^/]+",
    "{version}": r"[0-9]+(?:\.[0-9]+)*", "{h}": r"[0-9a-f]", "{coord}": r"[a-zA-Z0-9][a-zA-Z0-9_.+-]*",
    "{sha1}": r"[0-9a-f]{40}", "{sha256}": r"[0-9a-f]{64}",
    "{mipmaps}": r"mipmaps-[0-9a-f]{40}\.d", "{level}": r"[0-8]",
    "{gemhost}": r"[a-zA-Z0-9.-]+%[0-9]{1,5}",
}


def folders(home, roots, warnings, *, host=True):
    starts = {"{cache}": roots["cache"], "{data}": roots["data"]}
    listings = {}
    for kind, rule in RULES.items():
        layouts = (rule.folder,) if isinstance(rule.folder, str) else rule.folder
        for layout in layouts:
            first, *parts = layout.split("/")
            root = starts.get(first, Path(first) if host else None)
            if root is None:
                continue
            paths = [root]
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


def digest_matches(fd, size, algorithm, expected):
    if not 0 < size <= 64 * 1024 * 1024:
        return False
    digest = hashlib.new(algorithm, usedforsecurity=False)
    offset = 0
    while offset < size:
        chunk = os.pread(fd, min(1024 * 1024, size - offset), offset)
        if not chunk:
            return False
        digest.update(chunk)
        offset += len(chunk)
    return digest.hexdigest() == expected


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


def cabal_archive(fd, folder, name):
    base = f"{folder.parent.name}-{folder.name}"
    if name != base + ".tar.gz":
        return False
    try:
        header = zlib.decompressobj(31).decompress(os.pread(fd, 65536, 0), tarfile.BLOCKSIZE)
        if len(header) != tarfile.BLOCKSIZE:
            return False
        member = tarfile.TarInfo.frombuf(header, "utf-8", "strict")
        return member.name == base or member.name.startswith(base + "/")
    except (ValueError, tarfile.HeaderError, zlib.error):
        return False


def cache_json(fd, size):
    if size > 4 * 1024 * 1024:
        return {}
    try:
        data = json.loads(os.pread(fd, size, 0))
        return data if isinstance(data, dict) else {}
    except (ValueError, RecursionError):
        return {}


def matches(kind, fd, info, folder, match):
    if kind in {"firefox_http", "thunderbird_http"}:
        return firefox_http(fd, info.st_size, match[0])
    if kind == "go":
        action = match[0][:-2].encode()
        return (folder.name == match[0][:2] and info.st_size == 175 and
                re.fullmatch(b"v1 " + action + rb" [0-9a-f]{64} +[0-9]+ +[0-9]+\n", os.pread(fd, 175, 0)) is not None)
    if kind == "matplotlib":
        data = cache_json(fd, info.st_size)
        return (data.get("__class__") == "FontManager"
                and str(data.get("_version")) == match[1] and isinstance(data.get("ttflist"), list)
                and isinstance(data.get("afmlist"), list))
    if kind == "cabal":
        return cabal_archive(fd, folder, match[0])
    if kind == "helm_index":
        return re.match(rb"apiVersion: v1\r?\nentries:\s*\n  [A-Za-z0-9_.-]+:", os.pread(fd, 4096, 0)) is not None
    if kind == "composer_metadata":
        name = f"{match[1]}/{match[2]}"
        packages = cache_json(fd, info.st_size).get("packages")
        versions = packages.get(name) if isinstance(packages, dict) else None
        return (isinstance(versions, list) and bool(versions) and isinstance(versions[0], dict)
                and versions[0].get("name") == name and isinstance(versions[0].get("version"), str))
    if kind == "nuget_versions":
        versions = cache_json(fd, info.st_size).get("versions")
        return isinstance(versions, list) and bool(versions) and all(
            isinstance(v, str) and re.fullmatch(r"[0-9]+(?:\.[0-9]+){1,3}(?:[-+][A-Za-z0-9.+-]+)?", v) for v in versions)
    if kind == "go_output":
        return folder.name == match[1][:2] and digest_matches(fd, info.st_size, "sha256", match[1])
    if kind == "gradle":
        version, artifact = folder.parent.name, folder.parent.parent.name
        base = f"{artifact}-{version}"
        if not (match[0].startswith((base + ".", base + "-")) and digest_matches(fd, info.st_size, "sha1", folder.name)):
            return False
    if kind == "electron_download":
        url = "https://github.com/electron/electron/releases/download/" + match[1]
        if folder.name != hashlib.sha256(url.encode()).hexdigest():
            return False
    if kind == "pip_http" and "".join(folder.parts[-5:]) != match[1][:5]:
        return False
    if kind == "qml":
        header = os.pread(fd, 28, 0)
        if (len(header) != 28 or info.st_size < 128 or header[14] not in (5, 6)
                or int.from_bytes(header[24:28], "little") != info.st_size):
            return False
    if kind == "darktable_thumb" and (info.st_size < 20 or os.pread(fd, 2, info.st_size - 2) != b"\xff\xd9"):
        return False
    signature = RULES[kind].signature
    if os.pread(fd, len(signature), 0) != signature:
        return False
    if signature == ZIP:
        with os.fdopen(os.dup(fd), "rb") as stream:
            return zipfile.is_zipfile(stream)
    return True
