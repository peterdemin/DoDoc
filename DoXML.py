#!usr/bin/python
# -*- coding: utf8 -*-
encoding='utf8'
'''утф'''

import xml.dom.minidom

class DoXML(object):
    def __init__(self):
        self.doc = xml.dom.minidom.Document()
        self.doc.encoding = "UTF-8"
        self.root = self.doc.createElement(u'DoDoc')
        self.doc.appendChild(self.root)

    def text(self, node, name, content):
        if type(content) != unicode:
            content = unicode(content)
        if len(content):
            node.appendChild(self.doc.createElement(name)).appendChild(self.doc.createTextNode(content))
        else:
            node.appendChild(self.doc.createElement(name))

    def table(self, node, name):
        return node.appendChild(self.doc.createElement(name))

    def row(self, node):
        return node.appendChild(self.doc.createElement('ROW'))

    def image(self, node, name, image_path):
        if type(image_path) != unicode:
            image_path = unicode(image_path)
        node.appendChild(self.doc.createElement(name)).appendChild(self.doc.createElement(u'IMAGE')).appendChild(self.doc.createTextNode(image_path))

    def text_root(self, name, content):
        text(self.root, name, content)

    def table_root(self, name):
        return table(self.root, name)

    def image_root(self, name, image_path):
        image(self.root, name, image_path)

    def save(self, filename):
        import codecs
        codecs.open(filename, 'w', 'utf-8').write(self.doc.toprettyxml())

def main():
    doc = DoXML()
    funcs = doc.table_root(u'doc')
    row = doc.row(funcs)
    doc.text(row, 'section', u'Алгебраические операции')
    doc.text(row, 'short', u'Умножение')
    doc.text(row, 'prototype', u'mult(a, b, c)')
    args = doc.table(row, 'args')
    arg_row = doc.row(args)
    doc.text(arg_row, 'name', u'a')
    doc.text(arg_row, 'meaning', u'множитель')
    arg_row = doc.row(args)
    doc.text(arg_row, 'name', u'b')
    doc.text(arg_row, 'meaning', u'множитель')
    arg_row = doc.row(args)
    doc.text(arg_row, 'name', u'c')
    doc.text(arg_row, 'meaning', u'произведение')
    doc.text(row, 'comment', u'')
    doc.save('test.xml')
    return

if __name__ == '__main__':
    main()
