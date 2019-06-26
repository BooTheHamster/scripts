#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
from pathlib import Path
from xml.etree import ElementTree


class Node:
    def __init__(self, tag=""):
        self.tag = tag
        self.childs: {str, Node} = {}

    def append_child(self, child):
        self.childs[child.tag] = child

    def has_childs(self):
        return len(self.childs) > 0


def append_nodes(xml_parent_node, parent_node: Node):

    child_node = Node(xml_parent_node.tag)
    parent_node.append_child(child_node)

    for xml_child in xml_parent_node:
        append_nodes(xml_child, child_node)


def get_nodes_information(path: Path):
    tree = ElementTree.parse(path)
    root = tree.getroot()
    root_node = Node(root.tag)

    for child in root:
        append_nodes(child, root_node)

    return root_node


def compare_childs(prefix: str, original_node: Node, compare_node: Node):
    for key, node in original_node.childs.items():
        next_prefix = f"{prefix}{key}."

        if key not in compare_node.childs:
            print(f"{prefix}{key}")
            continue

        compare_childs(next_prefix, node, compare_node.childs[key])


def compare_structure(original_file, file):
    """
    Сравнение структуры файлов.

    :param original_file: Оригинальный файл.
    :param file: Файл для сравнения.
    :return:
    """

    original_root_node = get_nodes_information(original_file)
    root_node = get_nodes_information(file)

    # Корневой узел не используется в сравнении.
    # Сравнение начинается с дочерних.
    # Для быстрого поиска формируется словарь дочерних узлов для сравниваемого файла.
    for original_key, original_node in original_root_node.childs.items():

        if original_key not in root_node.childs:
            print(f'{original_key}')
            continue

        compare_childs(f"{original_key}.", original_node, root_node.childs[original_key])


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print('Usage: python3 compare-rza-xml-structure.py original-file.xml file.xml')
        sys.exit(-1)

    g_original_file = Path(sys.argv[1])
    g_file = Path(sys.argv[2])
    
    compare_structure(g_original_file, g_file)
