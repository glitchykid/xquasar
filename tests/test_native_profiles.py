import gzip
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from xquasar import activity, native
from xquasar.cleaner import apply, open_home, scan


class NativeProfiles(unittest.TestCase):
    def setUp(self):
        self.temp = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.root = self.temp / "home"
        self.root.mkdir()
        self.home = self.enterContext(open_home(self.root))
        self.proc = self.temp / "proc"
        self.proc.mkdir()
        self.observe(os.getpid())
        self.enterContext(patch.object(activity, "PROC", self.proc))
        self.logs = self.temp / "log"
        self.logs.mkdir()
        self.enterContext(patch.object(native, "APT_LOGS", self.logs))
        self.db = self.enterContext(patch.object(native, "dpkg_states", return_value=(set(), set())))
        self.snaps = self.enterContext(patch.object(native, "snap_state", return_value=(set(), set())))
        self.enterContext(patch.object(native, "available_command", return_value=False))
        self.enterContext(patch("xquasar.cleaner.installed_apps", return_value=set()))
        self.enterContext(patch.dict(os.environ, {
            "XDG_CONFIG_HOME": str(self.root / ".config"), "XDG_CACHE_HOME": str(self.root / ".cache"),
            "XDG_DATA_HOME": str(self.root / ".local/share"), "XDG_STATE_HOME": str(self.root / ".local/state"),
        }))

    def observe(self, pid):
        (self.proc / str(pid)).symlink_to(Path("/proc") / str(pid))

    def folder(self, path):
        folder = self.root / path
        folder.mkdir(parents=True)
        return folder

    def removed(self, name):
        with gzip.open(self.logs / "history.log.1.gz", "wt") as log:
            log.write(f"Start-Date: 2026-01-01  10:00:00\nRemove: {name}:amd64 (1.0)\nEnd-Date: 2026-01-01  10:01:00\n")

    def test_verified_apt_profiles_move_intact_but_similar_names_stay(self):
        self.removed("qbittorrent")
        paths = [".config/qBittorrent", ".local/share/qBittorrent"]
        for path in paths:
            (self.folder(path) / "settings").write_text("personal data")
        keep = self.folder(".config/qBittorrent-extra")
        items, warnings = scan(self.home)
        self.assertFalse(warnings)
        self.assertEqual({(i.kind, str(i.path)) for i in items}, {("apt", p) for p in paths})
        done, warnings, session = apply(self.home, items)
        self.assertEqual((done, warnings), (items, []))
        for path in paths:
            self.assertEqual((self.root / session / path / "settings").read_text(), "personal data")
        self.assertTrue(keep.exists())

    def test_apt_requires_history_and_rechecks_other_installations(self):
        profile = self.folder(".config/qBittorrent")
        self.assertFalse(scan(self.home)[0])
        (self.logs / "history.log").write_text("Start-Date: now\nPurge: qbittorrent:amd64 (1)\n")
        self.assertFalse(scan(self.home)[0])
        self.removed("qbittorrent")
        items, _ = scan(self.home)
        self.assertEqual(len(items), 1)
        self.db.return_value = ({"qbittorrent-nox"}, set())
        self.assertFalse(apply(self.home, items)[0])
        self.db.return_value = (set(), set())
        self.snaps.return_value = ({"qbittorrent_alt"}, set())
        self.assertFalse(scan(self.home)[0])
        self.snaps.return_value = (set(), set())
        with patch("xquasar.cleaner.installed_apps", return_value={"org.qbittorrent.qBittorrent"}):
            self.assertFalse(scan(self.home)[0])
        self.assertTrue(profile.exists())

    def test_snap_requires_known_removal_and_skips_reinstalled_instance(self):
        self.folder("snap/demo_alt/common")
        self.folder(".snap/data/demo_alt/42")
        self.folder("snap/demo/common")
        self.folder("snap/notes/project")
        self.assertFalse(scan(self.home)[0])
        self.snaps.return_value = ({"demo"}, {"demo_alt", "demo", "notes"})
        items, _ = scan(self.home)
        self.assertEqual({str(i.path) for i in items}, {"snap/demo_alt", ".snap/data/demo_alt"})
        self.snaps.return_value = ({"demo_alt"}, {"demo_alt"})
        self.assertFalse(apply(self.home, items)[0])
        self.snaps.return_value = (set(), {"demo_alt"})
        self.assertEqual(apply(self.home, items)[:2], (items, []))

    def test_real_process_using_profile_protects_directory_and_sibling_cache(self):
        self.removed("vlc")
        config = self.folder(".config/vlc")
        cache = self.folder(".cache/vlc/Code Cache/js") / ("a" * 16 + "_0")
        cache.write_bytes(bytes.fromhex("305c72a71b6dfbfc"))
        items, _ = scan(self.home)
        self.assertTrue(any(i.kind == "apt" for i in items))
        with subprocess.Popen(["/bin/sleep", "60"], cwd=config) as child:
            try:
                self.observe(child.pid)
                self.assertFalse(scan(self.home)[0])
                self.assertFalse(apply(self.home, items)[0])
            finally:
                child.terminate()
        self.assertTrue(config.exists() and cache.exists())

    def test_running_firefox_protects_old_cache_rules(self):
        folder = self.folder(".cache/mozilla/firefox/test.default/startupCache")
        cache = folder / "startupCache.8.little"
        cache.write_bytes(b"startupcache0002\0" + bytes(32))
        items, _ = scan(self.home)
        self.assertEqual(len(items), 1)
        with subprocess.Popen(["firefox", "60"], executable="/bin/sleep") as child:
            try:
                self.observe(child.pid)
                self.assertFalse(scan(self.home)[0])
                self.assertFalse(apply(self.home, items)[0])
            finally:
                child.terminate()
        self.assertTrue(cache.exists())

    def test_unknown_package_state_and_linked_profile_are_skipped(self):
        profile = self.folder(".config/vlc")
        (self.folder(".cache") / "vlc").symlink_to(profile, target_is_directory=True)
        self.db.return_value = (set(), {"vlc"})
        items, _ = scan(self.home)
        self.assertEqual([str(i.path) for i in items], [".config/vlc"])
        self.db.side_effect = OSError("incomplete dpkg inventory")
        self.assertTrue(scan(self.home)[1])
        self.assertFalse(apply(self.home, items)[0])
        self.assertTrue(profile.exists())

    def test_failed_apt_transaction_and_concurrent_snap_install_are_hidden(self):
        self.folder(".config/mpv")
        (self.logs / "history.log").write_text(
            "Start-Date: now\nRemove: mpv:amd64 (1.0)\nError: transaction failed\nEnd-Date: now\n")
        self.assertFalse(scan(self.home)[0])
        self.snaps.return_value = (set(), {"mpv"})
        self.assertEqual([i.kind for i in scan(self.home)[0]], ["snap"])
        self.snaps.side_effect = OSError("inventory unavailable")
        self.assertFalse(scan(self.home)[0])

    def test_open_file_identifies_app_even_when_process_name_differs(self):
        self.removed("filezilla")
        settings = self.folder(".filezilla") / "settings"
        settings.write_text("keep")
        self.folder(".config/filezilla")
        with settings.open() as handle, subprocess.Popen(
                ["/bin/sleep", "60"], pass_fds=(handle.fileno(),)) as child:
            try:
                self.observe(child.pid)
                self.assertFalse(scan(self.home)[0])
            finally:
                child.terminate()
