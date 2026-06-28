#!/usr/bin/env python
"""Audit CIRCVIE3 source text for calculator-safe rendering."""

import argparse
import re
import sys
from pathlib import Path


STRING_RE = re.compile(r'"((?:\\.|[^"\\])*)"')


def decode_c_string(raw):
    return bytes(raw, "ascii").decode("unicode_escape")


def audit_ascii(paths):
    bad = []
    for path in paths:
        data = path.read_bytes()
        if any(byte > 127 for byte in data):
            bad.append(path)
    return bad


def audit_string_lengths(paths, max_len):
    bad = []
    for path in paths:
        for line_no, line in enumerate(path.read_text(encoding="ascii").splitlines(), 1):
            for match in STRING_RE.finditer(line):
                value = decode_c_string(match.group(1))
                if len(value) > max_len:
                    bad.append((path, line_no, len(value), value))
    return bad


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--max-len", type=int, default=39)
    args = parser.parse_args()

    root = Path(args.root)
    src_files = sorted((root / "src").glob("*.c")) + sorted((root / "src").glob("*.h"))
    text_files = src_files + [root / "Makefile", root / "README.md"]
    text_files = [path for path in text_files if path.exists()]

    ascii_bad = audit_ascii(text_files)
    len_bad = audit_string_lengths(src_files, args.max_len)

    for path in ascii_bad:
        print("NONASCII {}".format(path))
    for path, line_no, length, value in len_bad:
        print("{}:{} len={} {}".format(path, line_no, length, value))

    if ascii_bad or len_bad:
        return 1

    print("OK: ASCII files and C strings <= {} chars".format(args.max_len))
    return 0


if __name__ == "__main__":
    sys.exit(main())
