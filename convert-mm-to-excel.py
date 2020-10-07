#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re
import sys
from pathlib import Path
import xml.etree.ElementTree as ElementTree

FREE_MIND_NODE_TAG = 'node'
FREE_MIND_NODE_TEXT_ATTRIBUTE_TAG = 'TEXT'

time_re = re.compile(r'.+(\s+\(.*\))')
time_number_re = re.compile(r'.*\((\d+[.,]?\d?).*\)')


class NodeInfo:
    def __init__(self, text=""):
        self.text = text
        self.childs: [NodeInfo] = []
        self.time = None
        self.child_time = None

    def append_child(self, child):
        self.childs.append(child)

    def has_childs(self):
        return len(self.childs) > 0

    def update_time(self):

        if not self.has_childs():
            self.child_time = self.time
            return

        for child in self.childs:
            child.update_time()

            child_time = child.time if child.child_time is None else child.child_time

            if child_time is None:
                continue

            self.child_time = child_time if self.child_time is None else self.child_time + child_time

    def get_display_time(self):
        if self.time is None:
            return "" if self.child_time is None else str(self.child_time)

        if self.child_time is None:
            return "" if self.time is None else str(self.time)

        if self.time == self.child_time:
            return str(self.time)

        return f"{self.time} ?? {self.child_time}"


def append_nodes(xml_parent_node, parent_node_info: NodeInfo):
    for child in xml_parent_node:
        if child.tag != FREE_MIND_NODE_TAG:
            continue

        if FREE_MIND_NODE_TEXT_ATTRIBUTE_TAG in child.attrib:
            node = NodeInfo(child.attrib[FREE_MIND_NODE_TEXT_ATTRIBUTE_TAG])

            time_match = time_re.match(node.text)

            if time_match is not None:
                time = time_match[1]
                node.text = node.text.replace(time, "")
                time_number_match = time_number_re.match(time)

                if time_number_match is not None:
                    node.time = float(time_number_match[1].replace(",", "."))

            parent_node_info.append_child(node)
            append_nodes(child, node)


def get_nodes_information(path: Path):
    tree = ElementTree.parse(path)
    root = tree.getroot()
    root_node_info = NodeInfo()

    for child in root:
        if child.tag != FREE_MIND_NODE_TAG:
            continue

        append_nodes(child, root_node_info)

    return root_node_info


def write_to_file_csv(outfile, node_info: NodeInfo, intend: str, number: str):
    if intend is None:
        node_intend = ""
        intend = ""
    else:
        node_intend = intend
        intend += "  "

    node_time = node_info.get_display_time().replace('.', ',')
    node_number = "" if not number else f"{number}."
    node_text = "Итого;" if not node_info.text else f"{node_info.text};"
    line = f"{node_intend}{node_number};{node_text}{node_time}"

    if line:
        outfile.write(line)
        outfile.write("\n")

    child_number = 1
    for child in node_info.childs:
        write_to_file_csv(outfile, child, intend, f"{node_number}{child_number}")
        child_number += 1


def write_to_file(outfile, node_info: NodeInfo, intend: str, number: str):
    if intend is None:
        node_intend = ""
        intend = ""
    else:
        node_intend = intend
        intend += "  "

    node_time = node_info.get_display_time().replace(',', '.')
    node_time = node_time if not node_time else f"({node_time} ч)"
    node_number = "" if not number else f"{number}."
    node_text = "Итого:" if not node_info.text else f" {node_info.text} "
    line = f"{node_intend}{node_number}{node_text}{node_time}"

    if line:
        outfile.write(line)
        outfile.write("\n")

    child_number = 1
    for child in node_info.childs:
        write_to_file(outfile, child, intend, f"{node_number}{child_number}")
        child_number += 1


def process_free_mind_document(path):
    in_file_path = Path(path)
    root_node_info = get_nodes_information(in_file_path)
    root_node_info.update_time()

    out_file_path = Path(in_file_path.parent).joinpath(in_file_path.name).with_suffix('.txt')

    if out_file_path.exists():
        out_file_path.unlink()

    with out_file_path.open('wt', encoding="utf-8") as outfile:
        outfile.write(f"{out_file_path.with_suffix('').name}\n\n")
        write_to_file_csv(outfile, root_node_info, None, None)
        outfile.write("\n-----\n\n!!\n")
        write_to_file(outfile, root_node_info, None, None)


if __name__ == "__main__":
    if len(sys.argv) < 2 or (sys.argv[1] is None):
        print('Usage: python3 convert-mm-to-excel.py path')
        sys.exit(-1)

    argv_iterator = iter(sys.argv)
    next(argv_iterator)

    for arg in argv_iterator:
        process_free_mind_document(arg)
