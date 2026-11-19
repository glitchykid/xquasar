[English](README.md) · [Русский](README.ru.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [简体中文](README.zh-CN.md)

# XQuasar

XQuasar는 Linux 홈에서 다시 생성할 수 있는 캐시와 삭제한 Flatpak 앱의 잔여 데이터를 자동으로 찾습니다. 앱을 열면 정리할 항목을 확인할 수 있습니다. 용도가 불분명한 폴더와 개인 파일은 그대로 보관합니다.

## Linux Mint, Ubuntu, Debian에 설치

[XQuasar 다운로드(.deb)](https://github.com/glitchykid/xquasar/releases/latest/download/xquasar.deb) · [배포된 버전](https://github.com/glitchykid/xquasar/releases)

다운로드한 파일을 열고 **설치**를 누르세요. 설치 후 애플리케이션 메뉴에서 **XQuasar**를 실행합니다. 패키지 관리자가 그래픽 화면에 필요한 구성 요소도 설치합니다. Python 3.12 이상을 제공하는 배포판이 필요합니다.

어두운 테마의 창에서 찾은 캐시의 총크기와 해당 범주를 확인하세요. **전체 검사 (20)**를 누르면 일치하는 파일이 없는 범주도 볼 수 있습니다. **경로 보기**로 파일 목록을 열고 **정리…**에서 작업을 확인하세요. **복구 폴더 열기**로 저장된 프로필과 바로가기를 찾을 수 있습니다.

소스에서 설치 파일을 만들려면 다음 명령을 실행하세요

```sh
sh packaging/build-deb.sh 0.5.0 ./xquasar.deb
```

## 소스에서 CLI 실행

Linux와 Python 3.12 이상이 필요합니다. 소스 코드를 복제하려면 Git을 설치하세요. Flatpak이 있으면 삭제한 Flatpak 앱의 데이터도 자동으로 찾습니다. 홈 디렉터리를 소유한 사용자 계정으로 실행하세요.

```sh
git clone https://github.com/glitchykid/xquasar.git
cd xquasar
python3 -m xquasar
```

첫 번째 명령은 정리할 항목만 보여 줍니다. 정리하려면 다음 명령을 실행하고 `yes`를 입력하세요. 취소하려면 Enter를 누르세요.

```sh
python3 -m xquasar --clean
```

## 정리 대상

- **다시 생성되는 캐시** — `$XDG_CACHE_HOME/thumbnails` 아래의 네 가지 크기별 폴더에 있는 PNG와 `$XDG_CACHE_HOME/fontconfig`에 있는 글꼴 캐시를 확인합니다. 파일 이름과 헤더가 모두 해당 형식과 일치해야 합니다. 기본 캐시 위치는 `~/.cache`입니다.
- **앱 캐시** — `.config`, `.local/share`, `.local/state`, `.cache`의 앱 폴더에서 이름과 헤더로 Chromium 및 Electron의 디스크 캐시와 코드 캐시를 식별합니다. `~/.thumbnails`의 예전 미리보기 이미지와 `~/.local/lib/python3.*/site-packages`에서 원본 소스가 남아 있는 Python 바이트코드도 찾습니다. 브라우저 또는 Python 캐시 파일을 지운 뒤 해당 캐시 폴더가 비면 함께 삭제합니다.
- **Flatpak 프로필** — `~/.var/app`과 설치된 앱 목록을 비교하고 사용자가 정리를 확인한 뒤 다시 검사합니다. 목록을 가져올 수 없으면 프로필을 건너뜁니다. 다른 캐시와 용도를 확인할 수 없는 앱 폴더는 보관합니다.
- **Flatpak 바로가기** — `.local/share/applications`의 메뉴 항목과 `.config/autostart`의 자동 시작 항목은 파일 이름, Flatpak 표식, 실행 명령이 같은 삭제된 앱을 가리킬 때 복구 폴더로 옮깁니다. 이동 직전에 설치된 앱 목록을 다시 확인합니다.
- **다른 앱의 잔여 데이터** — 삭제한 앱의 경로를 알고 있으면 `--leftover`로 지정하세요. 홈 기준 상대 경로이며 `.config`, `.cache`, `.local/share`, `.local/state` 바로 아래의 디렉터리여야 합니다. 여러 개는 옵션을 반복해 지정합니다. 예시 명령은 `python3 -m xquasar --clean --leftover .config/OldEditor`입니다.
- **Firefox 및 데스크톱** — Firefox의 HTTP, 시작, 스크립트, URL, 확장 기능 시작 캐시를 식별합니다. 미리보기 이미지 생성 실패 기록, GStreamer 플러그인 레지스트리, Matplotlib 글꼴 목록도 검사합니다.
- **개발 도구** — 기본 캐시 디렉터리에서 pip wheel, npm·Cargo·Composer 패키지 아카이브, NuGet HTTP 패키지, Go 빌드 기록을 찾습니다. 아카이브를 삭제하면 다음 빌드에서 다시 다운로드해야 할 수 있습니다.

앱 폴더는 프로필과 저장 데이터를 포함해 `~/.xquasar-recovery/<실행 ID>/<원래 경로>`로 이동합니다. 복구하려면 앱을 종료하고 원래 위치에 같은 이름의 항목이 없는지 확인한 뒤 되돌리세요. 디스크 공간은 복구용 사본을 직접 지울 때 확보됩니다.

## 개발 및 도움말

```sh
docker build -t xquasar-dev .
docker run --rm --network=none xquasar-dev
```

컨테이너에서 임시 홈 디렉터리로 테스트를 실행합니다. 일부 경로를 검사하지 못했다면 `Skipped` 메시지를 확인하세요. Flatpak 오류가 있으면 같은 사용자로 `flatpak list --app --columns=application:f`를 확인한 뒤 다시 실행하세요. [정리 및 복구 안내](docs/wiki/Guide-KO.md) · [문제 신고](https://github.com/glitchykid/xquasar/issues)
