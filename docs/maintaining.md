# Maintaining XQuasar

## Architecture

The Python CLI owns prompts and presentation. The scanner returns candidates and partial errors while the executor reopens home-relative directories and checks the object's identity before acting. Linux directory file descriptors and mount IDs limit traversal. Moving app profiles within the same filesystem preserves data and avoids recursive deletion. Empty folders use `rmdir`, which fails if an entry appeared during review. Each successful action stands on its own if another item fails.

The optional GTK 3 desktop window calls the same scanner and executor. Both run on a worker thread. GTK widget updates run on the main loop. The desktop entry launches the packaged system-Python command with `--gui`. Linux Mint 22.3 provides GTK 3.24.41 and PyGObject 3.48.2. [GTK 3 TreeView](https://docs.gtk.org/gtk3/class.TreeView.html) · [PyGObject threading](https://pygobject.gnome.org/guide/threading.html) · [Desktop Entry specification](https://specifications.freedesktop.org/desktop-entry/latest/)

Use Docker for development. The image runs tests as an ordinary user with private temporary homes and the real Flatpak CLI. To iterate after building the image, run `docker run --rm --network=none -v "$PWD:/workspace:ro" xquasar-dev` from the source checkout.

The image targets Python 3.15.2. The CLI also supports Python 3.12+. Filesystem operations use the standard library. [Python 3.15 os](https://docs.python.org/3.15/library/os.html) · [Python 3.12 os](https://docs.python.org/3.12/library/os.html) · [Dockerfile reference](https://docs.docker.com/reference/dockerfile/) · [Flatpak list](https://docs.flatpak.org/en/latest/flatpak-command-reference.html#flatpak-list) · [Thumbnail specification](https://specifications.freedesktop.org/thumbnail/latest/)

To build the installer from the checkout, run `sh packaging/build-deb.sh 0.2.0 /tmp/xquasar.deb`. The Docker suite installs the package, checks its menu launcher on a virtual X display, and exercises the window against temporary homes using Debian's system Python and GTK bindings. [dpkg-deb](https://manpages.debian.org/trixie/dpkg/dpkg-deb.1.en.html)

## GitHub Wiki

Edit the Markdown sources in `docs/wiki/` together. To initialize GitHub Wiki, save an initial Home page in the repository's Wiki tab. The Publish Wiki workflow copies the guides and Home page into the separate Wiki repository, converting links to Wiki page URLs. It runs when a Wiki page is created or guide sources change on main. Maintainers can also run it from the Actions tab. Edit the managed pages in the source repository so changes survive the next publication.

Verify the five language links from the published Home page. [Editing GitHub Wikis](https://docs.github.com/en/communities/documenting-your-project-with-wikis/adding-or-editing-wiki-pages)

## GitHub Releases

For a release, commit user-facing notes for every README language in `docs/releases/vX.Y.Z.md`. Describe changes, migration requirements and limitations. Tag the verified commit with the matching `vX.Y.Z` and push the tag. The workflow runs the Docker suite, smoke-tests the source archive, installs the versioned Debian package, and verifies the desktop launcher before publishing both assets. Keep the asset name `xquasar.deb` for the download link in the READMEs. [GitHub Releases](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository)
