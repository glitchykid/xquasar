[English](Guide-EN.md) · [Русский](Guide-RU.md) · [日本語](Guide-JA.md) · [한국어](Guide-KO.md) · [简体中文](Guide-ZH.md)

# Cleaning and restoring an application profile

1. Close the application and run `python3 -m xquasar --leftover .config/OldEditor` from the source directory. Replace the example with a directory belonging to an app you removed. The preview shows what would happen to each path.
2. Repeat the command with `--clean`. Enter just the number of the app folder, then type `yes`. Flatpak folders found automatically use the same recovery mechanism.
3. Copy the recovery directory printed at the end. In your file manager, enable hidden files and open the original relative path inside that directory, for example `.config/OldEditor`. Its contents are still available.
4. To restore, close the app and move the folder back to its original parent. If the app recreated its profile, keep both copies and compare their contents before merging. To reclaim space, delete the recovery copy once you are sure you no longer need it.

Thumbnail deletion and empty-directory removal are permanent. A `Skipped` line means that item or scan rule could not complete. Exit code 0 indicates a completed run or cancellation, 1 a partial result, and 2 invalid input or an inaccessible home. Run the preview again after resolving the reported problem.

[Installation and command examples](https://github.com/glitchykid/xquasar/blob/main/README.md)
