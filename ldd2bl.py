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

import xml.etree.ElementTree as ET

parts = {}


class ColorTable(object):
    data = []

    def read(self, filename=None):
        if filename is None:
            filename = 'colorlist.csv'

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


def make_wanted_list(parts, colortable):
    out_data = []

    out_data.append('<INVENTORY>')
    for part in parts:
        lego_color = part[1]
        item_id = part[0]

        color = colortable.by_legoid(lego_color)
        
        out_data.append('\t<ITEM>')
        out_data.append('\t\t<ITEMTYPE>P</ITEMTYPE>')
        out_data.append('\t\t<ITEMID>%s</ITEMID>' % part[0])
        out_data.append('\t\t<COLOR>%s</COLOR>' % color['BLID'])
        out_data.append('\t\t<MINQTY>%d</MINQTY>' % parts[part])
        out_data.append('\t</ITEM>')

    out_data.append('</INVENTORY>')
    return "\n".join(out_data)


def main():
    if not os.path.isfile(sys.argv[1]):
        raise IOError

    ct = ColorTable()
    ct.read()

    filename = sys.argv[1]
    xml_data = extract_xml(filename)
    parts = parse_xml(xml_data)
    print(make_wanted_list(parts, colortable=ct))


if __name__ == '__main__':
    main()
