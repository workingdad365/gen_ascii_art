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


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("text", nargs="+", help="변환할 문자열 (영문, 숫자, - _ . 및 공백)")
    parser.add_argument("--spacing", type=int, default=1, help="글자 간격 (기본: 1)")
    parser.add_argument("--start", default=DEFAULT_START, help="그라데이션 시작 HEX 색상")
    parser.add_argument("--end", default=DEFAULT_END, help="그라데이션 끝 HEX 색상")
    parser.add_argument("--motd", action="store_true", help="색상을 포함하여 /etc/motd에 저장함")
    parser.add_argument(
        "--color", choices=("auto", "always", "never"), default="auto",
        help="색상 출력: auto는 터미널에서 NO_COLOR를 존중하며, --motd는 항상 색상을 포함함",
    )
    args = parser.parse_args()
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
        return
    try:
        print(art)
    except BrokenPipeError:
        sys.stdout = open(os.devnull, "w")


if __name__ == "__main__":
    main()
