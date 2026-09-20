#!/usr/bin/env python3
"""영문, 숫자와 일부 기호를 3줄 블록 문자와 수평 그라데이션으로 출력함."""

import argparse
import os
from pathlib import Path
import re
import sys


# 영문과 숫자는 가로 5칸, 모든 도안은 세로 3줄로 구성함.
GLYPHS = {
    "A": ("▄▀▀▀▄", "█▀▀▀█", "▀   ▀"),
    "B": ("█▀▀▀▄", "█▀▀▀▄", "▀▀▀▀ "),
    "C": ("▄▀▀▀▀", "█    ", " ▀▀▀▀"),
    "D": ("█▀▀▀▄", "█   █", "▀▀▀▀ "),
    "E": ("█▀▀▀▀", "█▀▀▀▀", "▀▀▀▀▀"),
    "F": ("█▀▀▀▀", "█▀▀▀ ", "▀    "),
    "G": ("▄▀▀▀▀", "█ ▀▀█", " ▀▀▀▀"),
    "H": ("█   █", "█▀▀▀█", "▀   ▀"),
    "I": ("▀▀█▀▀", "  █  ", "▀▀▀▀▀"),
    "J": ("   ▀█", "█   █", " ▀▀▀ "),
    "K": ("█  ▄▀", "█▀▀▄ ", "▀   ▀"),
    "L": ("█    ", "█    ", "▀▀▀▀▀"),
    "M": ("█▄ ▄█", "█ ▀ █", "▀   ▀"),
    "N": ("█▄  █", "█ ▀▄█", "▀   ▀"),
    "O": ("▄▀▀▀▄", "█   █", " ▀▀▀ "),
    "P": ("█▀▀▀▄", "█▀▀▀ ", "▀    "),
    "Q": ("▄▀▀▀▄", "█ ▄ █", " ▀▀▀▄"),
    "R": ("█▀▀▀▄", "█▀▀▀▄", "▀   ▀"),
    "S": ("▄▀▀▀▀", "▀▀▀▀█", "▀▀▀▀ "),
    "T": ("▀▀█▀▀", "  █  ", "  ▀  "),
    "U": ("█   █", "█   █", " ▀▀▀ "),
    "V": ("█   █", "▀▄ ▄▀", "  ▀  "),
    "W": ("█   █", "█ ▄ █", "▀▀ ▀▀"),
    "X": ("▀▄ ▄▀", " ▄▀▄ ", "▀   ▀"),
    "Y": ("█   █", "▀▀▀▀█", "▀▀▀▀ "),
    "Z": ("▀▀▀▀█", " ▄▀▀ ", "▀▀▀▀▀"),
    "0": ("▄▀▀▀▄", "█ ▄ █", " ▀▀▀ "),
    "1": (" ▄█  ", "  █  ", "▀▀▀▀▀"),
    "2": ("▄▀▀▀▄", " ▄▀▀ ", "▀▀▀▀▀"),
    "3": ("▀▀▀▀▄", " ▀▀▀█", "▀▀▀▀ "),
    "4": ("█   █", "▀▀▀▀█", "    ▀"),
    "5": ("█▀▀▀▀", "▀▀▀▀█", "▀▀▀▀ "),
    "6": ("▄▀▀▀ ", "█▀▀▀▄", " ▀▀▀ "),
    "7": ("▀▀▀▀█", "   █ ", "  ▀  "),
    "8": ("▄▀▀▀▄", "█▀▀▀█", " ▀▀▀ "),
    "9": ("▄▀▀▀▄", "▀▀▀▀█", " ▀▀▀ "),
    "-": ("   ", "▀▀▀", "   "),
    "_": ("     ", "     ", "▄▄▄▄▄"),
    ".": (" ", " ", "▄"),
    " ": ("   ", "   ", "   "),
}

DEFAULT_START = "#FF60FF"
DEFAULT_END = "#6B50FF"
MOTD_PATH = Path("/etc/motd")
HOOK_MARKER = "# gen_ascii_art: 로그인 셸 시작 시 MOTD 출력"
# 셸별 (구문 추가 후보 파일, 중복 확인용 추가 파일). 후보는 셸이 읽는 우선순위 순서임.
HOOK_FILES = {
    "zsh": ((".zprofile",), (".zshrc", ".zlogin")),
    "bash": ((".bash_profile", ".bash_login", ".profile"), (".bashrc",)),
}


def parse_color(value: str) -> tuple[int, int, int]:
    """HEX 색상을 RGB 값으로 변환함."""
    if not re.fullmatch(r"#?[0-9a-fA-F]{6}", value):
        raise ValueError("색상은 #RRGGBB 형식이어야 합니다.")
    value = value.removeprefix("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def render_text(text: str, spacing: int = 1) -> str:
    """영문, 숫자, 기호와 공백을 동일한 너비의 3줄 도안으로 결합함."""
    if spacing < 0:
        raise ValueError("글자 간격은 0 이상이어야 합니다.")
    if not text or not text.strip(" "):
        raise ValueError("변환할 문자열을 입력해 주세요.")
    if re.search(r"[^a-zA-Z0-9 ._-]", text):
        raise ValueError("영문 A–Z, a–z, 숫자 0–9, 기호 - _ . 및 공백만 지원합니다.")
    letters = [GLYPHS[char] for char in text.upper()]
    gap = " " * spacing
    return "\n".join(gap.join(letter[row] for letter in letters) for row in range(3))


def apply_gradient(art: str, start: str, end: str) -> str:
    """전체 도안의 가로 좌표를 기준으로 RGB 색상을 선형 보간함."""
    first, last = parse_color(start), parse_color(end)
    lines = art.split("\n")
    width = max(map(len, lines))
    ramp = [
        tuple(round(a + (b - a) * x / max(1, width - 1)) for a, b in zip(first, last))
        for x in range(width)
    ]
    result = []
    for line in lines:
        colored = []
        for x, char in enumerate(line):
            r, g, b = ramp[x]
            colored.append(f"\x1b[38;2;{r};{g};{b}m{char}")
        result.append("".join(colored) + "\x1b[0m" if line else "")
    return "\n".join(result)


def resolve_login_user():
    """sudo 실행 시에는 원 사용자, 그 외에는 현재 사용자의 계정 정보를 반환함."""
    import pwd  # Unix 전용 모듈이므로 필요 시점에만 불러옴.

    sudo_user = os.environ.get("SUDO_USER")
    try:
        return pwd.getpwnam(sudo_user) if sudo_user else pwd.getpwuid(os.getuid())
    except KeyError as exc:
        raise OSError(f"사용자 계정 정보를 찾을 수 없습니다: {exc}") from exc


def install_shell_hook() -> tuple[Path, bool]:
    """로그인 셸 설정 파일에 MOTD 출력 구문을 추가하고 (대상 파일, 추가 여부)를 반환함."""
    user = resolve_login_user()
    shell = Path(user.pw_shell).name
    if shell not in HOOK_FILES:
        raise ValueError(f"지원하지 않는 로그인 셸입니다: {user.pw_shell} (zsh, bash만 지원)")
    home = Path(user.pw_dir)
    candidates, extras = HOOK_FILES[shell]
    command = f"cat {MOTD_PATH}"
    for name in candidates + extras:
        path = home / name
        if path.is_file() and command in path.read_text(encoding="utf-8", errors="replace"):
            return path, False
    target = next((home / name for name in candidates if (home / name).is_file()), home / candidates[-1])
    existed = target.exists()
    content = target.read_text(encoding="utf-8", errors="replace") if existed else ""
    prefix = "" if not content else ("\n" if content.endswith("\n") else "\n\n")
    with target.open("a", encoding="utf-8") as file:
        file.write(f"{prefix}{HOOK_MARKER}\n[ -t 1 ] && [ -r {MOTD_PATH} ] && {command}\n")
    if not existed:
        # sudo로 생성한 파일이 root 소유로 남지 않도록 원 사용자에게 귀속시킴.
        os.chown(target, user.pw_uid, user.pw_gid)
    return target, True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("text", nargs="+", help="변환할 문자열 (영문, 숫자, - _ . 및 공백)")
    parser.add_argument("--spacing", type=int, default=1, help="글자 간격 (기본: 1)")
    parser.add_argument("--start", default=DEFAULT_START, help="그라데이션 시작 HEX 색상")
    parser.add_argument("--end", default=DEFAULT_END, help="그라데이션 끝 HEX 색상")
    parser.add_argument("--motd", action="store_true", help="색상을 포함하여 /etc/motd에 저장함")
    parser.add_argument(
        "--shell-hook", action="store_true",
        help="--motd와 함께 사용하며, 로그인 셸(zsh, bash) 설정 파일에 /etc/motd 출력 구문을 추가함",
    )
    parser.add_argument(
        "--color", choices=("auto", "always", "never"), default="auto",
        help="색상 출력: auto는 터미널에서 NO_COLOR를 존중하며, --motd는 항상 색상을 포함함",
    )
    args = parser.parse_args()
    if args.shell_hook and not args.motd:
        parser.error("--shell-hook은 --motd와 함께 사용해야 합니다.")
    try:
        parse_color(args.start)
        parse_color(args.end)
        art = render_text(" ".join(args.text), args.spacing)
        use_color = args.color == "always" or (
            args.color == "auto" and (
                args.motd or (sys.stdout.isatty() and not os.environ.get("NO_COLOR"))
            )
        )
        if use_color:
            art = apply_gradient(art, args.start, args.end)
    except ValueError as exc:
        parser.error(str(exc))
    if args.motd:
        try:
            MOTD_PATH.write_text(art + "\n", encoding="utf-8")
        except PermissionError:
            parser.exit(1, f"{MOTD_PATH} 쓰기 권한이 필요합니다. sudo로 실행해 주세요.\n")
        except OSError as exc:
            parser.exit(1, f"MOTD 저장 실패: {exc}\n")
        if args.shell_hook:
            try:
                target, added = install_shell_hook()
            except (OSError, ValueError) as exc:
                parser.exit(1, f"MOTD는 저장했으나 셸 설정 파일 등록에 실패했습니다: {exc}\n")
            print(f"{target}에 MOTD 출력 구문을 추가했습니다." if added
                  else f"{target}에 MOTD 출력 구문이 이미 있어 변경하지 않았습니다.")
        return
    try:
        print(art)
    except BrokenPipeError:
        sys.stdout = open(os.devnull, "w")


if __name__ == "__main__":
    main()
