# Maintaining XQuasar

## Architecture

The Python CLI owns prompts and presentation. The scanner returns candidates and partial errors while the executor reopens home-relative directories and checks the object's identity before acting. Linux directory file descriptors and mount IDs limit traversal. Moving app profiles within the same filesystem preserves data and avoids recursive deletion. Empty folders use `rmdir`, which fails if an entry appeared during review. Each successful action stands on its own if another item fails.

Use Docker for development. The image runs tests as an ordinary user with private temporary homes and the real Flatpak CLI. To iterate after building the image, run `docker run --rm --network=none -v "$PWD:/workspace:ro" xquasar-dev` from the source checkout.

The image targets Python 3.15.2. The CLI also supports Python 3.12+. Filesystem operations use the standard library. [Python 3.15 os](https://docs.python.org/3.15/library/os.html) · [Python 3.12 os](https://docs.python.org/3.12/library/os.html) · [Dockerfile reference](https://docs.docker.com/reference/dockerfile/) · [Flatpak list](https://docs.flatpak.org/en/latest/flatpak-command-reference.html#flatpak-list) · [Thumbnail specification](https://specifications.freedesktop.org/thumbnail/latest/)

## GitHub Wiki

Edit the Markdown sources in `docs/wiki/` together. For a new repository, save an initial Home page in GitHub's Wiki tab. The Wiki is a separate Git repository. From the project root, publish the reviewed pages to a fresh checkout with an account that can write to it. Review the diff before committing. The conversion below uses the Wiki's extensionless page URLs.

```sh
git clone https://github.com/glitchykid/xquasar.wiki.git ../xquasar.wiki
for page in docs/wiki/*.md; do
  sed -E 's/\]\((Guide-[A-Z]+)\.md\)/](\1)/g' "$page" > "../xquasar.wiki/$(basename "$page")"
done
git -C ../xquasar.wiki diff
git -C ../xquasar.wiki add -- Home.md Guide-EN.md Guide-RU.md Guide-JA.md Guide-KO.md Guide-ZH.md
git -C ../xquasar.wiki diff --cached
git -C ../xquasar.wiki commit -m "Update multilingual cleanup guide"
git -C ../xquasar.wiki push
```

Verify the five language links from the published Home page. [Editing GitHub Wikis](https://docs.github.com/en/communities/documenting-your-project-with-wikis/adding-or-editing-wiki-pages)

## GitHub Releases

For a release, commit user-facing notes for every README language in `docs/releases/vX.Y.Z.md`. Describe changes, migration requirements and limitations. Tag the verified commit with the matching `vX.Y.Z` and push the tag. The GitHub workflow runs the Docker suite, smoke-tests the source archive, and publishes it with the notes. Check the release page and download afterward. [GitHub Releases](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository)
