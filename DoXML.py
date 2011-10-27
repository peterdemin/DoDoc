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
        self.last = self.root
        self.last_table = None

    def text(self, name, content, node = None):
        node_ = node or self.last or self.root
        if type(content) != unicode:
            content = unicode(content)
        if len(content):
            node_.appendChild(self.doc.createElement(name)).appendChild(self.doc.createTextNode(content))
        else:
            node_.appendChild(self.doc.createElement(name))

    def table(self, name, node = None):
        node_ = node or self.last or self.root
        self.last_table = node_.appendChild(self.doc.createElement(name))
        return self.last_table

    def row(self, node = None):
        node_ = node or self.last_table
        self.last = node_.appendChild(self.doc.createElement('ROW'))
        return self.last

    def image(self, name, image_path, node = None):
        node_ = node or self.last or self.root
        if type(image_path) != unicode:
            image_path = unicode(image_path)
        node_.appendChild(self.doc.createElement(name)).appendChild(self.doc.createElement(u'IMAGE')).appendChild(self.doc.createTextNode(image_path))

    def textRoot(self, name, content):
        self.text(name, content, self.root)

    def tableRoot(self, name):
        return self.table(name, self.root)

    def imageRoot(self, name, image_path):
        self.image(self.root, name, image_path)

    def save(self, filename):
        import codecs
        codecs.open(filename, 'w', 'utf-8').write(self.doc.toprettyxml())

def main():
    doc = DoXML()
    funcs = doc.table(u'doc')
    row = doc.row()
    doc.text('section', u'Алгебраические операции')
    doc.text('short', u'Умножение')
    doc.text('prototype', u'mult(a, b, c)')
    doc.table('args')
    doc.row()
    doc.text('name', u'a')
    doc.text('meaning', u'множитель')
    doc.row()
    doc.text('name', u'b')
    doc.text('meaning', u'множитель')
    doc.row()
    doc.text('name', u'c')
    doc.text('meaning', u'произведение')
    doc.text('comment', u'', row)
    doc.save('test.xml')
    return

if __name__ == '__main__':
    main()
