# 영문·숫자 블록 아트 생성기

Crush 로고 스타일의 3줄 영문·숫자 블록 아트와 수평 보라색 그라데이션을 출력하는 Python 스크립트임.

## 실행

Python 3.10 이상이 필요하며 외부 패키지 설치는 불필요함.

```bash
python3 ascii_art.py CRUSH
python3 ascii_art.py "Hello World"
```

영문 A–Z, a–z, 숫자 0–9, 기호 `-`, `_`, `.` 및 공백을 지원하며 소문자는 대문자로 변환함. 각 글자는 유니코드 블록 문자 `█`, `▀`, `▄`로 구성함. 고정폭 글꼴과 True Color를 지원하는 터미널 사용을 권장함.

입력이 `-`로 시작하면 옵션으로 해석되지 않도록 문자열 앞에 `--`를 넣음. 예: `python3 ascii_art.py --color never -- "-NODE"`.

## 옵션

```bash
# 글자 간격 조절
python3 ascii_art.py HELLO --spacing 2

# 시작색과 끝색 지정
python3 ascii_art.py HELLO --start '#FFB3FF' --end '#8660FF'

# 색상 없는 도안 저장
python3 ascii_art.py "Hello World" --color never > logo.txt

# ANSI 색상 코드가 포함된 도안 저장 및 재출력
python3 ascii_art.py CRUSH --color always > logo.ansi
cat logo.ansi
```

기본 색상은 `#FF60FF` → `#6B50FF`이며 RGB 선형 보간을 사용함. `--color auto`가 기본값이며 터미널 출력에만 색상을 적용함. 비어 있지 않은 `NO_COLOR` 환경변수 설정 시 자동 색상을 비활성화함. `--color always`는 출력 대상과 `NO_COLOR`에 관계없이 색상을 적용함.

긴 문자열은 터미널 너비를 넘으면 줄바꿈될 수 있으므로 창 너비나 글자 간격 조절이 필요함.

## 로그인 메시지로 사용

```bash
sudo python3 ascii_art.py WELCOME --motd
sudo python3 ascii_art.py "UBUNTU 24.04" --motd
sudo python3 ascii_art.py "NODE-01_LTS" --motd
```

`/etc/motd`를 생성한 아트로 덮어씀. `--motd`는 출력 대상과 `NO_COLOR`에 관계없이 기본적으로 ANSI 색상을 포함하여 UTF-8로 저장함. 색상 없는 저장은 `--color never`를 추가하여 지정함.

### 새 터미널에서 MOTD가 표시되지 않는 경우

Ubuntu에서도 `/etc/motd`를 사용하지만, 새 터미널 창을 여는 과정이 MOTD를 출력하는 로그인 과정을 거치는 것은 아님. 특히 WSL에서 zsh를 바로 실행하면 MOTD가 자동으로 표시되지 않을 수 있음.

먼저 저장된 아트가 정상적으로 출력되는지 확인함.

```bash
cat /etc/motd
```

파일이 없거나 비어 있다면 위의 `--motd` 명령으로 다시 저장함. `cat`으로는 보이지만 새 터미널에서 표시되지 않는다면, zsh 사용 시 `~/.zshrc` 맨 위에 다음 한 줄을 추가함.

```zsh
[[ -o interactive && -t 1 && -r /etc/motd ]] && cat /etc/motd
```

대화형 셸이고 출력 대상이 터미널이며 파일을 읽을 수 있을 때만 출력함. Powerlevel10k instant prompt 로딩 블록이 있다면 해당 블록보다 위에 배치함.

설정 파일의 문법을 확인한 뒤 새 터미널 창을 열어 표시 여부를 확인함.

```bash
zsh -n ~/.zshrc
```

## 검증

```bash
python3 -m unittest -v
```

## 참고 출처

글자 스타일과 기본 색상은 [Charmbracelet Crush](https://github.com/charmbracelet/crush)의 `internal/ui/logo/letterforms.go` 및 기본 테마를 참고함. A–Z 도안 결합과 ANSI 출력은 독립적인 Python 구현임.

Crush 참고 부분의 저작권은 Copyright 2025–2026 Charmbracelet, Inc.에 귀속됨. 해당 소스의 이용 조건은 [FSL-1.1-MIT](https://github.com/charmbracelet/crush/blob/main/LICENSE.md)에 명시됨.
