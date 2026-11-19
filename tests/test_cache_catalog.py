import hashlib
from io import BytesIO
import os
from pathlib import Path
import struct
import tempfile
import unittest
import zipfile
from unittest.mock import patch

from xquasar.cleaner import apply, open_home, scan


def example_files():
    key = b":https://example.invalid/cache"
    name = hashlib.sha1(key).hexdigest().upper()
    entry = b"data" + bytes(6) + struct.pack(">8I", 4, 1, 0, 0, 0, 0, len(key), 0) + key + b"\0" + struct.pack(">I", 4)
    fox = ".cache/mozilla/firefox/sample.default/"
    ff = fox + "startupCache/"
    action = "ab" * 32
    archive = BytesIO()
    with zipfile.ZipFile(archive, "w") as package:
        package.writestr("demo/metadata", "from test fixture")
    zip_data = archive.getvalue()
    return [
        ("firefox_http", fox + "cache2/entries/" + name, entry),
        ("firefox_startup", ff + "startupCache.8.little", b"startupcache0002\0" + bytes(32)),
        ("firefox_script", ff + "scriptCache-child-current.bin", b"mozXDRcachev003\0" + bytes(32)),
        ("firefox_url", ff + "urlCache.bin", b"mozURLcachev003\0" + bytes(32)),
        ("firefox_webext", ff + "webext.sc.lz4", b"mozJSSCLz40v001\0" + bytes(32)),
        ("failed_thumbnail", ".cache/thumbnails/fail/gnome-thumbnail-factory/" + "a"*32 + ".png", b"\x89PNG\r\n\x1a\n"),
        ("gstreamer", ".cache/gstreamer-1.0/registry.x86_64.bin", b"\xc0\xde\xf0\x0d1.23.90\0" + bytes(80)),
        ("matplotlib", ".cache/matplotlib/fontlist-v390.json", b'{"_version":390,"__class__":"FontManager","ttflist":[],"afmlist":[]}'),
        ("pip", ".cache/pip/wheels/aa/bb/cc/" + "d"*50 + "/demo-1.0-py3-none-any.whl", zip_data),
        ("npm", ".npm/_cacache/content-v2/sha512/aa/bb/" + "c"*124, b"\x1f\x8b\x08" + bytes(32)),
        ("cargo", ".cargo/registry/cache/index.crates.io-1949cf8c6b5b557f/demo-1.0.0.crate", b"\x1f\x8b\x08" + bytes(32)),
        ("composer", ".cache/composer/files/org/demo/" + "a"*40 + ".zip", zip_data),
        ("nuget", ".local/share/NuGet/v3-cache/" + "a"*40 + "$ps_api.nuget.org_v3_index.json/nupkg_demo.1.0.dat", zip_data),
        ("go", ".cache/go-build/ab/" + action + "-a", f"v1 {action} {'f'*64} {50:20} {128:20}\n".encode()),
    ]


class CacheCatalog(unittest.TestCase):
    def setUp(self):
        self.root = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.home = self.enterContext(open_home(self.root))
        self.enterContext(patch.dict(os.environ, {
            "XDG_CACHE_HOME": str(self.root / ".cache"), "XDG_DATA_HOME": str(self.root / ".local/share"),
            "XDG_CONFIG_HOME": str(self.root / ".config"), "XDG_STATE_HOME": str(self.root / ".local/state"),
        }))

    def write(self, path, data):
        p = self.root / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
        return p

    def test_preview_and_confirm_all_formats(self):
        expected = {}
        for kind, path, data in example_files():
            self.write(path, data)
            expected[Path(path)] = kind
        items, warnings = scan(self.home)
        self.assertFalse(warnings)
        self.assertEqual({i.path: i.kind for i in items}, expected)
        self.assertTrue(all(i.is_cache for i in items))
        self.assertEqual(apply(self.home, items)[:2], (items, []))
        self.assertTrue(all(not (self.root / p).exists() for p in expected))
        self.assertEqual(scan(self.home), ([], []))

    def test_unrecognised_content_and_names_remain(self):
        for kind, path, data in example_files():
            self.write(path, b"not a generated cache")
            self.write(path + ".save", data)
        self.assertEqual(scan(self.home), ([], []))

    def test_truncated_package_archives_are_kept(self):
        for kind, path, data in example_files():
            if kind in {"pip", "composer", "nuget"}:
                self.write(path, data[:-30])
        self.assertFalse(scan(self.home)[0])

    def test_file_changed_since_preview_and_symlinked_cache_are_kept(self):
        _, path, data = example_files()[1]
        p = self.write(path, data)
        items, _ = scan(self.home)
        self.assertEqual(len(items), 1)
        p.write_bytes(b"user data")
        self.assertFalse(apply(self.home, items)[0])
        p.parent.rename(self.root / "Documents")
        p.parent.symlink_to(self.root / "Documents")
        self.assertFalse(scan(self.home)[0])
        self.assertEqual(p.read_bytes(), b"user data")

    def test_corrupt_firefox_offsets_and_font_metadata_do_not_authorize_cleanup(self):
        _, fox, data = example_files()[0]
        self.write(fox, data[:-4] + bytes([255])*4)
        self.write(".cache/matplotlib/fontlist-v390.json", b'{"_version":391,"__class__":"FontManager"}')
        self.assertFalse(scan(self.home)[0])
        self.write(fox, data.replace(b"example", b"replaced"))
        self.assertFalse(scan(self.home)[0])
