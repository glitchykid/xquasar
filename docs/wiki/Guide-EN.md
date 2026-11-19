[English](Guide-EN.md) · [Русский](Guide-RU.md) · [日本語](Guide-JA.md) · [한국어](Guide-KO.md) · [简体中文](Guide-ZH.md)

# Automatic cleanup and recovery

1. Open **XQuasar** from the applications menu and wait for the summary. Each cache category shows the file count and size. The Flatpak row counts profiles that can be moved to recovery. Empty personal folders are preserved.
2. Choose **Show paths** to inspect the plan. Select **Clean up…** to see how many cache files will be deleted and how many profiles will be moved. Confirm or cancel.
3. To restore a profile, choose **Open recovery folder** after cleanup. Close the app and move its folder back to the original path. If that path already exists, keep both copies and compare them first. Deleting the recovery copy frees its disk space.

From a source checkout, `python3 -m xquasar` shows a preview. Run `python3 -m xquasar --clean` and type `yes` to apply it. A `Skipped` message identifies an incomplete check or action. Exit codes are 0 for success or cancellation, 1 for a partial result and 2 for invalid input or an inaccessible home.

[Installation and command examples](https://github.com/glitchykid/xquasar/blob/main/README.md)
