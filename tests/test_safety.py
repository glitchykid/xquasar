import os
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from xquasar.cleaner import apply, open_home, scan


class Safety(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.home = Path(temporary.name) / "home"
        self.home.mkdir()
        self.enterContext(patch.dict(os.environ, {
            "XDG_CONFIG_HOME": str(self.home / ".config"),
            "XDG_CACHE_HOME": str(self.home / ".cache"),
        }))

    def test_changed_file_and_parent_replacement_are_skipped(self):
        folder = self.home / ".cache/thumbnails/normal"
        folder.mkdir(parents=True)
        thumbnail = folder / ("c" * 32 + ".png")
        thumbnail.touch()
        work = self.home / "work"
        (work / "empty").mkdir(parents=True)
        with open_home(self.home) as home:
            items, warnings = scan(home, [])
            self.assertEqual(warnings, [])
            thumbnail.write_bytes(b"replaced since preview")
            moved = self.home.parent / "moved"
            work.rename(moved)
            work.symlink_to(moved)
            done, warnings, _ = apply(home, items)
            self.assertEqual(done, [])
            self.assertEqual(len(warnings), 2)
            self.assertTrue((work / "empty").is_dir())
            self.assertTrue(thumbnail.exists())

    def test_customized_xdg_folder_and_linked_thumbnail_remain(self):
        (self.home / ".config").mkdir()
        (self.home / ".config/user-dirs.dirs").write_text(
            'XDG_DOWNLOAD_DIR="$HOME/Загрузки"\n'
        )
        (self.home / "Загрузки").mkdir()
        outside = self.home.parent / "picture"
        outside.touch()
        normal = self.home / ".cache/thumbnails/normal"
        normal.mkdir(parents=True)
        (normal / ("d" * 32 + ".png")).symlink_to(outside)
        with open_home(self.home) as home:
            self.assertEqual(scan(home, []), ([], []))

    def test_custom_cache_folder_outside_home_is_skipped(self):
        outside = self.home.parent / "cache"
        normal = outside / "thumbnails/normal"
        normal.mkdir(parents=True)
        (normal / ("e" * 32 + ".png")).touch()
        with patch.dict(os.environ, {"XDG_CACHE_HOME": str(outside)}), open_home(self.home) as home:
            self.assertEqual(scan(home, []), ([], []))

    def test_quoted_xdg_folder_with_comment_is_preserved(self):
        (self.home / ".config").mkdir()
        (self.home / ".config/user-dirs.dirs").write_text(
            r'XDG_DOWNLOAD_DIR="$HOME/My \"files\"" # local downloads' + "\n"
        )
        (self.home / 'My "files"').mkdir()
        with open_home(self.home) as home:
            self.assertEqual(scan(home, []), ([], []))

    def test_empty_directories_in_custom_xdg_data_roots_are_protected(self):
        (self.home / "Cache/active-app").mkdir(parents=True)
        with patch.dict(os.environ, {"XDG_CACHE_HOME": str(self.home / "Cache")}):
            with open_home(self.home) as home:
                self.assertEqual(scan(home, []), ([], []))

    def test_irrelevant_entry_does_not_hide_real_flatpak_orphan(self):
        base = self.home / ".var/app"
        base.mkdir(parents=True)
        (base / "org.example.Link").symlink_to(self.home)
        (base / "org.example.File").touch()
        (base / "org.example.Gone").mkdir()
        with patch("xquasar.cleaner.installed_apps", return_value=set()), open_home(self.home) as home:
            items, warnings = scan(home, [])
            self.assertEqual([i.path.name for i in items], ["org.example.Gone"])
            self.assertEqual(warnings, [])

    @unittest.skipUnless(shutil.which("flatpak"), "Flatpak CLI unavailable")
    def test_real_flatpak_inventory_and_recovery_in_an_isolated_home(self):
        # The synthetic ID is deliberately unique to this test, in either installation.
        target = self.home / ".var/app/org.example.XQuasarFixture"
        target.mkdir(parents=True)
        env = {**os.environ, "HOME": str(self.home), "XDG_DATA_HOME": str(self.home / ".local/share")}
        result = subprocess.run(
            [sys.executable, "-m", "xquasar", "--clean"], input="all\nyes\n", text=True,
            env=env, capture_output=True, timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(target.exists())
        self.assertEqual(len(list((self.home / ".xquasar-recovery").glob("*/.var/app/" + target.name))), 1)
