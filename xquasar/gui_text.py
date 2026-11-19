"""Desktop labels in the languages available in the user guide."""

import os


# English source text followed by Russian, Japanese, Korean and Simplified Chinese.
LABELS = {
    "Home cleanup": ("Очистка домашней папки", "ホームの整理", "홈 폴더 정리", "主目录清理"),
    "Scan again": ("Проверить снова", "再スキャン", "다시 검사", "重新扫描"),
    "Add app folder…": ("Добавить папку приложения…", "アプリのフォルダーを追加…", "앱 폴더 추가…", "添加应用目录…"),
    "Select": ("Выбор", "選択", "선택", "选择"),
    "Path in home": ("Путь в домашней папке", "ホーム内のパス", "홈 기준 경로", "主目录内的路径"),
    "Action": ("Действие", "操作", "작업", "操作"),
    "Remove empty folder": ("Удалить пустую папку", "空のフォルダーを削除", "빈 폴더 삭제", "删除空目录"),
    "Delete thumbnail": ("Удалить миниатюру", "サムネイルを削除", "미리보기 이미지 삭제", "删除缩略图"),
    "Move Flatpak data to recovery": ("Перенести профиль Flatpak", "Flatpak データを退避", "Flatpak 데이터 복구 폴더로 이동", "将 Flatpak 数据移入恢复目录"),
    "Move app data to recovery": ("Перенести профиль приложения", "アプリデータを退避", "앱 데이터 복구 폴더로 이동", "将应用数据移入恢复目录"),
    "Select all": ("Выбрать все", "すべて選択", "모두 선택", "全选"),
    "Clear selection": ("Снять выбор", "選択を解除", "선택 해제", "取消全选"),
    "Clean selected…": ("Очистить выбранное…", "選択した項目を整理…", "선택 항목 정리…", "清理所选项…"),
    "Open recovery folder": ("Открыть папку восстановления", "退避先を開く", "복구 폴더 열기", "打开恢复目录"),
    "Scanning…": ("Идёт поиск…", "スキャン中…", "검사 중…", "正在扫描…"),
    "Scan incomplete": ("Поиск завершён частично", "スキャンは一部のみ完了しました", "일부 경로를 검사하지 못했습니다", "扫描未全部完成"),
    "Cleaning…": ("Идёт очистка…", "整理中…", "정리 중…", "正在清理…"),
    "Nothing to clean": ("Нет кандидатов на очистку", "整理できる項目はありません", "정리할 항목이 없습니다", "没有可清理的项目"),
    "Found {n} · Selected {s}": ("Найдено {n} · Выбрано {s}", "検出 {n} 件 · 選択 {s} 件", "발견 {n}개 · 선택 {s}개", "找到 {n} 项 · 已选 {s} 项"),
    "Clean the selected items?": ("Очистить выбранные позиции?", "選択した項目を整理しますか？", "선택한 항목을 정리할까요?", "清理所选项目？"),
    "Permanently delete: {n}": ("Удалить безвозвратно: {n}", "完全に削除：{n} 件", "영구 삭제: {n}개", "永久删除：{n} 项"),
    "Move to recovery: {n}": ("Переместить в папку восстановления: {n}", "退避先に移動：{n} 件", "복구 폴더로 이동: {n}개", "移入恢复目录：{n} 项"),
    "Cancel": ("Отмена", "キャンセル", "취소", "取消"),
    "Clean": ("Очистить", "整理する", "정리", "清理"),
    "Add": ("Добавить", "追加", "추가", "添加"),
    "Cleaned {n} of {total}": ("Очищено {n} из {total}", "{total} 件中 {n} 件を整理しました", "{total}개 중 {n}개 정리됨", "已清理 {n} 项，共选 {total} 项"),
    "Some items were skipped": ("Часть позиций пропущена", "一部の項目をスキップしました", "일부 항목을 건너뛰었습니다", "已跳过部分项目"),
    "Could not complete the operation": ("Не удалось завершить операцию", "処理を完了できませんでした", "작업을 완료하지 못했습니다", "未能完成操作"),
    "Choose an app folder directly inside .config, .cache, .local/share or .local/state.":
        ("Выберите папку приложения непосредственно внутри .config, .cache, .local/share или .local/state.",
         ".config、.cache、.local/share、.local/state の直下にあるアプリのフォルダーを選択してください。",
         ".config, .cache, .local/share 또는 .local/state 바로 아래의 앱 폴더를 선택하세요.",
         "请选择 .config、.cache、.local/share 或 .local/state 的直接子目录。"),
}


def translate(source, **values):
    language = next((os.environ[key] for key in ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG")
                     if os.environ.get(key)), "en")
    code = language.split(":")[0].split(".")[0].split("_")[0].lower()
    index = {"ru": 0, "ja": 1, "ko": 2, "zh": 3}.get(code)
    text = source if index is None else LABELS[source][index]
    return text.format(**values)
