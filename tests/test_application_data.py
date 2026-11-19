import os
from pathlib import Path
import py_compile
import tempfile
import unittest
from unittest.mock import patch

from xquasar.cleaner import apply, open_home, scan


class ApplicationData(unittest.TestCase):
    def setUp(self):
        self.root = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.home = self.enterContext(open_home(self.root))
        self.enterContext(patch.dict(os.environ, {
            key: str(self.root / rel) for key, rel in [
                ("XDG_CONFIG_HOME", ".config"), ("XDG_DATA_HOME", ".local/share"),
                ("XDG_CACHE_HOME", ".cache"), ("XDG_STATE_HOME", ".local/state"),
            ]
        }))

    def make(self, path, data=b""):
        dest = self.root / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        return dest

    def test_cache_signatures_across_roots_and_profiles(self):
        header = bytes.fromhex("305c72a71b6dfbfc")
        valid = [self.make(folder + "/a1234567890bcdef_0", header + bytes(24)) for folder in [
            ".config/Editor/Cache/Cache_Data", ".local/share/Client/Code Cache/js",
            ".local/state/Desk/Code Cache/wasm", ".cache/chromium/Profile 2/Cache/Cache_Data",
        ]]
        valid.append(self.make(".thumbnails/normal/" + "b" * 32 + ".png", b"\x89PNG\r\n\x1a\n"))
        keep = [self.make(".config/Editor/Cache/Cache_Data/11234567890bcdef_0", b"settings"),
                self.make(".config/Editor/Local Storage/a1234567890bcdef_0", header),
                self.make(".local/share/Trash/files/Cache/Cache_Data/a1234567890bcdef_0", header),
                self.make("Documents/Editor/Code Cache/js/a1234567890bcdef_0", header)]
        items, warnings = scan(self.home)
        self.assertEqual(warnings, [])
        self.assertEqual({self.root / item.path for item in items}, set(valid))
        done, warnings, _ = apply(self.home, items)
        self.assertEqual((done, warnings), (items, []))
        self.assertTrue(all(p.is_file() for p in keep))
        self.assertTrue(all(not p.exists() for p in valid))
        self.assertTrue(valid[0].parent.is_dir())
        self.assertFalse(valid[1].parent.exists())

    def test_only_reproducible_local_python_cache_is_cleaned(self):
        source = self.make(".local/lib/python3.12/site-packages/pkg/sub/tool.py", b"value = True")
        bytecode = Path(py_compile.compile(str(source), doraise=True))
        other = self.make(bytecode.parent / "mystery.pyc", b"unknown")
        items, warnings = scan(self.home)
        self.assertEqual(warnings, [])
        self.assertEqual([self.root / i.path for i in items], [bytecode])
        source.rename(source.with_suffix(".saved"))
        done, warnings, _ = apply(self.home, items)
        self.assertFalse(done)
        self.assertTrue(warnings)
        self.assertTrue(bytecode.is_file())
        source.with_suffix(".saved").rename(source)
        items, _ = scan(self.home)
        self.assertEqual(apply(self.home, items)[:2], (items, []))
        self.assertTrue(other.is_file())
        other.unlink()
        py_compile.compile(str(source), doraise=True)
        items, _ = scan(self.home)
        self.assertEqual(apply(self.home, items)[:2], (items, []))
        self.assertFalse(bytecode.parent.exists())
        self.assertTrue(source.is_file())

    def test_only_verified_removed_flatpak_launchers_are_moved(self):
        def entry(name):
            return f"[Desktop Entry]\nType=Application\nX-Flatpak={name}\nExec=/usr/bin/flatpak run --branch=stable {name} %U\n".encode()
        gone = "org.example.Gone"
        keep = "org.example.Kept"
        saved = [self.make(folder + "/" + gone + ".desktop", entry(gone)) for folder in [
            ".config/autostart", ".local/share/applications"]]
        active = self.make(".config/autostart/" + keep + ".desktop", entry(keep))
        unknown = self.make(".local/share/applications/org.example.Custom.desktop", entry("org.example.Custom").replace(b"/usr/bin/flatpak", b"/opt/wrapper"))
        with patch("xquasar.cleaner.installed_apps", return_value={keep}):
            items, warnings = scan(self.home)
            self.assertEqual(warnings, [])
            self.assertEqual({self.root / i.path for i in items}, set(saved))
            with patch("xquasar.cleaner.installed_apps", return_value={keep, gone}):
                self.assertFalse(apply(self.home, items)[0])
            done, warnings, session = apply(self.home, items)
        self.assertEqual((done, warnings), (items, []))
        self.assertTrue(active.is_file() and unknown.is_file())
        for f in saved:
            self.assertFalse(f.exists())
            self.assertEqual((self.root / session / f.relative_to(self.root)).read_bytes(), entry(gone))

    def test_external_and_linked_roots_are_skipped(self):
        target = self.make("Documents/Editor/Cache/Cache_Data/aaaaaaaaaaaaaaaa_0",
                           bytes.fromhex("305c72a71b6dfbfc"))
        (self.root / ".config").symlink_to(target.parents[3])
        with patch.dict(os.environ, {"XDG_DATA_HOME": str(self.root.parent), "XDG_CACHE_HOME": str(self.root)}):
            self.assertFalse(scan(self.home)[0])
        self.assertTrue(target.is_file())

    def test_relocated_xdg_cache_preserves_new_entries_and_filters_aliases(self):
        folder = "custom/Editor/Code Cache/js/"
        target = self.make(folder + "1234567890abcdef_0", bytes.fromhex("305c72a71b6dfbfc"))
        with patch.dict(os.environ, {"XDG_CONFIG_HOME": str(self.root / "custom"),
                                     "XDG_DATA_HOME": str(self.root / "custom")}):
            items, warnings = scan(self.home)
            self.assertEqual(warnings, [])
            self.assertEqual([self.root / i.path for i in items], [target])
            keep = self.make(folder + "new-file", b"new data")
            self.assertEqual(apply(self.home, items)[:2], (items, []))
            self.assertFalse(target.exists())
            self.assertTrue(keep.is_file())
            self.assertEqual(scan(self.home), ([], []))

    def test_unknown_flatpak_inventory_skips_launcher_and_keeps_cache_actionable(self):
        app = "org.example.Unknown"
        launcher = self.make(".config/autostart/" + app + ".desktop",
                             f"[Desktop Entry]\nType=Application\nX-Flatpak={app}\nExec=flatpak run {app}\n".encode())
        target = self.make(".config/Editor/Code Cache/js/1234567890abcdef_0", bytes.fromhex("305c72a71b6dfbfc"))
        with patch("xquasar.cleaner.installed_apps", side_effect=OSError("unavailable")):
            items, warnings = scan(self.home)
            self.assertTrue(warnings)
            self.assertEqual([self.root / i.path for i in items], [target])
            self.assertEqual(apply(self.home, items)[:2], (items, []))
        self.assertTrue(launcher.is_file())
