[English](Guide-EN.md) · [Русский](Guide-RU.md) · [日本語](Guide-JA.md) · [한국어](Guide-KO.md) · [简体中文](Guide-ZH.md)

# 자동 정리 및 프로필 복구

1. 어두운 테마의 창에서 찾은 캐시의 총크기와 해당 범주를 확인하세요. **전체 검사 (22)**를 누르면 일치하는 파일이 없는 범주도 볼 수 있습니다.
2. **경로 보기**로 항목을 살펴보세요. **정리…**를 누르면 삭제할 캐시와 이동할 항목 수를 확인하고 진행하거나 취소할 수 있습니다.
3. 복원하려면 정리 후 **복구 폴더 열기**를 누르세요. 해당 앱을 종료하고 보관된 바로가기나 프로필을 원래 경로로 옮기세요. 같은 위치에 이미 항목이 있으면 두 사본을 보관하고 내용을 먼저 비교하세요.

**APT 및 Snap 프로필** — qBittorrent, VLC, mpv, Inkscape, Audacity, FileZilla는 `.config`, `.local`, `.cache`와 이전 버전의 숨김 디렉터리에서 알려진 경로를 검사합니다. APT의 삭제 완료 기록이나 dpkg에서 설정 파일만 남은 상태를 현재 패키지 목록과 대조합니다. `~/snap`과 `~/.snap/data`에서는 해당 Snap 인스턴스의 삭제 기록이 있고 설치된 리비전이 모두 사라졌는지 확인합니다. 기록이 만료된 프로필은 찾지 못할 수 있습니다.

**실행 중인 앱** — 미리보기와 정리 시 사용자 프로세스를 확인합니다. 실행 중인 앱과 연결된 프로필 및 캐시는 건너뜁니다. Firefox HTTP 캐시도 여기에 포함됩니다. 앱을 닫고 다시 검사하면 해당 캐시를 볼 수 있습니다. 삭제가 확인된 프로필은 폴더째 복구 폴더로 옮깁니다.

**Firefox 및 데스크톱** — Firefox의 HTTP, 시작, 스크립트, URL, 확장 기능 시작 캐시를 식별합니다. 미리보기 이미지 생성 실패 기록, GStreamer 플러그인 레지스트리, Matplotlib 글꼴 목록도 검사합니다.

**개발 도구** — 기본 캐시 디렉터리에서 pip wheel, npm·Cargo·Composer 패키지 아카이브, NuGet HTTP 패키지, Go 빌드 기록을 찾습니다. 아카이브를 삭제하면 다음 빌드에서 다시 다운로드해야 할 수 있습니다.

**앱 캐시** — `.config`, `.local/share`, `.local/state`, `.cache`의 앱 폴더에서 이름과 헤더로 Chromium 및 Electron의 디스크 캐시와 코드 캐시를 식별합니다. `~/.thumbnails`의 예전 미리보기 이미지와 `~/.local/lib/python3.*/site-packages`에서 원본 소스가 남아 있는 Python 바이트코드도 찾습니다. 브라우저 또는 Python 캐시 파일을 지운 뒤 해당 캐시 폴더가 비면 함께 삭제합니다.

**Flatpak 바로가기** — `.local/share/applications`의 메뉴 항목과 `.config/autostart`의 자동 시작 항목은 파일 이름, Flatpak 표식, 실행 명령이 같은 삭제된 앱을 가리킬 때 복구 폴더로 옮깁니다. 이동 직전에 설치된 앱 목록을 다시 확인합니다.

소스 폴더에서 `python3 -m xquasar`로 계획을 확인하세요. `python3 -m xquasar --clean`을 실행하고 `yes`를 입력하면 정리를 시작합니다. `Skipped`는 검사나 작업을 건너뛴 항목을 알려 줍니다. 종료 코드는 성공 또는 취소 시 0, 일부 완료 시 1, 입력 오류 또는 홈에 접근할 수 없는 경우 2입니다.

[설치 및 명령 예시](https://github.com/glitchykid/xquasar/blob/main/README.ko.md)
