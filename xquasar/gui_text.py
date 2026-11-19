"""Desktop labels in the languages available in the user guide."""

import os


# English source text followed by Russian, Japanese, Korean and Simplified Chinese.
LABELS = {
    "Removed KDE application settings": ("Настройки удалённых программ KDE", "削除済み KDE アプリの設定", "삭제한 KDE 앱 설정", "已卸载 KDE 应用的设置"),
    "Browser graphics cache": ("Графический кэш браузеров", "ブラウザーの描画キャッシュ", "브라우저 그래픽 캐시", "浏览器图形缓存"),
    "Qt QML bytecode": ("Байткод Qt QML", "Qt QML バイトコード", "Qt QML 바이트코드", "Qt QML 字节码"),
    "darktable thumbnails": ("Миниатюры darktable", "darktable のサムネイル", "darktable 미리보기", "darktable 缩略图"),
    "Thunderbird HTTP": ("HTTP-кэш Thunderbird", "Thunderbird の HTTP キャッシュ", "Thunderbird HTTP 캐시", "Thunderbird HTTP 缓存"),
    "Thunderbird startup": ("Кэш запуска Thunderbird", "Thunderbird の起動キャッシュ", "Thunderbird 시작 캐시", "Thunderbird 启动缓存"),
    "Go build outputs": ("Результаты сборки Go", "Go のビルド出力", "Go 빌드 결과", "Go 构建产物"),
    "Gradle dependency archives": ("Архивы зависимостей Gradle", "Gradle の依存アーカイブ", "Gradle 의존성 아카이브", "Gradle 依赖归档"),
    "Electron downloads": ("Установочные архивы Electron", "Electron の配布アーカイブ", "Electron 배포 파일", "Electron 下载归档"),
    "pip HTTP archives": ("Архивы из HTTP-кэша pip", "pip の HTTP アーカイブ", "pip HTTP 아카이브", "pip HTTP 归档"),
    "RubyGems package indexes": ("Индексы пакетов RubyGems", "RubyGems の索引", "RubyGems 패키지 색인", "RubyGems 软件包索引"),
    "RubyGems specifications": ("Метаданные пакетов RubyGems", "RubyGems のパッケージ仕様", "RubyGems 패키지 명세", "RubyGems 软件包规格"),
    "Cabal source archives": ("Архивы пакетов Cabal", "Cabal のソースアーカイブ", "Cabal 소스 아카이브", "Cabal 源码归档"),
    "Helm repository indexes": ("Индексы репозиториев Helm", "Helm のリポジトリ索引", "Helm 저장소 색인", "Helm 仓库索引"),
    "Composer package metadata": ("Метаданные пакетов Composer", "Composer のパッケージ情報", "Composer 패키지 정보", "Composer 软件包元数据"),
    "NuGet version lists": ("Списки версий NuGet", "NuGet のバージョン一覧", "NuGet 버전 목록", "NuGet 版本列表"),
    "Removed APT profiles": ("Профили удалённых APT-приложений", "APT で削除したアプリのプロファイル", "APT로 삭제한 앱 프로필", "已通过 APT 卸载的应用配置"),
    "Removed Snap profiles": ("Профили удалённых Snap-приложений", "削除済み Snap のプロファイル", "삭제한 Snap 앱 프로필", "已卸载 Snap 应用的配置"),
    "Package managers may need to download these archives again.": ("Менеджерам пакетов может потребоваться повторно скачать эти архивы.", "パッケージ管理ツールがアーカイブを再度ダウンロードする場合があります。", "패키지 관리자가 이 파일을 다시 다운로드해야 할 수 있습니다.", "包管理器可能需要重新下载这些归档。"),
    "Cache to clear": ("Кэш к очистке", "整理できるキャッシュ", "정리할 캐시", "可清理的缓存"),
    "Cleanup plan": ("План очистки", "整理の候補", "정리 계획", "清理计划"),
    "All checks ({n})": ("Все проверки ({n})", "すべての検査 ({n})", "전체 검사 ({n})", "全部检查 ({n})"),
    "Firefox HTTP": ("HTTP-кэш Firefox", "Firefox HTTP キャッシュ", "Firefox HTTP 캐시", "Firefox HTTP 缓存"),
    "Firefox startup": ("Кэш запуска Firefox", "Firefox 起動キャッシュ", "Firefox 시작 캐시", "Firefox 启动缓存"),
    "Firefox scripts": ("Кэш скриптов Firefox", "Firefox スクリプト", "Firefox 스크립트", "Firefox 脚本缓存"),
    "Firefox URL cache": ("Кэш адресов Firefox", "Firefox URL キャッシュ", "Firefox URL 캐시", "Firefox 网址缓存"),
    "Firefox extension startup": ("Кэш запуска расширений Firefox", "Firefox 拡張機能の起動キャッシュ", "Firefox 확장 기능 시작 캐시", "Firefox 扩展启动缓存"),
    "Failed thumbnails": ("Кэш неудачных миниатюр", "生成失敗のサムネイル", "생성에 실패한 미리보기 캐시", "缩略图生成失败记录"),
    "GStreamer registry": ("Реестр модулей GStreamer", "GStreamer レジストリ", "GStreamer 레지스트리", "GStreamer 插件注册表"),
    "Matplotlib fonts": ("Кэш шрифтов Matplotlib", "Matplotlib フォント", "Matplotlib 글꼴", "Matplotlib 字体缓存"),
    "pip wheels": ("Кэш пакетов pip", "pip の wheel キャッシュ", "pip wheel 캐시", "pip wheel 缓存"),
    "npm package archives": ("Архивы пакетов npm", "npm パッケージアーカイブ", "npm 패키지 아카이브", "npm 软件包归档"),
    "Cargo crate archives": ("Архивы пакетов Cargo", "Cargo クレートアーカイブ", "Cargo 크레이트 아카이브", "Cargo crate 归档"),
    "Composer archives": ("Архивы Composer", "Composer アーカイブ", "Composer 아카이브", "Composer 归档"),
    "NuGet HTTP": ("HTTP-кэш NuGet", "NuGet HTTP キャッシュ", "NuGet HTTP 캐시", "NuGet HTTP 缓存"),
    "Go build actions": ("Записи сборки Go", "Go ビルドキャッシュ", "Go 빌드 기록", "Go 构建记录"),
    "Automatic home cleanup": ("Автоматическая очистка", "ホームの自動整理", "홈 자동 정리", "自动清理主目录"),
    "Thumbnail cache": ("Кэш миниатюр", "サムネイルキャッシュ", "미리보기 이미지 캐시", "缩略图缓存"),
    "Browser and Electron cache": ("Кэш браузеров и Electron", "ブラウザー・Electron キャッシュ", "브라우저 및 Electron 캐시", "浏览器和 Electron 缓存"),
    "Python bytecode": ("Кэш Python", "Python バイトコード", "Python 바이트코드", "Python 字节码缓存"),
    "Obsolete Flatpak launchers": ("Ярлыки удалённых приложений Flatpak", "削除済み Flatpak のランチャー", "삭제한 Flatpak 앱 바로가기", "已卸载 Flatpak 应用的启动器"),
    "Font cache": ("Кэш шрифтов", "フォントキャッシュ", "글꼴 캐시", "字体缓存"),
    "Uninstalled Flatpak profiles": ("Профили удалённых приложений Flatpak", "削除済み Flatpak アプリのプロファイル", "삭제한 Flatpak 앱 프로필", "已卸载 Flatpak 应用的配置"),
    "Personal folders are kept.": ("Личные папки сохраняются.", "個人用フォルダーは保持されます。", "개인 폴더는 그대로 보관합니다.", "保留个人目录。"),
    "Show paths": ("Показать пути", "パスを表示", "경로 보기", "查看路径"),
    "Showing {n} of {total} paths": ("Показано путей: {n} из {total}", "{total} 件中 {n} 件のパスを表示", "경로 {total}개 중 {n}개 표시", "共 {total} 个路径，显示 {n} 个"),
    "Clean up…": ("Очистить…", "整理…", "정리…", "清理…"),
    "Ready to clean: {n}": ("К очистке: {n}", "整理の候補：{n} 件", "정리할 항목: {n}개", "可清理：{n} 项"),
    "Apply this cleanup plan?": ("Выполнить очистку?", "この内容で整理しますか？", "이 계획대로 정리할까요?", "按此计划清理？"),
    "Delete cache files: {n}": ("Удалить файлов кэша: {n}", "削除するキャッシュファイル：{n} 件", "삭제할 캐시 파일: {n}개", "删除缓存文件：{n} 个"),
    "Move to recovery: {n}": ("Переместить в папку восстановления: {n}", "退避する項目数：{n}", "복구 폴더로 옮길 항목: {n}개", "移入恢复目录：{n} 项"),
    "Scan again": ("Проверить снова", "再スキャン", "다시 검사", "重新扫描"),
    "Open recovery folder": ("Открыть папку восстановления", "退避先を開く", "복구 폴더 열기", "打开恢复目录"),
    "Scanning…": ("Идёт поиск…", "スキャン中…", "검사 중…", "正在扫描…"),
    "Scan incomplete": ("Поиск завершён частично", "スキャンは一部のみ完了しました", "일부 경로를 검사하지 못했습니다", "扫描未全部完成"),
    "Cleaning…": ("Идёт очистка…", "整理中…", "정리 중…", "正在清理…"),
    "Nothing to clean": ("Нет кандидатов на очистку", "整理できる項目はありません", "정리할 항목이 없습니다", "没有可清理的项目"),
    "Cancel": ("Отмена", "キャンセル", "취소", "取消"),
    "Browser and Python cache folders emptied by this cleanup are removed.": ("Опустевшие папки кэша браузера и Python также удаляются.", "整理で空になったブラウザーと Python のキャッシュフォルダーも削除します。", "정리 후 비게 된 브라우저 및 Python 캐시 폴더도 삭제합니다.", "清理后变空的浏览器和 Python 缓存目录也会移除。"),
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
