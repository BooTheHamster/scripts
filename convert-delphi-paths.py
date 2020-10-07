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


def get_variable_name(is_x_64: bool, counter: int):
    arch = "X64" if is_x_64 else ""
    counter_str = "" if counter <= 0 else f"{counter}"
    return f"\"DelphiSearchPath{arch}{counter_str}\"=hex(2):"


def create_registry_file(in_file_path: Path):
    out_file_path = Path(in_file_path.parent).joinpath(in_file_path.name).with_suffix('.reg')

    if out_file_path.exists():
        out_file_path.unlink()

    out_lines = [
        "Windows Registry Editor Version 5.00", linesep,
        linesep,
        "[HKEY_LOCAL_MACHINE\\SYSTEM\\ControlSet001\\Control\\Session Manager\\Environment]", linesep,
        linesep,
    ]

    out_lines_x64 = []

    variable_to_lines = {}
    variables_count = 0
    current_variable_length = 0

    with in_file_path.open("rt", encoding="utf-8") as infile:
        in_lines = infile.readlines()

    for line in in_lines:
        line = line.strip()

        if len(line) <= 0:
            continue

        length = len(line) + 1

        if (current_variable_length + length) > 2040:
            print(f"{current_variable_length}, {length} {line}")
            variables_count += 1
            current_variable_length = 0
        else:
            current_variable_length += length

        if variables_count not in variable_to_lines:
            variable_to_lines[variables_count] = []

        variable_to_lines[variables_count].append(line)

    for variable_number, variable_paths in variable_to_lines.items():

        out_line_x32 = get_variable_name(False, variable_number)
        out_line_x64 = get_variable_name(True, variable_number)
        add_delimiter = False

        for path in variable_paths:
            path = (";" if add_delimiter else "") + path
            add_delimiter = True
            path_x64 = path.replace("X32", "X64").replace("x32", "x64").replace("Win32", "Win64")

            path_bytes = bytes(path, encoding="utf-8")
            path_bytes_x64 = bytes(path_x64, encoding="utf-8")

            out_line_x32 = process_line_bytes(path_bytes, out_line_x32, out_lines)
            out_line_x64 = process_line_bytes(path_bytes_x64, out_line_x64, out_lines_x64)

        if len(out_line_x32) > 0:
            out_line_x32 += "00,00" + linesep

        out_lines.append(out_line_x32)

        if len(out_line_x64) > 0:
            out_line_x64 += "00,00" + linesep

        out_lines_x64.append(out_line_x64)

    with out_file_path.open('wt', encoding="utf-8") as outfile:
        outfile.writelines(out_lines)
        outfile.writelines(out_lines_x64)


if __name__ == "__main__":
    delphi_paths_filename = Path("D:\\Work\\delphi-paths.txt")
    create_registry_file(delphi_paths_filename)
