import argparse
from pathlib import Path
import sys

from .cleaner import apply, manual_path, open_home, scan


def choose(items):
    try:
        choice = input("Items to clean (space-separated numbers, 'all', or Enter to cancel): ")
        if not choice.strip():
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
    mode.add_argument("--clean", action="store_true", help="select items and confirm cleanup")
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
            return run(manual)
        with open_home(Path.home()) as home:
            items, warnings = scan(home, manual)
            for warning in warnings:
                print(f"Skipped: {warning}", file=sys.stderr)
            for index, item in enumerate(items, 1):
                action = {"empty": "remove empty folder", "thumbnail": "delete thumbnail",
                          "manual": "recoverable move", "flatpak": "recoverable move"}[item.kind]
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
                    if any(item.kind in {"flatpak", "manual"} for item in done):
                        print(f"Recovery directory: {str(home.path / session)!r}")
                    warnings.extend(failures)
                else:
                    print("Cancelled.")
            else:
                print(f"Preview: {len(items)} item(s). Run with --clean to select and confirm.")
            return int(bool(warnings))
    except (OSError, ValueError) as exc:
        print(f"xquasar: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
