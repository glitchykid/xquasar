# Maintaining XQuasar

## Architecture

The Python CLI owns prompts and presentation. The scanner returns candidates and partial errors while the executor reopens home-relative directories and checks the object's identity before acting. Linux directory file descriptors and mount IDs limit traversal. Moving app profiles within the same filesystem preserves data and avoids recursive deletion. Empty folders use `rmdir`, which fails if an entry appeared during review. Each successful action stands on its own if another item fails.

Use Docker for development. The image runs tests as an ordinary user with private temporary homes and the real Flatpak CLI. To iterate after building the image, run `docker run --rm --network=none -v "$PWD:/workspace:ro" xquasar-dev` from the source checkout.

The image targets Python 3.15.2. The CLI also supports Python 3.12+. Filesystem operations use the standard library. [Python 3.15 os](https://docs.python.org/3.15/library/os.html) · [Python 3.12 os](https://docs.python.org/3.12/library/os.html) · [Dockerfile reference](https://docs.docker.com/reference/dockerfile/) · [Flatpak list](https://docs.flatpak.org/en/latest/flatpak-command-reference.html#flatpak-list) · [Thumbnail specification](https://specifications.freedesktop.org/thumbnail/latest/)

## GitHub Wiki

Edit the Markdown sources in `docs/wiki/` together. To initialize GitHub Wiki, save an initial Home page in the repository's Wiki tab. The Publish Wiki workflow copies the guides and Home page into the separate Wiki repository, converting links to Wiki page URLs. It runs when a Wiki page is created or guide sources change on main. Maintainers can also run it from the Actions tab. Edit the managed pages in the source repository so changes survive the next publication.

Verify the five language links from the published Home page. [Editing GitHub Wikis](https://docs.github.com/en/communities/documenting-your-project-with-wikis/adding-or-editing-wiki-pages)

## GitHub Releases

For a release, commit user-facing notes for every README language in `docs/releases/vX.Y.Z.md`. Describe changes, migration requirements and limitations. Tag the verified commit with the matching `vX.Y.Z` and push the tag. The GitHub workflow runs the Docker suite, smoke-tests the source archive, and publishes it with the notes. Check the release page and download afterward. [GitHub Releases](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository)
