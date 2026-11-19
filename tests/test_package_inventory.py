import http.server
import json
from pathlib import Path
import shutil
import socketserver
import subprocess
import tempfile
import threading
import unittest
from unittest.mock import patch

from xquasar import activity, native
from xquasar.cleaner import apply, open_home, scan


class Inventories(unittest.TestCase):
    def setUp(self):
        self.stage = Path(self.enterContext(tempfile.TemporaryDirectory()))

    @unittest.skipUnless(shutil.which("dpkg-query"), "dpkg-query required")
    def test_real_dpkg_database_with_two_architectures(self):
        entries = [("vlc", "amd64", "deinstall ok config-files"),
                   ("vlc", "arm64", "install ok unpacked"),
                   ("mpv", "amd64", "deinstall ok config-files")]
        (self.stage / "status").write_text("".join(
            f"Package: {p}\nStatus: {s}\nArchitecture: {a}\nMulti-Arch: same\n"
            f"Version: 1.0\nDescription: Test profile\nMaintainer: Test\n\n" for p, a, s in entries))
        with patch.object(native, "DPKG_DB", self.stage):
            self.assertEqual(native.dpkg_states(), ({"vlc"}, {"mpv"}))
        with patch("xquasar.native.subprocess.run", return_value=subprocess.CompletedProcess(
                [], 0, "vlc\tunknown\n", "")):
            with self.assertRaises(OSError):
                native.dpkg_states()

    def test_snap_socket_inactive_revision_pending_reinstall_and_failed_removal(self):
        def change(name, status):
            return {"kind": "remove-snap", "status": status, "ready": status != "Doing",
                    "summary": "操作", "data": {"snap-names": [name]}}
        database = {"snaps": [{"name": "retained", "status": "installed"}],
                    "changes": [change(n, "Done") for n in ["demo_test", "retained", "pending"]]
                    + [change("pending", "Doing"), change("failed", "Error")]}

        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                data = {f"/v2/{k}?select=all": v for k, v in database.items()}[self.path]
                body = json.dumps({"type": "sync", "status-code": 200, "result": data}).encode()
                self.send_response(200)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *args):
                pass

        sock = self.stage / "snapd.socket"
        with patch.object(native, "SNAP_SOCKET", sock), socketserver.UnixStreamServer(str(sock), Handler) as server:
            thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.02})
            thread.start()
            try:
                self.assertEqual(native.snap_state(), ({"pending", "retained"}, {"demo_test"}))
                database["changes"].append({"ready": False, "status": "Doing", "kind": "install-snap"})
                with self.assertRaises(OSError):
                    native.snap_state()
                database["snaps"] = {}
                with self.assertRaises(OSError):
                    native.snap_state()
            finally:
                server.shutdown()
                thread.join()

    def test_process_inventory_failure_prevents_cleanup(self):
        path = self.stage / ".thumbnails/normal" / ("a" * 32 + ".png")
        path.parent.mkdir(parents=True)
        path.write_bytes(b"\x89PNG\r\n\x1a\n")
        with open_home(self.stage) as home:
            items, _ = scan(home)
            self.assertEqual(len(items), 1)
            with patch.object(activity, "PROC", self.stage):
                result, warnings = scan(home)
                self.assertFalse(result)
                self.assertTrue(warnings)
                result, warnings, _ = apply(home, items)
                self.assertFalse(result)
                self.assertTrue(warnings)
        self.assertTrue(path.is_file())
