import os
import shutil
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

try:
    import gi
    gi.require_version("Gtk", "3.0")
    from gi.repository import GLib, Gtk
except (ImportError, ValueError):
    Gtk = None


@unittest.skipUnless(Gtk and Gtk.init_check()[0], "requires GTK 3 and a display")
class DesktopFlow(unittest.TestCase):
    def setUp(self):
        from xquasar.gui import CleanerWindow

        tmp = self.enterContext(tempfile.TemporaryDirectory())
        self.home = Path(tmp)
        self.enterContext(patch.dict(os.environ, {
            "XDG_CONFIG_HOME": str(self.home / ".config"),
            "XDG_CACHE_HOME": str(self.home / ".cache"),
            "LANGUAGE": "en",
        }))
        self.empty = self.home / "work"
        self.empty.mkdir()
        self.app = self.home / ".config/OldEditor"
        self.app.mkdir(parents=True)
        (self.app / "profile").write_text("keep")
        normal = self.home / ".cache/thumbnails/normal"
        normal.mkdir(parents=True)
        self.cache = normal / ("f" * 32 + ".png")
        self.cache.write_bytes(b"\x89PNG\r\n\x1a\n" + bytes(32))
        self.window = CleanerWindow(self.home)
        self.addCleanup(self.window.destroy)
        self.idle()

    def idle(self):
        loop = GLib.MainLoop()
        def ready():
            if self.window.busy:
                return True
            loop.quit()
            return False
        poll = GLib.timeout_add(5, ready)
        timeout = GLib.timeout_add_seconds(10, lambda: loop.quit() or False)
        loop.run()
        if self.window.busy:
            GLib.source_remove(poll)
            self.fail("Window stayed busy")
        GLib.source_remove(timeout)

    def confirm(self, response):
        def answer():
            for dialog in Gtk.Window.list_toplevels():
                if isinstance(dialog, Gtk.MessageDialog) and dialog.get_visible():
                    dialog.response(response)
                    return False
            return True
        GLib.idle_add(answer)
        self.window.clean_button.clicked()
        self.idle()

    def test_no_folder_selection_and_cancel_then_confirm(self):
        self.assertTrue(self.cache.exists())
        self.assertTrue(self.window.clean_button.get_sensitive())
        self.confirm(Gtk.ResponseType.CANCEL)
        self.assertTrue(self.cache.exists())
        self.confirm(Gtk.ResponseType.OK)
        self.assertFalse(self.cache.exists())
        self.assertTrue(self.empty.is_dir())
        self.assertEqual((self.app / "profile").read_text(), "keep")
        self.assertFalse(self.window.clean_button.get_sensitive())

    def test_summary_and_rule_catalog(self):
        self.assertEqual(self.window.cache_total.get_text(), GLib.format_size(self.cache.stat().st_size))
        self.assertTrue(self.window.rows["thumbnail"].get_visible())
        self.assertFalse(self.window.rows["cargo"].get_visible())
        self.window.all_rules.set_active(True)
        self.assertTrue(self.window.rows["cargo"].get_visible())
        self.assertEqual(len(self.window.rows), 22)
        self.window.all_rules.set_active(False)
        self.assertFalse(self.window.rows["cargo"].get_visible())

    @unittest.skipUnless(shutil.which("flatpak"), "Flatpak CLI unavailable")
    def test_auto_detected_profile_moves_to_recovery(self):
        profile = self.home / ".var/app/org.example.XQuasarDesktopFixture"
        profile.mkdir(parents=True)
        (profile / "settings").write_text("saved")
        self.window.rescan_button.clicked()
        self.idle()
        self.assertTrue(self.window.clean_button.get_sensitive())
        self.confirm(Gtk.ResponseType.OK)
        saved, = (self.home / ".xquasar-recovery").glob("*/.var/app/" + profile.name + "/settings")
        self.assertEqual(saved.read_text(), "saved")
        self.assertTrue(self.window.recovery_button.get_visible())
        self.assertTrue(self.app.exists())

    def test_confirmed_snap_shown_and_restorable_from_desktop(self):
        profile = self.home / "snap/test-xquasar/common"
        profile.mkdir(parents=True)
        (profile / "settings").write_text("keep")
        with patch("xquasar.native.snap_state", return_value=(set(), {"test-xquasar"})):
            self.window.rescan_button.clicked()
            self.idle()
            self.assertTrue(self.window.rows["snap"].get_visible())
            self.assertEqual(self.window.counts["snap"].get_text(), "1")
            self.confirm(Gtk.ResponseType.OK)
            self.assertFalse(profile.exists())
            saved, = (self.home / ".xquasar-recovery").glob("*/snap/test-xquasar/common/settings")
            self.assertEqual(saved.read_text(), "keep")

    def test_changed_item_and_rescan(self):
        self.cache.write_bytes(b"new content")
        self.assertTrue(self.window.clean_button.get_sensitive())
        self.confirm(Gtk.ResponseType.OK)
        self.assertTrue(self.cache.exists())
        self.assertTrue(self.window.details.get_visible())
        self.window.rescan_button.clicked()
        self.idle()
        self.assertFalse(self.window.clean_button.get_sensitive())

    def test_application_cache_appears_and_unknown_config_stays_hidden(self):
        file = self.home / ".config/Editor/Code Cache/js/aaaaaaaaaaaaaaaa_0"
        file.parent.mkdir(parents=True)
        file.write_bytes(bytes.fromhex("305c72a71b6dfbfc") + bytes(24))
        self.window.rescan_button.clicked()
        self.idle()
        self.assertTrue(self.window.counts["browser"].get_text().startswith("1"))
        self.window.paths.set_expanded(True)
        buf = self.window.path_text
        preview = buf.get_text(*buf.get_bounds(), True)
        self.assertIn("Code Cache/js", preview)
        self.assertNotIn("OldEditor", preview)
        self.confirm(Gtk.ResponseType.OK)
        self.assertFalse(file.exists())
        self.assertTrue(self.app.is_dir())

    def test_incomplete_scan_offers_retry(self):
        self.cache.unlink()
        (self.home / ".var/app/org.example.Unknown").mkdir(parents=True)
        with patch.dict(os.environ, {"PATH": ""}):
            self.window.rescan_button.clicked()
            self.idle()
        self.assertEqual(self.window.status.get_text(), "Scan incomplete")
        self.assertTrue(self.window.details.get_visible())
        self.assertTrue(self.window.rescan_button.get_sensitive())
        self.assertFalse(self.window.clean_button.get_sensitive())
