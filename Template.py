import xml.sax.handler
import xml.sax

import re

import xml.dom.minidom
from pprint import pprint


TAG_TABLE = 'table:table'
TAG_ROW = 'table:table-row'


def setAttributes(doc, node, attributes):
    if attributes:
        for k, v in attributes.items():
            attr = doc.createAttribute(k)
            node.setAttribute(k, v)


class Gen_XML(object):
    def __init__(self, params = None):
        self.params = params or {}
        self.doc = xml.dom.minidom.Document()
        self.doc.encoding = "UTF-8"
        self.node = None
        self.in_table = False
        self.table_handler = None

    def startElement(self, name, attrs):
        if name == TAG_TABLE:
            self.table_handler = Table_handler(self.params)
            self.in_table = True
        if self.in_table:
            self.table_handler.startElement(name, attrs)
            return
        if self.node:
            self.node = self.node.appendChild(self.doc.createElement(name))
        else:
            self.node = self.doc.createElement(name)
            self.doc.appendChild(self.node)
        setAttributes(self.doc, self.node, attrs)

    def endElement(self, name):
        if self.in_table:
            self.table_handler.endElement(name)
            if name == TAG_TABLE:
                self.in_table = False
                self.node.appendChild(self.table_handler.doc.firstChild)
            return
        self.node = self.node.parentNode

    def characters(self, content):
        if self.in_table:
            self.table_handler.characters(content)
            return
        text_node = self.doc.createTextNode(content)
        self.node.appendChild(text_node)

    def resultXML(self):
        r = Replacer(self.params)
        iterNode(self.doc, self.doc.firstChild, r)
        return r.doc.toxml()


class Template_handler(xml.sax.handler.ContentHandler):
    re_param = re.compile(ur'(?iu)\{([a-z0-9\._]+)\}')

    def __init__(self):
        self.in_body = False
        self.in_table = False
        self.params = {
            u'name' : u'World',
            u'table1' :
                (
                    {'id' : '1', 'name' : 'SIAM.00479', 'description' : 'Test1'},
                    {'id' : '2', 'name' : 'SIAM.00172', 'description' : 'Test2'}
                )
            }
        self.gen = Gen_XML(self.params)

    def startElement(self, name, attrs):
        if self.in_body:
            pass
        elif name == 'office:body':
            self.in_body = True
        self.gen.startElement(name, attrs)

    def endElement(self, name):
        if self.in_body:
            if name == 'office:body':
                self.in_body = False
        self.gen.endElement(name)

    def characters(self, content):
        self.gen.characters(content)

    def resultXML(self):
        return self.gen.resultXML()


class Template(object):
    def __init__(self, xml_content):
        self.xml_content = xml_content

    def render(self):
        h = Template_handler()
        xml.sax.parseString(self.xml_content, h)
        result = h.resultXML()
        return result


def iterNode(doc, node, callback):
    if node.nodeType == node.TEXT_NODE:
        callback.characters(node.wholeText)
    else:
        #print node.tagName
        callback.startElement(node.tagName, node.attributes)
        if node.hasChildNodes():
            for child in node.childNodes:
                iterNode(doc, child, callback)
        callback.endElement(node.tagName)


class Parameters_finder(object):
    re_param = re.compile(ur'(?iu)\{([a-z0-9\._]+)\}')

    def __init__(self, doc = None):
        self.parameters = set()

    def startElement(self, name, attrs):
        pass

    def endElement(self, name):
        pass

    def characters(self, content):
        params = self.re_param.findall(content)
        for p in params:
            self.parameters.add(p)


class Table_handler(object):
    def __init__(self, data = None):
        self.data = data or {}
        self.doc = xml.dom.minidom.Document()
        self.node = None
        self.table_node = None
        self.row_handler = None
        self.in_row = False

    def startElement(self, name, attrs):
        if name == TAG_ROW and self.table_node.isSameNode(self.node):
            self.row_handler = Row_handler(self.node)
            self.in_row = True
        if self.in_row:
            self.row_handler.startElement(name, attrs)
            return
        if name == TAG_TABLE:
            self.table_node = self.doc.createElement(name)
            self.node = self.table_node
            self.doc.appendChild(self.node)
        else:
            self.node = self.node.appendChild(self.doc.createElement(name))
        setAttributes(self.doc, self.node, attrs)

    def endElement(self, name):
        if self.in_row:
            self.row_handler.endElement(name)
            if name == TAG_ROW:
                self.renderRow()
                self.in_row = False
        else:
            self.node = self.node.parentNode

    def characters(self, content):
        if self.in_row:
            self.row_handler.characters(content)
        else:
            self.node.appendChild(self.doc.createTextNode(content))

    def renderRow(self):
        pf = Parameters_finder()
        iterNode(self.doc, self.row_handler.row_node, pf)
        tables_used = set()
        for param in pf.parameters:
            data = param.split('.')
            if len(data) == 2:
                tables_used.add(param.split('.')[0])
        if len(tables_used):
            for t in tables_used:
                row_dict = {}
                for lines in self.data[t]:
                    for k, v in lines.iteritems():
                        row_dict['%s.%s' % (t, k)] = v
                    self.row_handler.render(row_dict)
        else:
            self.row_handler.render({})


class Row_handler(object):
    def __init__(self, parent = None):
        self.doc = xml.dom.minidom.Document()
        self.parent = parent
        self.node = None
        self.row_node = None

    def startElement(self, name, attrs):
        if name == TAG_ROW:
            self.row_node = self.doc.createElement(name)
            self.node = self.row_node
            self.doc.appendChild(self.node)
        else:
            self.node = self.node.appendChild(self.doc.createElement(name))
        setAttributes(self.doc, self.node, attrs)

    def endElement(self, name):
        self.node = self.node.parentNode

    def characters(self, content):
        self.node.appendChild(self.doc.createTextNode(content))

    def render(self, params):
        r = Replacer(params)
        iterNode(self.doc, self.row_node, r)
        self.parent.appendChild(r.doc.firstChild)


class Replacer(object):
    re_param = re.compile(ur'(?iu)\{([a-z0-9\._]+)\}')

    def __init__(self, rdict):
        self.doc = xml.dom.minidom.Document()
        self.node = None
        self.rdict = rdict

    def startElement(self, name, attrs):
        if not self.node:
            self.node = self.doc.createElement(name)
            self.doc.appendChild(self.node)
        else:
            elem = self.doc.createElement(name)
            self.node = self.node.appendChild(elem)
        setAttributes(self.doc, self.node, attrs)

    def endElement(self, name):
        self.node = self.node.parentNode

    def replacement(self, matched):
        key = matched.group(1)
        if self.rdict.has_key(key):
            return unicode(self.rdict[key])
        else:
            return key

    def characters(self, content):
        rcontent = self.re_param.sub(self.replacement, content)
        self.node.appendChild(self.doc.createTextNode(rcontent))


def testTable():
    t = Table_handler()
    t.data = { 't' : ( {'c1' : '11', 'c2' : '12'}, {'c1' : '21', 'c2' : '22'} ) }
    t.startElement(TAG_TABLE, [])
    t.startElement(TAG_ROW, [])
    t.startElement('table:table-cell', [])
    t.characters('{t.c1}')
    t.endElement('table:table-cell')
    t.startElement('table:table-cell', [])
    t.characters('{t.c2}')
    t.endElement('table:table-cell')
    t.endElement(TAG_ROW)
    t.endElement(TAG_TABLE)
    print t.doc.toprettyxml()

def main():
    testTable()

if __name__ == '__main__':
    main()
