#!/usr/bin/env python
# -*- coding: utf8 -*-

from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division

import csv
import json
import urllib2
from bs4 import BeautifulSoup

CHART_URL = "http://ryanhowerter.net/colors"


def get_chart(url=CHART_URL):
    response = urllib2.urlopen(url)
    return response.read()


def write_csv(headers, data, filename='colors.csv'):
    with open(filename, 'wb') as csvfile:
        colorwriter = csv.writer(csvfile, delimiter=b',',
                                 quotechar=b'"')

        colorwriter.writerow(headers)
        for row in data:
            colorwriter.writerow(row)


def write_json(names, values, filename='colors.json'):
    data = []

    for color in values:
        dataset = dict(zip(names, color))
        data.append(dataset)

    with open(filename, 'wb') as jsonfile:
        json.dump(data, jsonfile, indent=4)


def main():
    html = get_chart()

    soup = BeautifulSoup(html)
    table = soup.find_all("table")[0]

    headings = [th.get_text().replace(u'\xa0', ' ')
                for th in table.find("tr").find_all("th")]

    assert len(headings) == 24

    print (headings)

    datasets = []
    for row in table.find_all('tr')[1:]:
        rowdata = [td.get_text().replace(u'\xa0', ' ')
                   for td in row.find_all("td")]

        assert len(rowdata) == len(headings) + 1

        rowdata = rowdata[0:13] + [[rowdata[13], rowdata[14]], ] + rowdata[15:]
        assert len(rowdata) == len(headings)

        datasets.append(rowdata)

    write_csv(headings, datasets)
    write_json(headings, datasets)


if __name__ == '__main__':
    main()
