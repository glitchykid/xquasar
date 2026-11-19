import argparse
from pathlib import Path
import sys

from .catalog import RULES
from .cleaner import apply, manual_path, open_home, scan


def choose(items):
    try:
        choice = input(f"Clean the {len(items)} listed item(s)? Type yes to confirm, or Enter to cancel: ")
        if choice.strip() == "yes":
            return items
        if choice.strip() in {"", "no"}:
            return []
        if choice.strip() == "all":
            selected = items
        else:
            indexes = sorted({int(word) for word in choice.split()})
            if any(index < 1 or index > len(items) for index in indexes):
                raise ValueError("item number outside the list")
            selected = [items[index - 1] for index in indexes]
        if input(f"Clean {len(selected)} item(s)? Type yes to confirm: ").strip() == "yes":
            return selected
    except (EOFError, KeyboardInterrupt):
        pass
    return []


def main():
    parser = argparse.ArgumentParser(prog="xquasar", description="Preview Linux home cleanup.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--clean", action="store_true", help="confirm the automatic cleanup plan")
    mode.add_argument("--gui", action="store_true", help="open the desktop cleanup window")
    parser.add_argument("--leftover", action="append", default=[], metavar="APP_DIR",
                        help="include a home-relative app directory, e.g. .config/OldEditor")
    args = parser.parse_args()
    try:
        manual = [manual_path(path) for path in args.leftover]
        if args.gui:
            try:
                from .gui import run
            except (ImportError, ValueError):
                parser.exit(2, "XQuasar GUI requires GTK 3 and PyGObject. On Mint or Ubuntu install "
                            "python3-gi and gir1.2-gtk-3.0, or use the XQuasar .deb package.\n")
            if manual:
                parser.error("--leftover is an explicit terminal option; the desktop plan is automatic")
            return run()
        with open_home(Path.home()) as home:
            items, warnings = scan(home, manual)
            for warning in warnings:
                print(f"Skipped: {warning}", file=sys.stderr)
            for index, item in enumerate(items, 1):
                action = {"browser": "delete browser cache", "bytecode": "delete Python cache",
                          "launcher": "recoverable move", "fontconfig": "delete font cache", "thumbnail": "delete thumbnail",
                          "apt": "recoverable move", "snap": "recoverable move",
                          "manual": "recoverable move", "flatpak": "recoverable move"}.get(item.kind)
                if item.kind in RULES:
                    action = "delete cache: " + RULES[item.kind].label
                print(f"{index:4}  {item.kind:9}  {str(item.path)!r}  ({action})")
            if not items:
                print("No cleanup candidates.")
            elif args.clean:
                selected = choose(items)
                if selected:
                    done, failures, session = apply(home, selected)
                    for failure in failures:
                        print(f"Skipped: {failure}", file=sys.stderr)
                    print(f"Cleaned {len(done)} of {len(selected)} selected item(s).")
                    if any(not item.is_cache for item in done):
                        print(f"Recovery directory: {str(home.path / session)!r}")
                    warnings.extend(failures)
                else:
                    print("Cancelled.")
            else:
                print(f"Preview: {len(items)} item(s). Run with --clean to confirm the plan.")
            return int(bool(warnings))
    except (OSError, ValueError) as exc:
        print(f"xquasar: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
