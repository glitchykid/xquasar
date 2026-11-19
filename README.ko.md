[English](README.md) · [Русский](README.ru.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [简体中文](README.zh-CN.md)

# XQuasar

XQuasar는 Linux 홈 디렉터리를 검사해 정리할 수 있는 항목을 보여 줍니다. 각 줄에서 경로와 처리 방식을 확인한 뒤 원하는 항목을 선택할 수 있습니다.

## 빠른 시작

Linux와 Python 3.12 이상이 필요합니다. 소스 코드를 복제하려면 Git을 설치하세요. Flatpak이 있으면 삭제한 Flatpak 앱의 데이터도 자동으로 찾습니다. 홈 디렉터리를 소유한 사용자 계정으로 실행하세요.

```sh
git clone https://github.com/glitchykid/xquasar.git
cd xquasar
python3 -m xquasar
```

첫 명령은 목록만 보여 줍니다. 정리하려면 다음 명령을 실행하고 번호를 공백으로 구분해 입력하세요. 전체 선택은 `all`, 최종 확인은 `yes`입니다. 아무것도 입력하지 않고 Enter를 누르면 취소됩니다.

```sh
python3 -m xquasar --clean
```

## 정리 대상

- **미리보기 이미지** — `$XDG_CACHE_HOME/thumbnails`(기본값 `~/.cache/thumbnails`) 아래 네 개의 크기별 폴더에서 이름이 32자리 16진수인 표준 PNG 캐시 파일을 선택해 삭제합니다.
- **빈 폴더** — 선택한 폴더가 여전히 비어 있으면 삭제합니다. 숨김 디렉터리, Git 작업 트리, 별도로 마운트된 경로는 건너뜁니다. 기본 사용자 폴더와 XDG에 지정한 사용자 폴더는 보존합니다. 정리 후 비게 된 상위 폴더는 다음 검사에서 찾을 수 있습니다.
- **Flatpak 잔여 데이터** — `~/.var/app`과 설치된 앱 목록을 대조하고 사용자가 확인한 뒤 다시 대조합니다. 목록을 얻을 수 없으면 해당 폴더를 건너뜁니다.
- **다른 앱의 잔여 데이터** — 삭제한 앱의 경로를 알고 있으면 `--leftover`로 지정하세요. 홈 기준 상대 경로이며 `.config`, `.cache`, `.local/share`, `.local/state` 바로 아래의 디렉터리여야 합니다. 여러 개는 옵션을 반복해 지정합니다. 예시 명령은 `python3 -m xquasar --clean --leftover .config/OldEditor`입니다.

앱 폴더는 프로필과 저장 데이터를 포함해 `~/.xquasar-recovery/<실행 ID>/<원래 경로>`로 이동합니다. 복구하려면 앱을 종료하고 원래 위치에 같은 이름의 항목이 없는지 확인한 뒤 되돌리세요. 디스크 공간은 복구용 사본을 직접 지울 때 확보됩니다.

## 개발 및 도움말

```sh
docker build -t xquasar-dev .
docker run --rm --network=none xquasar-dev
```

컨테이너에서 임시 홈 디렉터리로 테스트를 실행합니다. 일부 경로를 검사하지 못했다면 `Skipped` 메시지를 확인하세요. Flatpak 오류가 있으면 같은 사용자로 `flatpak list --app --columns=application:f`를 확인한 뒤 다시 실행하세요. [정리 및 복구 안내](docs/wiki/Guide-KO.md) · [문제 신고](https://github.com/glitchykid/xquasar/issues)
