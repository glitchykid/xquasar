import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest


class CleanerCLI(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.home = self.root / "home"
        self.home.mkdir()
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.env = {
            **os.environ,
            "HOME": str(self.home),
            "PATH": str(self.bin),
            "XDG_CONFIG_HOME": str(self.home / ".config"),
            "XDG_CACHE_HOME": str(self.home / ".cache"),
        }

    def cli(self, *args, answer=""):
        return subprocess.run(
            [sys.executable, "-m", "xquasar", *args], input=answer, text=True,
            capture_output=True, env=self.env, timeout=10,
        )

    def directory(self, name):
        target = self.home / name
        target.mkdir(parents=True, exist_ok=True)
        return target

    def flatpak(self, script):
        tool = self.bin / "flatpak"
        tool.write_text("#!/bin/sh\n" + script)
        tool.chmod(0o755)

    def test_preview_then_cancel_leaves_home_intact(self):
        target = self.directory("old-empty")
        preview = self.cli()
        self.assertEqual(preview.returncode, 0, preview.stderr)
        self.assertIn("old-empty", preview.stdout)
        for answer in ("", "\n", "no\n", "1\nno\n", "7\nyes\n"):
            with self.subTest(answer=answer):
                self.cli("--clean", answer=answer)
                self.assertTrue(target.is_dir())
        self.assertEqual(list(self.home.iterdir()), [target])

    def test_only_selected_empty_directory_is_removed(self):
        first = self.directory("alpha")
        other = self.directory("beta")
        run = self.cli("--clean", answer="1\nyes\n")
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertFalse(first.exists())
        self.assertTrue(other.is_dir())

    def test_visible_empty_dirs_only_and_thumbnail_allowlist(self):
        empty = self.directory("work/empty")
        protected = [self.directory(name) for name in
                     (".ssh/private", "repo/.git", "repo/assets", "Downloads", "docs/personal")]
        (protected[-1] / "notes").write_text("keep")
        outside = self.root / "elsewhere"
        outside.mkdir()
        (self.home / "link").symlink_to(outside, target_is_directory=True)
        folder = self.directory(".cache/thumbnails/normal")
        junk = folder / ("a" * 32 + ".png")
        junk.write_bytes(b"cached image")
        (folder / "photo.png").write_bytes(b"personal")
        run = self.cli("--clean", answer="all\nyes\n")
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertFalse(empty.exists())
        self.assertFalse(junk.exists())
        self.assertTrue((folder / "photo.png").exists())
        self.assertTrue(all(p.is_dir() for p in protected))
        self.assertTrue(outside.is_dir())
        self.assertTrue((self.home / "link").is_symlink())

    def test_manual_and_orphan_data_can_be_recovered(self):
        self.flatpak("echo org.example.Installed")
        kept = self.directory(".var/app/org.example.Installed")
        paths = [".var/app/org.example.Gone", ".config/OldEditor"]
        for path in paths:
            (self.directory(path) / "profile").write_text("saved")
        run = self.cli("--clean", "--leftover", paths[1], answer="all\nyes\n")
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertTrue(kept.exists())
        for path in paths:
            self.assertFalse((self.home / path).exists())
            recovered, = (self.home / ".xquasar-recovery").glob("*/" + path + "/profile")
            self.assertEqual(recovered.read_text(), "saved")
        again = self.cli("--clean", answer="all\nyes\n")
        self.assertEqual(again.returncode, 0, again.stderr)
        self.assertNotIn("profile", again.stdout)

    def test_flatpak_unavailable_or_partial_never_authorizes_orphans(self):
        orphan = self.directory(".var/app/org.example.Unknown")
        for script in (None, "exit 1", "echo partial >&2", "echo 'broken output'"):
            with self.subTest(script=script):
                if script:
                    self.flatpak(script)
                run = self.cli("--clean", answer="all\nyes\n")
                self.assertTrue(orphan.exists())
                self.assertIn("flatpak", run.stderr.lower())
                self.assertNotEqual(run.returncode, 0)

    def test_reinstalled_flatpak_is_retained_after_confirmation(self):
        self.flatpak('if [ -e "$HOME/.queried" ]; then echo org.example.Back; fi\n'
                     'touch_marker="$HOME/.queried"; : > "$touch_marker"')
        reinstalled = self.directory(".var/app/org.example.Back")
        run = self.cli("--clean", answer="all\nyes\n")
        self.assertIn("org.example.Back", run.stdout)
        self.assertTrue(reinstalled.is_dir())
        self.assertNotEqual(run.returncode, 0)

    def test_invalid_manual_target_cancels_before_any_changes(self):
        protected = self.directory("keep")
        for path in (".config", "/tmp", "../outside", ".config/../keep", ".ssh", ".local/share"):
            with self.subTest(path=path):
                run = self.cli("--leftover", path, "--clean", answer="all\nyes\n")
                self.assertNotEqual(run.returncode, 0)
                self.assertTrue(protected.is_dir())

    def test_symlinked_recovery_or_manual_parent_cannot_move_external_data(self):
        outside = self.root / "outside"
        outside.mkdir()
        (outside / "app").mkdir()
        (self.home / ".config").symlink_to(outside)
        self.cli("--leftover", ".config/app", "--clean", answer="all\nyes\n")
        self.assertTrue((outside / "app").is_dir())
        target = self.directory(".cache/old")
        (self.home / ".xquasar-recovery").symlink_to(outside)
        self.cli("--leftover", ".cache/old", "--clean", answer="all\nyes\n")
        self.assertTrue(target.is_dir())
        self.assertEqual(list(outside.iterdir()), [outside / "app"])
