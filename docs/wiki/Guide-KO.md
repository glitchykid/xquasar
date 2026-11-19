[English](Guide-EN.md) · [Русский](Guide-RU.md) · [日本語](Guide-JA.md) · [한국어](Guide-KO.md) · [简体中文](Guide-ZH.md)

# 자동 정리 및 프로필 복구

1. 메뉴에서 **XQuasar**를 여세요. 캐시 종류별 파일 수와 크기, 복구 폴더로 옮길 Flatpak 프로필 및 바로가기 수가 표시됩니다. 개인 파일과 용도가 불분명한 폴더는 목록에서 제외됩니다.
2. **경로 보기**로 항목을 살펴보세요. **정리…**를 누르면 삭제할 캐시와 이동할 항목 수를 확인하고 진행하거나 취소할 수 있습니다.
3. 복원하려면 정리 후 **복구 폴더 열기**를 누르세요. 해당 앱을 종료하고 보관된 바로가기나 프로필을 원래 경로로 옮기세요. 같은 위치에 이미 항목이 있으면 두 사본을 보관하고 내용을 먼저 비교하세요.

**앱 캐시** — `.config`, `.local/share`, `.local/state`, `.cache`의 앱 폴더에서 이름과 헤더로 Chromium 및 Electron의 디스크 캐시와 코드 캐시를 식별합니다. `~/.thumbnails`의 예전 미리보기 이미지와 `~/.local/lib/python3.*/site-packages`에서 원본 소스가 남아 있는 Python 바이트코드도 찾습니다. 브라우저 또는 Python 캐시 파일을 지운 뒤 해당 캐시 폴더가 비면 함께 삭제합니다.

**Flatpak 바로가기** — `.local/share/applications`의 메뉴 항목과 `.config/autostart`의 자동 시작 항목은 파일 이름, Flatpak 표식, 실행 명령이 같은 삭제된 앱을 가리킬 때 복구 폴더로 옮깁니다. 이동 직전에 설치된 앱 목록을 다시 확인합니다.

소스 폴더에서 `python3 -m xquasar`로 계획을 확인하세요. `python3 -m xquasar --clean`을 실행하고 `yes`를 입력하면 정리를 시작합니다. `Skipped`는 검사나 작업을 건너뛴 항목을 알려 줍니다. 종료 코드는 성공 또는 취소 시 0, 일부 완료 시 1, 입력 오류 또는 홈에 접근할 수 없는 경우 2입니다.

[설치 및 명령 예시](https://github.com/glitchykid/xquasar/blob/main/README.ko.md)
