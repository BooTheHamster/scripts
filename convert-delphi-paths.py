#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path

linesep = "\n"


def process_line_bytes(line_bytes, out_line, out_lines):
    for byte in line_bytes:
        out_line += f"{byte:00x},00,"

        if len(out_line) > 80:
            intend = True
            out_line += "\\" + linesep
            out_lines.append(out_line)
            out_line = "  " if intend else ""

    return out_line


def create_registry_file(in_file_path: Path):
    out_file_path = Path(in_file_path.parent).joinpath(in_file_path.name).with_suffix('.reg')

    if out_file_path.exists():
        out_file_path.unlink()

    out_lines = [
        "Windows Registry Editor Version 5.00",
        linesep, linesep,
        "[HKEY_LOCAL_MACHINE\\SYSTEM\\ControlSet001\\Control\\Session Manager\\Environment]",
        linesep, linesep
    ]

    out_lines_x64 = [linesep]

    with in_file_path.open("rt", encoding="utf-8") as infile:

        # x32
        byte_line_x32 = "\"DelphiSearchPath\"=hex(2):"
        # x64
        byte_line_x64 = "\"DelphiSearchPathX64\"=hex(2):"

        while True:
            in_line = infile.readline()

            if len(in_line) == 0:
                break

            line_x32 = in_line.strip()
            line_x64 = line_x32.replace("X32", "X64")
            line_x64 = line_x32.replace("x32", "x64")

            line_bytes_x32 = bytes(line_x32 + ";", encoding="utf-8")
            line_bytes_x64 = bytes(line_x64 + ";", encoding="utf-8")

            byte_line_x32 = process_line_bytes(line_bytes_x32, byte_line_x32, out_lines)
            byte_line_x64 = process_line_bytes(line_bytes_x64, byte_line_x64, out_lines_x64)

    if len(byte_line_x32) > 0:
        byte_line_x32 += "00,00" + linesep

    out_lines.append(byte_line_x32)

    if len(byte_line_x64) > 0:
        byte_line_x64 += "00,00" + linesep

    out_lines_x64.append(byte_line_x64)

    with out_file_path.open('wt', encoding="utf-8") as outfile:
        outfile.writelines(out_lines)
        outfile.writelines(out_lines_x64)


if __name__ == "__main__":
    delphi_paths_filename = Path("D:\\Work\\delphi-paths.txt")
    create_registry_file(delphi_paths_filename)
