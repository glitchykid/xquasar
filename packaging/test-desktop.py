"""Exercise the installed application and its menu entry on an isolated X display."""

import os
from pathlib import Path
import shlex
import subprocess
import tempfile
import unittest

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gio, Gtk

if not Gtk.init_check()[0]:
    raise RuntimeError("Desktop tests require an X display")

desktop = Gio.DesktopAppInfo.new("xquasar.desktop")
if desktop is None:
    raise RuntimeError("XQuasar is missing from the application menu")
command = shlex.split(desktop.get_commandline())
if command != ["/usr/bin/xquasar", "--gui"] or desktop.get_boolean("Terminal"):
    raise RuntimeError("Unexpected application-menu command")

with tempfile.TemporaryDirectory() as tmp:
    env = {**os.environ, "HOME": tmp, "XDG_CONFIG_HOME": tmp + "/.config",
           "XDG_CACHE_HOME": tmp + "/.cache", "XDG_DATA_HOME": tmp + "/.local/share"}
    with subprocess.Popen(command, cwd=tmp, env=env) as window:
        try:
            subprocess.run(
                ["xdotool", "search", "--sync", "--onlyvisible", "--all",
                 "--pid", str(window.pid), "--name", "^XQuasar$"],
                check=True, timeout=20, stdout=subprocess.DEVNULL,
            )
        finally:
            window.terminate()

tests = Path(__file__).resolve().parent.parent / "tests"
suite = unittest.defaultTestLoader.discover(str(tests), pattern="test_gui.py")
result = unittest.TextTestRunner(verbosity=2).run(suite)
raise SystemExit(0 if result.wasSuccessful() and not result.skipped else 1)
