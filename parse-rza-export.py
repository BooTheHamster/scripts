#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
from pathlib import Path
import xml.etree.ElementTree as ElementTree

g_estimations = ('Н', 'НО', 'ПУ', 'НЛ', 'НИ', 'П', 'Д', 'ПН', '??', 'ПУ2', 'ПУ1')


def append_nodes(xml_parent_node: ElementTree):

    for xml_child in xml_parent_node:
        if ('ClassName' in xml_child.attrib) and (xml_child.attrib['ClassName'] == 'TRZASecondEquipmentCard'):
            print_estimation(xml_child)
        else:
            append_nodes(xml_child)


def print_estimation(xml_parent_node: ElementTree):

    has_estimation = False
    for xml_child in xml_parent_node:
        if xml_child.tag == 'Estimation':
            has_estimation = True;
            break

    if not has_estimation:
        print("!!!!")

    for xml_child in xml_parent_node:
        if (xml_child.tag == 'Estimation') and (xml_child.text not in g_estimations):
            print(f"Estimation: {xml_child.text}")


def get_nodes_information(path: Path):
    tree = ElementTree.parse(path)
    root = tree.getroot()

    for child in root:
        append_nodes(child)


def parse_export(file: Path):
    print("Begin parse ...")
    get_nodes_information(file)
    print("Done.")


if __name__ == "__main__":
    if len(sys.argv) < 2 or (sys.argv[1] is None):
        print('Usage: python3 parse-rza-export.py path_to_xml')
        sys.exit(-1)

    g_file = Path(sys.argv[1])

    parse_export(g_file)
