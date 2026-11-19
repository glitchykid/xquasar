"""GTK preview of the automatic cleanup plan."""

from pathlib import Path
import threading

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import GdkPixbuf, GLib, Gtk, Pango

from .appearance import draw_quasar, load_theme, styled
from .catalog import DOWNLOADS, RULES
from .cleaner import apply, open_home, scan
from .gui_text import translate as tr


GROUPS = {"thumbnail": "Thumbnail cache", "fontconfig": "Font cache",
          "browser": "Browser and Electron cache", "browser_gpu": "Browser graphics cache", "bytecode": "Python bytecode",
          "flatpak": "Uninstalled Flatpak profiles", "launcher": "Obsolete Flatpak launchers",
          "kconfig": "Removed KDE application settings",
          "apt": "Removed APT profiles", "snap": "Removed Snap profiles",
          **{key: rule.label for key, rule in RULES.items()}}
RECOVERABLE = {"flatpak", "launcher", "apt", "snap", "kconfig"}


def label(value, style):
    return styled(Gtk.Label(label=value, xalign=0), style)


def group_icon(kind):
    if kind in RECOVERABLE:
        return "folder-download-symbolic"
    if kind in {"browser", "browser_gpu"} or kind.startswith(("firefox_", "thunderbird_")):
        return "web-browser-symbolic"
    if kind in {"thumbnail", "failed_thumbnail", "matplotlib", "fontconfig", "gstreamer"}:
        return "image-x-generic-symbolic"
    return "applications-engineering-symbolic"


def button(label, callback):
    widget = Gtk.Button(label=tr(label))
    widget.connect("clicked", callback)
    return widget


def text_panel(label):
    panel = Gtk.Expander(label=tr(label))
    view = Gtk.TextView(editable=False, cursor_visible=False, wrap_mode=Gtk.WrapMode.WORD_CHAR)
    scroll = Gtk.ScrolledWindow(min_content_height=85, shadow_type=Gtk.ShadowType.IN)
    scroll.add(view)
    panel.add(scroll)
    return panel, view.get_buffer()


class CleanerWindow(Gtk.Window):
    def __init__(self, path):
        super().__init__(title="XQuasar")
        self.home_path = path
        self.plan = []
        self.scan_warnings = []
        self.busy = self.applying = self.closed = False
        self.recovery = None
        self.set_default_size(750, 625)
        load_theme(self)
        self.connect("destroy", lambda *_: setattr(self, "closed", True))
        self.connect("delete-event", lambda *_: self.applying)

        header = styled(Gtk.HeaderBar(show_close_button=True), "quasar-bar")
        header.set_custom_title(Gtk.Box())
        brand = Gtk.Box(spacing=9)
        symbol = Gtk.Image.new_from_pixbuf(self.get_icon().scale_simple(30, 30, GdkPixbuf.InterpType.BILINEAR))
        brand.pack_start(symbol, False, False, 0)
        brand.pack_start(label("XQuasar", "brand"), False, False, 0)
        header.pack_start(brand)
        self.rescan_button = button("Scan again", self.refresh)
        header.pack_end(self.rescan_button)
        self.set_titlebar(header)

        shell = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(shell)
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        shell.pack_start(scroll, True, True, 0)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12, border_width=18)
        scroll.add(box)

        hero = Gtk.Overlay()
        art = Gtk.DrawingArea(height_request=166)
        art.connect("draw", draw_quasar)
        hero.add(art)
        info = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1, margin_start=23,
                       margin_end=18, valign=Gtk.Align.CENTER)
        info.pack_start(label(tr("Cache to clear"), "hero-label"), False, False, 0)
        self.cache_total = label("—", "hero-total")
        info.pack_start(self.cache_total, False, False, 0)
        location = label(str(path), "hero-path")
        location.set_ellipsize(Pango.EllipsizeMode.MIDDLE)
        location.set_tooltip_text(str(path))
        info.pack_start(location, False, False, 0)
        hero.add_overlay(info)
        box.pack_start(hero, False, False, 0)

        heading = Gtk.Box(spacing=8)
        heading.pack_start(label(tr("Cleanup plan"), "section"), True, True, 0)
        self.all_rules = Gtk.ToggleButton(label=tr("All checks ({n})", n=len(GROUPS)))
        self.all_rules.connect("toggled", self.filter_rows)
        heading.pack_end(self.all_rules, False, False, 0)
        box.pack_start(heading, False, False, 0)
        self.rows = {}
        self.counts = {}
        self.present = set()
        rows = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        for kind, name in GROUPS.items():
            row = styled(Gtk.Box(spacing=10), "plan-row")
            icon = styled(Gtk.Image.new_from_icon_name(group_icon(kind), Gtk.IconSize.MENU), "row-icon")
            if kind in RECOVERABLE:
                styled(icon, "recover")
            row.pack_start(icon, False, False, 0)
            title = label(tr(name), "row-name")
            title.set_line_wrap(True)
            row.pack_start(title, True, True, 0)
            count = label("—", "row-count")
            row.pack_end(count, False, False, 0)
            rows.pack_start(row, False, False, 0)
            self.rows[kind], self.counts[kind] = row, count
        box.pack_start(rows, False, False, 0)
        self.empty_state = label(tr("Nothing to clean"), "empty")
        box.pack_start(self.empty_state, False, False, 0)

        self.paths, self.path_text = text_panel("Show paths")
        self.paths.connect("notify::expanded", self.show_paths)
        box.pack_start(self.paths, False, False, 0)
        self.details, self.detail_text = text_panel("Some items were skipped")
        box.pack_start(self.details, False, False, 0)

        footer = styled(Gtk.Box(spacing=10), "bottom-bar")
        shell.pack_end(footer, False, False, 0)
        self.spinner = Gtk.Spinner()
        footer.pack_start(self.spinner, False, False, 0)
        feedback = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        self.status = label("", "row-name")
        self.status.set_line_wrap(True)
        feedback.pack_start(self.status, False, False, 0)
        feedback.pack_start(label(tr("Personal folders are kept."), "muted"), False, False, 0)
        footer.pack_start(feedback, True, True, 0)
        self.recovery_button = button("Open recovery folder", self.open_recovery)
        box.pack_start(self.recovery_button, False, False, 0)
        self.clean_button = styled(button("Clean up…", self.clean), "primary")
        footer.pack_end(self.clean_button, False, False, 0)
        self.show_all()
        self.recovery_button.hide()
        self.refresh()

    def update_buttons(self):
        self.rescan_button.set_sensitive(not self.busy)
        self.clean_button.set_sensitive(bool(self.plan) and not self.busy)

    def filter_rows(self, *_):
        show_all = self.all_rules.get_active()
        for kind, row in self.rows.items():
            row.set_visible(show_all or kind in self.present)
        self.empty_state.set_visible(not show_all and not self.present and not self.busy)

    def show_plan(self, items):
        self.plan = items
        totals = {kind: [0, 0] for kind in GROUPS}
        for item in items:
            totals[item.kind][0] += 1
            totals[item.kind][1] += item.size
        self.present = {kind for kind, (count, _) in totals.items() if count}
        self.filter_rows()
        self.cache_total.set_text(GLib.format_size(sum(item.size for item in items if item.is_cache)))
        for kind, (count, size) in totals.items():
            value = str(count)
            if kind not in RECOVERABLE and count:
                value += " · " + GLib.format_size(size)
            self.counts[kind].set_text(value)
        self.paths.set_visible(bool(items))
        self.show_paths()

    def show_paths(self, *_):
        if not self.paths.get_expanded():
            return
        # Keep the optional preview responsive even with a very large cache.
        visible = self.plan[:200]
        lines = [repr(str(item.path))[1:-1] for item in visible]
        if len(visible) < len(self.plan):
            lines.insert(0, tr("Showing {n} of {total} paths", n=len(visible), total=len(self.plan)))
        self.path_text.set_text("\n".join(lines))

    def warnings(self, messages):
        self.details.set_visible(bool(messages))
        self.detail_text.set_text("\n".join(messages).encode("utf-8", "backslashreplace").decode())

    def run_job(self, operation, finish, status, *args):
        self.busy = True
        self.empty_state.hide()
        self.status.set_text(tr(status))
        self.spinner.start()
        self.update_buttons()

        def deliver(result, error):
            if self.closed:
                return False
            self.busy = self.applying = False
            self.spinner.stop()
            if error is None:
                finish(*result)
            else:
                self.show_plan([])
                self.empty_state.hide()
                self.cache_total.set_text("—")
                self.status.set_text(tr("Could not complete the operation"))
                self.warnings([error])
            self.update_buttons()
            return False

        def work():
            try:
                with open_home(self.home_path) as home:
                    result = operation(home, *args)
            except (OSError, ValueError) as exc:
                GLib.idle_add(deliver, None, str(exc))
            else:
                GLib.idle_add(deliver, result, None)

        threading.Thread(target=work, daemon=not self.applying).start()

    def refresh(self, *_):
        self.show_plan([])
        for count in self.counts.values():
            count.set_text("—")
        self.cache_total.set_text("—")
        self.scan_warnings = []
        self.warnings([])
        self.run_job(scan, self.scanned, "Scanning…")

    def scanned(self, items, warnings):
        self.show_plan(items)
        self.empty_state.set_text(tr("Scan incomplete" if warnings else "Nothing to clean"))
        self.scan_warnings = warnings
        self.warnings(warnings)
        if items:
            self.status.set_text(tr("Ready to clean: {n}", n=len(items)))
        else:
            self.status.set_text(tr("Scan incomplete" if warnings else "Nothing to clean"))

    def clean(self, *_):
        if not self.plan or self.busy:
            return
        cached = sum(item.is_cache for item in self.plan)
        dialog = Gtk.MessageDialog(transient_for=self, modal=True, message_type=Gtk.MessageType.QUESTION,
                                   text=tr("Apply this cleanup plan?"))
        styled(dialog, "quasar")
        summary = [tr("Delete cache files: {n}", n=cached),
                   tr("Move to recovery: {n}", n=len(self.plan) - cached)]
        if any(item.kind in {"browser", "bytecode"} for item in self.plan):
            summary.append(tr("Browser and Python cache folders emptied by this cleanup are removed."))
        if any(item.kind in DOWNLOADS for item in self.plan):
            summary.append(tr("Package managers may need to download these archives again."))
        dialog.format_secondary_text("\n".join(summary))
        dialog.add_buttons(tr("Cancel"), Gtk.ResponseType.CANCEL, tr("Clean"), Gtk.ResponseType.OK)
        dialog.set_default_response(Gtk.ResponseType.CANCEL)
        confirmed = dialog.run() == Gtk.ResponseType.OK
        dialog.destroy()
        if confirmed:
            self.applying = True
            self.run_job(apply, self.cleaned, "Cleaning…", tuple(self.plan))

    def cleaned(self, done, failures, session):
        count = len(self.plan)
        self.show_plan([])
        self.empty_state.set_text(tr("Scan again"))
        self.empty_state.hide()
        self.status.set_text(tr("Cleaned {n} of {total}", n=len(done), total=count))
        self.warnings([*self.scan_warnings, *failures])
        if any(not item.is_cache for item in done):
            self.recovery = self.home_path / session
            self.recovery_button.show()
            self.recovery_button.set_tooltip_text(str(self.recovery))

    def open_recovery(self, *_):
        try:
            Gtk.show_uri_on_window(self, self.recovery.as_uri(), Gtk.get_current_event_time())
        except GLib.Error as exc:
            self.warnings([str(exc)])
            self.details.set_expanded(True)


def run():
    if not Gtk.init_check()[0]:
        raise ValueError("XQuasar needs a graphical desktop. Run python3 -m xquasar for a terminal preview.")
    window = CleanerWindow(Path.home())
    window.connect("destroy", lambda *_: Gtk.main_quit())
    Gtk.main()
    return 0
