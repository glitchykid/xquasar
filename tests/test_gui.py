import os
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

    def select(self, path):
        index = next(i for i, row in enumerate(self.window.model) if row[1] == path)
        self.window.toggle.emit("toggled", str(index))

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

    def test_preview_selection_cancel_and_confirm(self):
        self.assertTrue(self.empty.exists())
        self.assertFalse(self.window.clean_button.get_sensitive())
        self.select("work")
        self.assertTrue(self.window.clean_button.get_sensitive())
        self.confirm(Gtk.ResponseType.CANCEL)
        self.assertTrue(self.empty.exists())
        self.confirm(Gtk.ResponseType.OK)
        self.assertFalse(self.empty.exists())
        self.assertFalse(self.window.clean_button.get_sensitive())
        self.assertIn("1", self.window.status.get_text())

    def test_manual_folder_and_recovery(self):
        self.window.include_folder(self.app)
        self.idle()
        self.select(".config/OldEditor")
        self.confirm(Gtk.ResponseType.OK)
        recovered, = (self.home / ".xquasar-recovery").glob("*/.config/OldEditor/profile")
        self.assertEqual(recovered.read_text(), "keep")
        self.assertTrue(self.empty.exists())
        self.assertTrue(self.window.recovery_button.get_visible())

    def test_changed_item_and_partial_scan(self):
        self.select("work")
        (self.empty / "new").touch()
        self.confirm(Gtk.ResponseType.OK)
        self.assertTrue((self.empty / "new").exists())
        self.assertTrue(self.window.details.get_visible())
        self.window.rescan_button.clicked()
        self.idle()
        self.assertEqual(len(self.window.model), 0)
        self.assertFalse(self.window.clean_button.get_sensitive())

    def test_incomplete_scan_offers_retry(self):
        self.empty.rmdir()
        (self.home / ".var/app/org.example.Unknown").mkdir(parents=True)
        with patch.dict(os.environ, {"PATH": ""}):
            self.window.rescan_button.clicked()
            self.idle()
        self.assertEqual(self.window.status.get_text(), "Scan incomplete")
        self.assertTrue(self.window.details.get_visible())
        self.assertTrue(self.window.rescan_button.get_sensitive())
        self.assertFalse(self.window.clean_button.get_sensitive())
