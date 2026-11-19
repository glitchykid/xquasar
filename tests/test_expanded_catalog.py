import hashlib
from io import BytesIO
import os
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from xquasar.native import SnapState
from xquasar.cleaner import apply, open_home, scan


def archive():
    output = BytesIO()
    with zipfile.ZipFile(output, "w") as z:
        z.writestr("META-INF/MANIFEST.MF", "Manifest-Version: 1.0\n")
    return output.getvalue()


class ExpandedCatalog(unittest.TestCase):
    def setUp(self):
        self.root = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.home = self.enterContext(open_home(self.root))
        self.proc = self.root / "proc"
        self.proc.mkdir()
        (self.proc / str(os.getpid())).symlink_to("/proc/self")
        self.enterContext(patch("xquasar.activity.PROC", self.proc))
        self.flat = self.enterContext(patch("xquasar.cleaner.installed_apps", return_value=set()))
        self.snaps = self.enterContext(patch("xquasar.native.snap_state", return_value=SnapState(set(), set(), set())))
        self.db = self.enterContext(patch("xquasar.native.dpkg_states", return_value=(set(), set())))
        self.enterContext(patch("xquasar.native.available_command", return_value=False))
        self.enterContext(patch("xquasar.native.apt_history", return_value=set()))
        self.enterContext(patch.dict(os.environ, {f"XDG_{key}_HOME": str(self.root / val) for key,val in
            [("CONFIG", ".config"), ("CACHE", ".cache"), ("DATA", ".local/share"), ("STATE", ".local/state")]}))

    def write(self, path, data):
        file = self.root / path
        file.parent.mkdir(exist_ok=True, parents=True)
        file.write_bytes(data)
        return Path(path)

    def plan(self):
        plan, warnings = scan(self.home)
        self.assertFalse(warnings)
        return {i.path: i.kind for i in plan}

    def test_format_rules_and_similar_personal_files(self):
        z = archive()
        output = b"compiled object"
        sha = hashlib.sha256(output).hexdigest()
        qt = b"qv4cdata" + struct.pack("<IIQI", 42, 0x60503, 42, 256) + bytes(228)
        release = hashlib.sha256(b"https://github.com/electron/electron/releases/download/v32.0.0").hexdigest()
        examples = [
            ("go_output", f".cache/go-build/{sha[:2]}/{sha}-d", output),
            ("gradle", ".gradle/caches/modules-2/files-2.1/org.example/sdk/1.0/" +
             hashlib.sha1(z).hexdigest() + "/sdk-1.0.jar", z),
            ("electron_download", f".cache/electron/{release}/electron-v32.0.0-linux-x64.zip", z),
            ("qml", ".cache/Example/Viewer/qmlcache/" + "a"*40 + ".qmlc", qt),
            ("darktable_thumb", ".cache/darktable/mipmaps-" + "f"*40 + ".d/2/812.jpg",
             b"\xff\xd8\xff\xe0" + bytes(80) + b"\xff\xd9"),
            ("ruby_index", ".gem/specs/rubygems.org%443/latest_specs.4.8", b"\x04\x08[" + bytes(32)),
            ("ruby_spec", ".gem/specs/rubygems.org%443/quick/Marshal.4.8/rake-13.0.0.gemspec",
             b"\x04\x08u:\x17Gem::Specification" + bytes(40)),
            ("thunderbird_http", ".cache/thunderbird/test/cache2/entries/" + hashlib.sha1(b":mail").hexdigest().upper(),
             bytes(4) + struct.pack(">8I", 4, 0, 0, 0, 0, 0, 5, 0) + b":mail\0" + bytes(4)),
            ("thunderbird_startup", ".cache/thunderbird/test/startupCache/startupCache.8.little", b"startupcache0002\0" + bytes(32)),
            ("browser_gpu", ".config/Example/Default/GPUCache/" + "f"*16 + "_0", bytes.fromhex("305c72a71b6dfbfc")),
        ]
        expected = {}
        for kind,path,data in examples:
            expected[self.write(path,data)] = kind
            self.write("Documents/" + path, data)
            self.write(path + ".bak", data)
        self.assertEqual(self.plan(), expected)
        for _,path,_ in examples:
            (self.root/path).write_bytes(b"settings")
        self.assertFalse(self.plan())

    def test_pip_http_body_needs_metadata_and_matching_fanout(self):
        name = "abcde" + "f"*51
        path = ".cache/pip/http-v2/a/b/c/d/e/" + name
        body = self.write(path + ".body", archive())
        self.assertFalse(self.plan())
        self.write(path, b"cc=4,\x81\xa8response" + bytes(30))
        self.assertEqual(self.plan(), {body: "pip_http"})
        items, _ = scan(self.home)
        (self.root / path).unlink()
        self.assertFalse(apply(self.home, items)[0])
        self.assertTrue((self.root / body).is_file())

    def test_installed_sandboxes_get_format_checks_and_removed_profile_stays_whole(self):
        self.flat.return_value = {"org.example.Lens"}
        self.snaps.return_value = SnapState({"camera"}, set(), set())
        rel = "thumbnails/normal/" + "b"*32 + ".png"
        paths = [self.write(base + rel, b"\x89PNG\r\n\x1a\n") for base in
                 [".var/app/org.example.Lens/cache/", "snap/camera/43/.cache/", ".snap/data/camera/common/.cache/"]]
        self.write("snap/unknown/43/.cache/" + rel, b"\x89PNG\r\n\x1a\n")
        removed = Path(".var/app/org.example.Gone")
        self.write(str(removed / "cache" / rel), b"\x89PNG\r\n\x1a\n")
        self.write("snap/camera/43/Documents/" + rel, b"\x89PNG\r\n\x1a\n")
        self.assertEqual(self.plan(), {**dict.fromkeys(paths,"thumbnail"), removed:"flatpak"})
        items, _ = scan(self.home)
        with subprocess.Popen(["Lens","60"], executable="/bin/sleep") as proc:
            try:
                (self.proc / str(proc.pid)).symlink_to(Path("/proc") / str(proc.pid))
                self.assertNotIn(paths[0], self.plan())
                self.assertFalse(apply(self.home, [i for i in items if i.path == paths[0]])[0])
            finally:
                proc.terminate()

    def test_shared_profiles_require_removal_and_veto_other_package_and_binary(self):
        profile = self.write(".config/obs-studio/basic/settings", b"my settings").parents[1]
        self.assertFalse(self.plan())
        self.db.return_value = (set(), {"obs-studio"})
        self.assertEqual(self.plan(), {profile:"apt"})
        with patch("xquasar.native.available_command", side_effect=lambda names: "obs" in names):
            self.assertFalse(self.plan())
        self.flat.return_value = {"com.obsproject.Studio"}
        self.assertFalse(self.plan())

    def test_container_removal_or_in_progress_change_invalidates_preview(self):
        self.flat.return_value = {"org.example.Lens"}
        self.snaps.return_value = SnapState({"camera"}, set(), set())
        suffix = "thumbnails/normal/" + "b"*32 + ".png"
        files = [self.write(prefix + suffix, b"\x89PNG\r\n\x1a\n") for prefix in
                 [".var/app/org.example.Lens/cache/", "snap/camera/common/.cache/"]]
        items, warnings = scan(self.home)
        self.assertEqual({i.path for i in items}, set(files))
        self.flat.return_value = set()
        self.snaps.return_value = SnapState({"camera"}, {"camera"}, set())
        self.assertNotIn(files[1], self.plan())
        self.assertFalse(apply(self.home, items)[0])
        self.assertTrue(all((self.root/f).exists() for f in files))

    def test_downloaded_registry_metadata_and_source_archives(self):
        import tarfile
        tar = BytesIO()
        with tarfile.open(fileobj=tar, mode="w:gz") as output:
            entry = tarfile.TarInfo("demo-1.2/demo.cabal")
            output.addfile(entry)
        files = {
            self.write(".cache/cabal/packages/hackage.haskell.org/demo/1.2/demo-1.2.tar.gz", tar.getvalue()): "cabal",
            self.write(".cache/helm/repository/stable-index.yaml", b"apiVersion: v1\nentries:\n  demo:\n  - apiVersion: v2\n"): "helm_index",
            self.write(".cache/composer/repo/https---repo.packagist.org/provider-acme$demo.json",
                       b'{"packages":{"acme/demo":[{"name":"acme/demo","version":"1.0"}]}}'): "composer_metadata",
            self.write(".local/share/NuGet/v3-cache/" + "a"*40 + "$ps_api.nuget.org_v3_index.json/list_demo.dat",
                       b'{"versions":["1.0.0","2.0.0-beta.1"]}'): "nuget_versions",
        }
        self.assertEqual(self.plan(), files)
        self.write(".cache/cabal/packages/hackage.haskell.org/other/1.2/other-1.2.tar.gz", tar.getvalue())
        self.write(".cache/composer/repo/https---repo.packagist.org/provider-wrong$demo.json",
                   (self.root/next(p for p,k in files.items() if k=="composer_metadata")).read_bytes())
        self.assertEqual(self.plan(), files)
        items, _ = scan(self.home)
        self.assertEqual(apply(self.home, items)[:2], (items, []))

    def test_verified_kde_settings_move_intact_and_recheck_running_app(self):
        self.db.return_value = (set(), {"kcalc", "ark", "kmines", "filelight"})
        accepted = self.write(".config/kcalcrc", b"[Precision]\nDigits=12\n")
        self.write(".config/arkrc", b"my personal notes")
        self.write(".config/kminesrc/notes", b"ordinary folder")
        self.write(".config/kcalcrc.backup", b"[Precision]\nDigits=8\n")
        (self.root / ".config/filelightrc").symlink_to(self.root / accepted)
        self.assertEqual(self.plan(), {accepted: "kconfig"})
        items, _ = scan(self.home)
        with subprocess.Popen(["kcalc", "60"], executable="/bin/sleep") as proc:
            try:
                (self.proc / str(proc.pid)).symlink_to(Path("/proc") / str(proc.pid))
                self.assertFalse(self.plan())
                self.assertFalse(apply(self.home, items)[0])
            finally:
                proc.terminate()
        self.flat.return_value = {"org.kde.kcalc"}
        self.assertFalse(self.plan())
        self.flat.return_value = set()
        done, warnings, session = apply(self.home, items)
        self.assertEqual((done, warnings), (items, []))
        self.assertEqual((self.root / session / accepted).read_bytes(), b"[Precision]\nDigits=12\n")

    def test_busy_owner_skipped_before_reading_large_cache_objects(self):
        data = b"compiled"
        digest = hashlib.sha256(data).hexdigest()
        self.write(f".cache/go-build/{digest[:2]}/{digest}-d", data)
        with subprocess.Popen(["go", "60"], executable="/bin/sleep") as proc:
            try:
                (self.proc / str(proc.pid)).symlink_to(Path("/proc") / str(proc.pid))
                with patch("xquasar.catalog.digest_matches", side_effect=AssertionError("read an active cache")):
                    self.assertFalse(self.plan())
            finally:
                proc.terminate()

    def test_checksum_size_and_qt_length_limits(self):
        self.write(".cache/go-build/aa/" + "a"*64 + "-d", b"personal file")
        sparse = self.write(".cache/go-build/bb/" + "b"*64 + "-d", b"")
        with (self.root / sparse).open("wb") as file:
            file.truncate(65*1024*1024)
        self.write(".cache/Example/qmlcache/" + "a"*40 + ".qmlc",
                   b"qv4cdata" + struct.pack("<IIQI", 42, 0x60503, 42, 255) + bytes(228))
        self.assertFalse(self.plan())

    def test_kde_package_and_executable_may_have_different_names(self):
        settings = self.write(".config/spectaclerc", b"[Save]\nquality=85\n")
        self.db.return_value = (set(), {"kde-spectacle"})
        self.assertEqual(self.plan(), {settings:"kconfig"})
        self.snaps.return_value = SnapState({"spectacle"}, set(), set())
        self.assertFalse(self.plan())

    def test_chromium_partitions_and_qtwebengine_keep_offline_storage(self):
        signature = bytes.fromhex("305c72a71b6dfbfc")
        entry = "a"*16 + "_1"
        allowed = [
            ".config/Example/Partitions/work/Cache/Cache_Data/",
            ".cache/Example/QtWebEngine/Default/Code Cache/js/",
            ".cache/Example/Guest Profile/Network/Cache/Cache_Data/",
        ]
        files = {self.write(folder + entry, signature): "browser" for folder in allowed}
        personal = self.write(".config/Example/Service Worker/CacheStorage/" + entry, signature)
        self.assertEqual(self.plan(), files)
        items, _ = scan(self.home)
        self.assertEqual(apply(self.home, items)[:2], (items, []))
        self.assertTrue((self.root / personal).is_file())
