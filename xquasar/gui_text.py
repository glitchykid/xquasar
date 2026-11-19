"""Desktop labels in the languages available in the user guide."""

import os


# English source text followed by Russian, Japanese, Korean and Simplified Chinese.
LABELS = {
    "Automatic home cleanup": ("Автоматическая очистка", "ホームの自動整理", "홈 자동 정리", "自动清理主目录"),
    "Thumbnail cache": ("Кэш миниатюр", "サムネイルキャッシュ", "미리보기 이미지 캐시", "缩略图缓存"),
    "Font cache": ("Кэш шрифтов", "フォントキャッシュ", "글꼴 캐시", "字体缓存"),
    "Uninstalled Flatpak profiles": ("Профили удалённых приложений Flatpak", "削除済み Flatpak アプリのプロファイル", "삭제한 Flatpak 앱 프로필", "已卸载 Flatpak 应用的配置"),
    "Personal folders are kept.": ("Личные папки сохраняются.", "個人用フォルダーは保持されます。", "개인 폴더는 그대로 보관합니다.", "保留个人目录。"),
    "Show paths": ("Показать пути", "パスを表示", "경로 보기", "查看路径"),
    "Showing {n} of {total} paths": ("Показано путей: {n} из {total}", "{total} 件中 {n} 件のパスを表示", "경로 {total}개 중 {n}개 표시", "共 {total} 个路径，显示 {n} 个"),
    "Clean up…": ("Очистить…", "整理…", "정리…", "清理…"),
    "Ready to clean: {n}": ("К очистке: {n}", "整理の候補：{n} 件", "정리할 항목: {n}개", "可清理：{n} 项"),
    "Apply this cleanup plan?": ("Выполнить очистку?", "この内容で整理しますか？", "이 계획대로 정리할까요?", "按此计划清理？"),
    "Delete cache files: {n}": ("Удалить файлов кэша: {n}", "削除するキャッシュファイル：{n} 件", "삭제할 캐시 파일: {n}개", "删除缓存文件：{n} 个"),
    "Move profiles to recovery: {n}": ("Переместить профилей для восстановления: {n}", "退避先に移すプロファイル：{n} 件", "복구 폴더로 이동할 프로필: {n}개", "移入恢复目录的配置：{n} 个"),
    "Scan again": ("Проверить снова", "再スキャン", "다시 검사", "重新扫描"),
    "Open recovery folder": ("Открыть папку восстановления", "退避先を開く", "복구 폴더 열기", "打开恢复目录"),
    "Scanning…": ("Идёт поиск…", "スキャン中…", "검사 중…", "正在扫描…"),
    "Scan incomplete": ("Поиск завершён частично", "スキャンは一部のみ完了しました", "일부 경로를 검사하지 못했습니다", "扫描未全部完成"),
    "Cleaning…": ("Идёт очистка…", "整理中…", "정리 중…", "正在清理…"),
    "Nothing to clean": ("Нет кандидатов на очистку", "整理できる項目はありません", "정리할 항목이 없습니다", "没有可清理的项目"),
    "Cancel": ("Отмена", "キャンセル", "취소", "取消"),
    "Clean": ("Очистить", "整理する", "정리", "清理"),
    "Cleaned {n} of {total}": ("Очищено {n} из {total}", "{total} 件中 {n} 件を整理しました", "{total}개 중 {n}개 정리됨", "已清理 {n} 项，共选 {total} 项"),
    "Some items were skipped": ("Часть позиций пропущена", "一部の項目をスキップしました", "일부 항목을 건너뛰었습니다", "已跳过部分项目"),
    "Could not complete the operation": ("Не удалось завершить операцию", "処理を完了できませんでした", "작업을 완료하지 못했습니다", "未能完成操作"),
}


def translate(source, **values):
    language = next((os.environ[key] for key in ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG")
                     if os.environ.get(key)), "en")
    code = language.split(":")[0].split(".")[0].split("_")[0].lower()
    index = {"ru": 0, "ja": 1, "ko": 2, "zh": 3}.get(code)
    text = source if index is None else LABELS[source][index]
    return text.format(**values)
