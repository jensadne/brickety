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

import os
import sys
import zipfile
import csv
import argparse

import xml.etree.ElementTree as ET

parts = {}


class LookupTable(object):
    data = []

    def read(self, filename):
        if filename is None:
            raise IOError

        with open(filename) as colorfile:
            colorreader = csv.DictReader(colorfile, delimiter=b';')
            for row in colorreader:
                self.data.append(row)

    def by_legoid(self, legoid):
        for c in self.data:
            if len(c['LEGOID']) > 0:
                if int(c['LEGOID']) == int(legoid):
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

    for part in root.iter('Part'):
        #print(part.attrib)
        design_id = part.attrib['designID']
        colors = part.attrib['materials'].split(',')
        color = int(max(colors))
        if (design_id, color) in parts:
            parts[(design_id, color)] += 1
        else:
            parts[(design_id, color)] = 1

    return parts


def make_wanted_list(parts, colortable, elementtable, notify=False, condition=None, listid=None):
    out_data = []

    out_data.append('<INVENTORY>')
    for part in parts:
        lego_color = part[1]
        item_id = part[0]

        color = colortable.by_legoid(lego_color)

        element = elementtable.by_legoid(item_id)

        if element is not None:
            item_id = element['BLID']

        out_data.append('\t<ITEM>')
        out_data.append('\t\t<ITEMTYPE>P</ITEMTYPE>')
        out_data.append('\t\t<ITEMID>%s</ITEMID>' % item_id)
        out_data.append('\t\t<COLOR>%s</COLOR>' % color['BLID'])
        out_data.append('\t\t<MINQTY>%d</MINQTY>' % parts[part])
        
        if notify:
            out_data.append('\t\t<NOTIFY>Y</NOTIFY>')
        else:
            out_data.append('\t\t<NOTIFY>N</NOTIFY>')

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

    print(args)

    infile = args.ldd_file
    notify = args.notify
    condition = args.condition
    listid = args.listid

    if not os.path.isfile(infile):
        raise IOError

    ct = LookupTable()
    ct.read('colorlist.csv')

    et = LookupTable()
    et.read('elementlist.csv')

    filename = infile
    xml_data = extract_xml(filename)
    parts = parse_xml(xml_data)
    print(make_wanted_list(parts,
                           colortable=ct,
                           elementtable=et,
                           notify=notify,
                           condition=condition,
                           listid=listid))


if __name__ == '__main__':
    main()
