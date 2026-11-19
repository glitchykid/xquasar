"""Native Linux desktop interface. GTK is optional for CLI users."""

from pathlib import Path
import threading

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gtk, Pango

from .cleaner import apply, manual_path, open_home, scan
from .gui_text import translate as tr


ACTIONS = {
    "empty": "Remove empty folder",
    "thumbnail": "Delete thumbnail",
    "flatpak": "Move Flatpak data to recovery",
    "manual": "Move app data to recovery",
}


def button(label, callback):
    widget = Gtk.Button(label=tr(label))
    widget.connect("clicked", callback)
    return widget


class CleanerWindow(Gtk.Window):
    def __init__(self, path, manual=()):
        super().__init__(title="XQuasar")
        self.home_path = path
        self.manual = set(manual)
        self.busy = False
        self.applying = False
        self.closed = False
        self.recovery = None
        self.selected_count = 0
        self.set_default_size(790, 460)
        self.set_icon_name("edit-clear")
        self.connect("destroy", lambda *_: setattr(self, "closed", True))
        self.connect("delete-event", lambda *_: self.applying)

        header = Gtk.HeaderBar(title="XQuasar", subtitle=tr("Home cleanup"), show_close_button=True)
        self.set_titlebar(header)
        self.rescan_button = button("Scan again", self.refresh)
        header.pack_start(self.rescan_button)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10, border_width=12)
        self.add(box)
        toolbar = Gtk.Box(spacing=8)
        box.pack_start(toolbar, False, False, 0)
        location = Gtk.Label(label=str(path), xalign=0, ellipsize=Pango.EllipsizeMode.MIDDLE)
        location.set_tooltip_text(str(path))
        toolbar.pack_start(location, True, True, 0)
        self.add_button = button("Add app folder…", self.pick_folder)
        toolbar.pack_end(self.add_button, False, False, 0)

        self.model = Gtk.ListStore(bool, str, str, object)
        self.view = Gtk.TreeView(model=self.model)
        self.view.set_search_column(1)
        self.view.set_tooltip_column(1)
        self.toggle = Gtk.CellRendererToggle()
        self.toggle.connect("toggled", self.toggle_row)
        check = Gtk.TreeViewColumn(tr("Select"), self.toggle, active=0)
        self.view.append_column(check)
        for index, title in [(1, "Path in home"), (2, "Action")]:
            cell = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(tr(title), cell, text=index)
            if index == 1:
                cell.set_property("ellipsize", Pango.EllipsizeMode.MIDDLE)
                column.set_expand(True)
                column.set_min_width(120)
            self.view.append_column(column)
        self.view.connect("row-activated", lambda _, row, col: self.toggle_row(None, row)
                          if col != check else None)
        scroll = Gtk.ScrolledWindow(shadow_type=Gtk.ShadowType.IN)
        scroll.add(self.view)
        box.pack_start(scroll, True, True, 0)

        self.details = Gtk.Expander(label=tr("Some items were skipped"))
        self.detail_text = Gtk.TextView(editable=False, cursor_visible=False,
                                        wrap_mode=Gtk.WrapMode.WORD_CHAR)
        detail_scroll = Gtk.ScrolledWindow(min_content_height=64)
        detail_scroll.add(self.detail_text)
        self.details.add(detail_scroll)
        box.pack_start(self.details, False, False, 0)

        footer = Gtk.Box(spacing=8)
        box.pack_start(footer, False, False, 0)
        self.all_button = button("Select all", self.toggle_all)
        footer.pack_start(self.all_button, False, False, 0)
        self.spinner = Gtk.Spinner()
        footer.pack_start(self.spinner, False, False, 0)
        self.status = Gtk.Label(xalign=0, wrap=True)
        footer.pack_start(self.status, True, True, 0)
        self.recovery_button = button("Open recovery folder", self.open_recovery)
        footer.pack_start(self.recovery_button, False, False, 0)
        self.clean_button = button("Clean selected…", self.clean)
        self.clean_button.get_style_context().add_class("suggested-action")
        footer.pack_end(self.clean_button, False, False, 0)
        self.show_all()
        self.details.hide()
        self.recovery_button.hide()
        self.refresh()

    def update_buttons(self):
        for control in (self.add_button, self.rescan_button, self.view):
            control.set_sensitive(not self.busy)
        self.all_button.set_sensitive(bool(len(self.model)) and not self.busy)
        self.clean_button.set_sensitive(self.selected_count > 0 and not self.busy)
        self.all_button.set_label(tr("Clear selection" if self.selected_count else "Select all"))

    def selection_status(self):
        self.update_buttons()
        self.status.set_text(tr("Found {n} · Selected {s}", n=len(self.model), s=self.selected_count)
                             if len(self.model) else tr("Nothing to clean"))

    def toggle_row(self, _, path):
        if not self.busy:
            row = self.model[path]
            row[0] = not row[0]
            self.selected_count += 1 if row[0] else -1
            self.selection_status()

    def toggle_all(self, *_):
        select = self.selected_count == 0
        for row in self.model:
            row[0] = select
        self.selected_count = len(self.model) if select else 0
        self.selection_status()

    def warnings(self, messages):
        self.details.set_visible(bool(messages))
        self.details.set_expanded(False)
        self.detail_text.get_buffer().set_text("\n".join(messages).encode("utf-8", "backslashreplace").decode())

    def run_job(self, operation, args, finish, status):
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
                self.status.set_text(tr("Could not complete the operation"))
                self.warnings([error])
            self.update_buttons()
            return False

        def work():
            try:
                with open_home(self.home_path) as home:
                    result = operation(home, args)
            except (OSError, ValueError) as exc:
                GLib.idle_add(deliver, None, str(exc))
            else:
                GLib.idle_add(deliver, result, None)

        threading.Thread(target=work, daemon=not self.applying).start()

    def refresh(self, *_):
        self.model.clear()
        self.selected_count = 0
        self.warnings([])
        self.run_job(scan, tuple(self.manual), self.show_items, "Scanning…")

    def show_items(self, items, warnings):
        self.view.set_model(None)
        for item in items:
            self.model.append((False, repr(str(item.path))[1:-1], tr(ACTIONS[item.kind]), item))
        self.view.set_model(self.model)
        self.selection_status()
        self.warnings(warnings)
        if warnings and not items:
            self.status.set_text(tr("Scan incomplete"))

    def pick_folder(self, *_):
        dialog = Gtk.FileChooserDialog(title=tr("Add app folder…"), transient_for=self, modal=True,
                                       action=Gtk.FileChooserAction.SELECT_FOLDER)
        dialog.add_buttons(tr("Cancel"), Gtk.ResponseType.CANCEL, tr("Add"), Gtk.ResponseType.OK)
        dialog.set_show_hidden(True)
        dialog.set_current_folder(str(self.home_path))
        path = dialog.get_filename() if dialog.run() == Gtk.ResponseType.OK else None
        dialog.destroy()
        if path:
            self.include_folder(Path(path))

    def include_folder(self, path):
        try:
            self.manual.add(manual_path(path.relative_to(self.home_path)))
        except ValueError:
            self.warnings([tr("Choose an app folder directly inside .config, .cache, .local/share or .local/state.")])
            self.details.set_expanded(True)
            return
        self.refresh()

    def clean(self, *_):
        selected = [row[3] for row in self.model if row[0]]
        if not selected or self.busy:
            return
        permanent = sum(item.kind in {"empty", "thumbnail"} for item in selected)
        dialog = Gtk.MessageDialog(transient_for=self, modal=True, message_type=Gtk.MessageType.QUESTION,
                                   text=tr("Clean the selected items?"))
        dialog.format_secondary_text(tr("Permanently delete: {n}", n=permanent) + "\n" +
                                     tr("Move to recovery: {n}", n=len(selected) - permanent))
        dialog.add_buttons(tr("Cancel"), Gtk.ResponseType.CANCEL, tr("Clean"), Gtk.ResponseType.OK)
        dialog.set_default_response(Gtk.ResponseType.CANCEL)
        confirmed = dialog.run() == Gtk.ResponseType.OK
        dialog.destroy()
        if confirmed:
            self.applying = True
            self.run_job(apply, selected, self.cleaned, "Cleaning…")

    def cleaned(self, done, failures, session):
        completed = set(done)
        for item in done:
            if item.kind == "manual":
                self.manual.discard(item.path)
        paths = [row[3] for row in self.model if row[3] not in completed]
        count = self.selected_count
        self.model.clear()
        self.selected_count = 0
        self.show_items(paths, failures)
        self.status.set_text(tr("Cleaned {n} of {total}", n=len(done), total=count))
        if any(item.kind in {"flatpak", "manual"} for item in done):
            self.recovery = self.home_path / session
            self.recovery_button.show()
            self.recovery_button.set_tooltip_text(str(self.recovery))

    def open_recovery(self, *_):
        try:
            Gtk.show_uri_on_window(self, self.recovery.as_uri(), Gtk.get_current_event_time())
        except GLib.Error as exc:
            self.warnings([str(exc)])
            self.details.set_expanded(True)


def run(manual=()):
    if not Gtk.init_check()[0]:
        raise ValueError("XQuasar needs a graphical desktop. Run python3 -m xquasar for a terminal preview.")
    window = CleanerWindow(Path.home(), manual)
    window.connect("destroy", lambda *_: Gtk.main_quit())
    Gtk.main()
    return 0
