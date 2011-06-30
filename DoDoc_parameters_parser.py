#!usr/bin/python
# -*- coding: utf8 -*-
encoding='utf8'

import xml.sax
from pprint import pprint

class Parser(xml.sax.handler.ContentHandler):
    def __init__(self):
        self.parameters = {}
        self.cur_param = None
        self.cur_image = None
        self.cur_table = None
        self.level = 0

    def startElement(self, name, attrs):
        if self.level > 0:
            if self.cur_table:
                if name == u'row':
                    self.parameters[self.cur_table].append({})
                else:
                    self.cur_param = name
            elif self.cur_image:
                if name == u'image':
                    self.cur_param = name
            else:
                if attrs.has_key('type'):
                    if attrs['type'] == u'image':
                        self.cur_image = name
                        self.parameters[self.cur_image] = []
                    elif attrs['type'] == u'table':
                        self.cur_table = name
                        self.parameters[self.cur_table] = []
                    elif attrs['type'] == u'var':
                        self.cur_param = name
                    else:
                        print 'Unexpected type attribute value: "%s"' % (attrs['type'])
                else:
                    self.cur_param = name
        self.level+= 1

    def endElement(self, name):
        if self.cur_param:
            self.cur_param = None
        elif self.cur_table:
            if self.cur_table == name:
                self.cur_table = None
        elif self.cur_image:
            if self.cur_image == name:
                self.cur_image = None
        self.level-= 1

    def characters(self, content):
        if self.cur_table:
            if self.cur_param:
                self.parameters[self.cur_table][-1][self.cur_param] = content
        elif self.cur_image:
            if self.cur_param:
                self.parameters[self.cur_image].append(content)
        elif self.cur_param:
            self.parameters[self.cur_param] = content

def parseParams_XML(xml_content):
    p = Parser()
    xml.sax.parseString(xml_content, p)
    return p.parameters

def main():
    xml_content = u'''<DoDoc>
    <approver>А.С. Сыров</approver>
    <siam_id>00496-01 96 01</siam_id>
    <params type="table">
        <row>
            <id>1</id>
            <name>Item1</name>
        </row>
        <row>
            <id>2</id>
            <name>Item2</name>
        </row>
    </params>
    <flow_chart type='image'>
        <image>svbsa101k2_1.png</image>
        <image>svbsa101k2_2.png</image>
        <image>svbsa101k2_3.png</image>
    </flow_chart>
</DoDoc>'''
    pprint(parseParams_XML(xml_content))

if __name__ == '__main__':
    main()
