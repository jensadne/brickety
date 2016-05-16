#!/usr/bin/python
#-*- coding: utf-8 -*-

"""
    Util to convert files from Lego Digital Designer into wishlists for Bricklink
    Copyright (C) 2015  Greger Stolt Nilsen

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as published
    by the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""

from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division

from collections import defaultdict
import os
import zipfile
import csv
import argparse

import xml.etree.ElementTree as ET


class LookupTable(object):
    def __init__(self, filename):
        self.data = []
        if filename is None:
            raise IOError

        base_dir = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(base_dir, filename)) as colorfile:
            colorreader = csv.DictReader(colorfile, delimiter=b';')
            self.data = [row for row in colorreader]

    def by_legoid(self, legoid):
        for c in self.data:
            if len(c['LEGOID']) > 0 and int(c['LEGOID']) == int(legoid):
                return c
        return None


def extract_xml(filename):
    with zipfile.ZipFile(filename, 'r') as inzip:
        with inzip.open('IMAGE100.LXFML') as inxml:
            # print(inxml.read())
            return inxml.read()


def parse_xml(indata):
    root = ET.fromstring(indata)
    assert root.tag == 'LXFML'

    parts = defaultdict(int)

    for part in root.iter('Part'):
        design_id = part.attrib['designID']
        colors = part.attrib['materials'].split(',')
        color = int(max(colors))
        parts[(design_id, color)] += 1
    return parts


def bricklink_convert(parts):
    colortable = LookupTable('colorlist.csv')
    elementtable = LookupTable('elementlist.csv')

    ret = []
    for part in parts:
        item_id, lego_color = part

        color = colortable.by_legoid(lego_color)['BLID']
        element = elementtable.by_legoid(item_id)

        if element is not None:
            item_id = element['BLID']

        quantity = parts[part]
        ret.append((item_id, color, quantity))

    return ret


def make_wanted_list(parts, notify=False, condition=None, listid=None):
    out_data = []

    out_data.append('<INVENTORY>')
    for item_id, color, quantity in parts:
        out_data.append('\t<ITEM>')
        out_data.append('\t\t<ITEMTYPE>P</ITEMTYPE>')
        out_data.append('\t\t<ITEMID>%s</ITEMID>' % item_id)
        out_data.append('\t\t<COLOR>%s</COLOR>' % color)
        out_data.append('\t\t<MINQTY>%d</MINQTY>' % quantity)
        out_data.append('\t\t<NOTIFY>%s</NOTIFY>' % ('Y' if notify else 'N'))

        if condition is not None:
            assert condition.lower() == 'new' or condition.lower() == 'used'
            out_data.append('\t\t<CONDITION>%s</CONDITION>' % condition.upper()[0])

        if listid is not None:
            out_data.append('\t\t<WANTEDLISTID>%s</WANTEDLISTID>' % listid)

        out_data.append('\t</ITEM>')

    out_data.append('</INVENTORY>')
    return "\n".join(out_data)


def init_arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('ldd_file', type=str)
    parser.add_argument("--notify", action="store_true", help="Requests notification of availability")
    parser.add_argument("--condition", choices=['new', 'used'], help="Specify condition new/used")
    parser.add_argument("--listid", type=str, help="Specify wantedlist id to add to")
    return parser


def main():
    parser = init_arg_parser()
    args = parser.parse_args()

    infile = args.ldd_file
    notify = args.notify
    condition = args.condition
    listid = args.listid

    if not os.path.isfile(infile):
        raise IOError

    filename = infile
    xml_data = extract_xml(filename)
    parts = bricklink_convert(parse_xml(xml_data))
    print(make_wanted_list(parts, notify=notify, condition=condition, listid=listid))


if __name__ == '__main__':
    main()
