#!usr/bin/python
# -*- coding: utf8 -*-
encoding='utf8'

import sys
import xml.sax
import xml.dom.minidom
import zipfile
import codecs
from OpenOffice_document import extractAll

class CalcHandler(xml.sax.handler.ContentHandler):
    tag_table = "table:table"
    tag_row   = "table:table-row"
    tag_cell  = "table:table-cell"
    tag_table_name = "table:name"

    def __init__(self):
        self.chars  = []
        self.cells  = []
        self.rows   = []
        self.tables = {}
        self.table_name = u''

    def characters(self, content):
        self.chars.append(content)

    def startElement(self, name, attrs):
        if name == self.tag_cell:
            self.chars = []
        elif name == self.tag_row:
            self.cells = []
        elif name == self.tag_table:
            self.rows  = []
            self.table_name = attrs[self.tag_table_name]

    def endElement(self, name):
        if name == self.tag_cell:
            self.cells.append(''.join(self.chars))
        elif name == self.tag_row:
            self.rows.append(self.cells)
        elif name == self.tag_table:
            self.tables[self.table_name] = self.rows

def parseODS(filename):
    fd = zipfile.ZipFile(filename, 'r')
    content = fd.read("content.xml")
    fd.close()
    calcHandler=CalcHandler()
    xml.sax.parseString(content, calcHandler)
    return calcHandler.tables

def filterBlank_rows(table):
    return filter(len, [filter(len, [cell.strip() for cell in row]) for row in table])

def cropColumns(table, start, finish):
    return zip(*(zip(*table)[start:finish]))

from pprint import pprint

def table2dom(table, table_name):
    names = table[0]
    doc = xml.dom.minidom.Document()
    doc.encoding = "UTF-8"
    root = doc.createElement(table_name)
    root.attributes['type'] = 'table'
    doc.appendChild(root)
    for row in table[1:]:
        row_node = root.appendChild(doc.createElement('ROW'))
        for i, cell in enumerate(row):
            node = row_node.appendChild(doc.createElement(names[i]))
            node.appendChild(doc.createTextNode(cell))
    return root

def table2csv(table):
    return u'\n'.join([u'\t'.join([u'"%s"' % (cell) for cell in row]) for row in table])

if __name__ == '__main__':
    tables = parseODS("CARD_all.ods")
    translations = {
                    u'Карточка Cпец.раздела' : u'special',
                    u'Карточка БОЦП' : u'bocp',
                    u'Карточка ПАУД' : u'paud',
                    u'Карточка ПЦБИК' : u'pcbik',
                    u'Карточка ФДККП' : u'fdkkp',
                   }

    for table_name in tables.iterkeys():
        #table_name = u'bocp'
        filtered = filterBlank_rows(tables[table_name])
        rows = filtered # cropColumns(filtered, 2, 4)
        table_name = translations[table_name] or table_name
        filename = table_name + '.csv'
        codecs.open(filename, "w", "utf8").write(table2csv(rows))
        #fp = codecs.open(filename, "w", "utf8")
        #doc = xml.dom.minidom.Document()
        #doc.encoding = "UTF-8"
        #root = doc.createElement('DoDoc')
        #doc.appendChild(root)
        #root.appendChild(table2dom(rows, table_name))
        #fp.write(doc.toprettyxml())
        ##for cells in rows:
        ##    fp.write(u';'.join(cells) + u'\n')
        #fp.close()
