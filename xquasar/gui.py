"""GTK preview of the automatic cleanup plan."""

from pathlib import Path
import threading

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gtk, Pango

from .cleaner import apply, open_home, scan
from .gui_text import translate as tr


GROUPS = {"thumbnail": "Thumbnail cache", "fontconfig": "Font cache",
          "flatpak": "Uninstalled Flatpak profiles"}


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
        self.set_default_size(610, 300)
        self.set_icon_name("edit-clear")
        self.connect("destroy", lambda *_: setattr(self, "closed", True))
        self.connect("delete-event", lambda *_: self.applying)

        header = Gtk.HeaderBar(title="XQuasar", subtitle=tr("Automatic home cleanup"), show_close_button=True)
        self.set_titlebar(header)
        self.rescan_button = button("Scan again", self.refresh)
        header.pack_start(self.rescan_button)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10, border_width=14)
        self.add(box)
        location = Gtk.Label(label=str(path), xalign=0, ellipsize=Pango.EllipsizeMode.MIDDLE)
        location.set_tooltip_text(str(path))
        box.pack_start(location, False, False, 0)
        grid = Gtk.Grid(row_spacing=8, column_spacing=20, border_width=10)
        frame = Gtk.Frame()
        frame.add(grid)
        box.pack_start(frame, False, False, 0)
        self.counts = {}
        for row, (kind, name) in enumerate(GROUPS.items()):
            grid.attach(Gtk.Label(label=tr(name), xalign=0, hexpand=True), 0, row, 1, 1)
            count = Gtk.Label(label="—", xalign=1)
            grid.attach(count, 1, row, 1, 1)
            self.counts[kind] = count
        box.pack_start(Gtk.Label(label=tr("Personal folders are kept."), xalign=0), False, False, 0)

        self.paths, self.path_text = text_panel("Show paths")
        self.paths.connect("notify::expanded", self.show_paths)
        box.pack_start(self.paths, False, False, 0)
        self.details, self.detail_text = text_panel("Some items were skipped")
        box.pack_start(self.details, False, False, 0)

        footer = Gtk.Box(spacing=8)
        box.pack_end(footer, False, False, 0)
        self.spinner = Gtk.Spinner()
        footer.pack_start(self.spinner, False, False, 0)
        self.status = Gtk.Label(xalign=0, wrap=True)
        footer.pack_start(self.status, True, True, 0)
        self.recovery_button = button("Open recovery folder", self.open_recovery)
        footer.pack_start(self.recovery_button, False, False, 0)
        self.clean_button = button("Clean up…", self.clean)
        self.clean_button.get_style_context().add_class("suggested-action")
        footer.pack_end(self.clean_button, False, False, 0)
        self.show_all()
        self.recovery_button.hide()
        self.refresh()

    def update_buttons(self):
        self.rescan_button.set_sensitive(not self.busy)
        self.clean_button.set_sensitive(bool(self.plan) and not self.busy)

    def show_plan(self, items):
        self.plan = items
        totals = {kind: [0, 0] for kind in GROUPS}
        for item in items:
            totals[item.kind][0] += 1
            totals[item.kind][1] += item.size
        for kind, (count, size) in totals.items():
            value = str(count)
            if kind != "flatpak" and count:
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
        self.scan_warnings = []
        self.warnings([])
        self.run_job(scan, self.scanned, "Scanning…")

    def scanned(self, items, warnings):
        self.show_plan(items)
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
        dialog.format_secondary_text(tr("Delete cache files: {n}", n=cached) + "\n" +
                                     tr("Move profiles to recovery: {n}", n=len(self.plan) - cached))
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
