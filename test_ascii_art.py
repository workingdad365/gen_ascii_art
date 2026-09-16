"""문자 도안, 그라데이션 및 CLI 회귀 검증."""

import io
import os
from pathlib import Path
import re
import string
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from ascii_art import GLYPHS, apply_gradient, main, parse_color, render_text


class RenderTests(unittest.TestCase):
    def test_alphanumeric_glyphs_have_fixed_height_and_width(self):
        characters = string.ascii_uppercase + string.digits
        self.assertEqual(set(GLYPHS), set(characters + " -_."))
        for char in characters:
            with self.subTest(char=char):
                lines = render_text(char).splitlines()
                self.assertEqual(len(lines), 3)
                self.assertEqual([len(line) for line in lines], [5, 5, 5])
        self.assertEqual(
            [len(line) for line in render_text(characters).splitlines()],
            [215, 215, 215],
        )

    def test_crush_regression(self):
        self.assertEqual(render_text("crush"), "\n".join([
            "▄▀▀▀▀ █▀▀▀▄ █   █ ▄▀▀▀▀ █   █",
            "█     █▀▀▀▄ █   █ ▀▀▀▀█ █▀▀▀█",
            " ▀▀▀▀ ▀   ▀  ▀▀▀  ▀▀▀▀  ▀   ▀",
        ]))

    def test_spacing_and_word_spaces(self):
        self.assertEqual(render_text("a b", 0).splitlines()[0], "▄▀▀▀▄   █▀▀▀▄")
        self.assertEqual(render_text("hi"), render_text("HI"))

    def test_numeric_banner_regression(self):
        self.assertEqual(render_text("24"), "\n".join([
            "▄▀▀▀▄ █   █",
            " ▄▀▀  ▀▀▀▀█",
            "▀▀▀▀▀     ▀",
        ]))

    def test_rejects_empty_and_unsupported_input(self):
        for text in ("", "   ", "한글", "café", "ß", "２４", "A!", "A\nB", "\x1b[31m"):
            with self.subTest(text=text), self.assertRaises(ValueError):
                render_text(text)
        with self.assertRaises(ValueError):
            render_text("A", -1)


class GradientTests(unittest.TestCase):
    def test_endpoints_and_shared_horizontal_positions(self):
        self.assertEqual(
            apply_gradient("ABC\nDEF", "#000000", "#FFFFFF"),
            "\x1b[38;2;0;0;0mA\x1b[38;2;128;128;128mB\x1b[38;2;255;255;255mC\x1b[0m\n"
            "\x1b[38;2;0;0;0mD\x1b[38;2;128;128;128mE\x1b[38;2;255;255;255mF\x1b[0m",
        )

    def test_color_preserves_art_and_resets_each_line(self):
        art = render_text("HELLO WORLD-24.04_LTS")
        colored = apply_gradient(art, "FF60FF", "6B50FF")
        self.assertEqual(re.sub(r"\x1b\[[0-9;]*m", "", colored), art)
        self.assertTrue(all(line.endswith("\x1b[0m") for line in colored.splitlines()))

    def test_single_column_and_empty(self):
        self.assertEqual(apply_gradient("A", "123456", "ffffff"), "\x1b[38;2;18;52;86mA\x1b[0m")
        self.assertEqual(apply_gradient("", "123456", "ffffff"), "")

    def test_invalid_colors(self):
        for value in ("#FFF", "red", "#GG0000", "1234567"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_color(value)


class CliTests(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run(
            [sys.executable, str(Path(__file__).with_name("ascii_art.py")), *args],
            capture_output=True, text=True, env={**os.environ, "NO_COLOR": "1"},
        )

    def test_plain_redirect_and_explicit_color(self):
        result = self.run_cli("Hello", "World")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, render_text("Hello World") + "\n")
        result = self.run_cli("Crush", "--color", "always")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("\x1b[38;2;255;96;255m", result.stdout)
        result = self.run_cli("Crush", "--color", "never")
        self.assertNotIn("\x1b", result.stdout)

    def test_invalid_arguments_report_without_traceback(self):
        for args in ([], ["한글"], ["A", "--spacing", "-1"], ["A", "--start", "wrong"]):
            with self.subTest(args=args):
                result = self.run_cli(*args)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, "")
                self.assertNotIn("Traceback", result.stderr)

    def test_ubuntu_version_banner(self):
        for text in ("UBUNTU 24", "UBUNTU 24.04", "NODE-01_LTS", "-_.", "-NODE"):
            with self.subTest(text=text):
                result = self.run_cli("--", text)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, render_text(text) + "\n")
                lines = result.stdout.splitlines()
                self.assertEqual(len(lines), 3)
                self.assertEqual(len(set(map(len, lines))), 1)


class MotdTests(unittest.TestCase):
    def test_saves_utf8_with_default_color_and_plain_override(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "motd"
            for text, options in (
                ("WELCOME", []), ("WELCOME", ["--color", "never"]),
                ("UBUNTU 24", []), ("UBUNTU 24", ["--color", "never"]),
                ("UBUNTU-24.04_LTS", []), ("UBUNTU-24.04_LTS", ["--color", "never"]),
            ):
                with self.subTest(text=text, options=options), patch("ascii_art.MOTD_PATH", target), \
                        patch.object(sys, "argv", ["ascii_art.py", text, "--motd", *options]), \
                        patch.dict(os.environ, {"NO_COLOR": "1"}), \
                        patch("sys.stdout", new_callable=io.StringIO) as stdout:
                    main()
                    saved = target.read_text(encoding="utf-8")
                    self.assertEqual(re.sub(r"\x1b\[[0-9;]*m", "", saved), render_text(text) + "\n")
                    self.assertEqual("\x1b[38;2;" in saved, not options)
                    self.assertEqual(stdout.getvalue(), "")

    def test_invalid_input_preserves_existing_motd(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "motd"
            target.write_text("기존 메시지\n", encoding="utf-8")
            with patch("ascii_art.MOTD_PATH", target), \
                    patch.object(sys, "argv", ["ascii_art.py", "한글", "--motd"]), \
                    patch("sys.stderr", new_callable=io.StringIO), \
                    self.assertRaises(SystemExit) as error:
                main()
            self.assertEqual(error.exception.code, 2)
            self.assertEqual(target.read_text(encoding="utf-8"), "기존 메시지\n")

    def test_permission_error_explains_sudo(self):
        with patch.object(Path, "write_text", side_effect=PermissionError), \
                patch.object(sys, "argv", ["ascii_art.py", "WELCOME", "--motd"]), \
                patch("sys.stderr", new_callable=io.StringIO) as stderr, \
                self.assertRaises(SystemExit) as error:
            main()
        self.assertEqual(error.exception.code, 1)
        self.assertIn("sudo", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
