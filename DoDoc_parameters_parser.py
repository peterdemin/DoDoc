#!usr/bin/python
# -*- coding: utf8 -*-
encoding='utf8'

import os
import xml.sax
from pprint import pprint

class Parser(xml.sax.handler.ContentHandler):
    def __init__(self):
        self.parameters = {}
        self.cur_param = None
        self.cur_image = None
        self.cur_table = None
        self.image_pathes = set()
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
                        print 'ATTENTION: Unexpected type attribute value: "%s"' % (attrs['type'])
                else:
                    self.cur_param = name
        self.level+= 1

    def endElement(self, name):
        if self.cur_table:
            if self.cur_table == name:
                self.cur_table = None
            elif self.cur_param:
                if not self.parameters[self.cur_table][-1].has_key(self.cur_param):
                    self.parameters[self.cur_table][-1][self.cur_param] = u''
                self.cur_param = None
        if self.cur_image:
            if self.cur_image == name:
                self.cur_image = None
        if self.cur_param:
            if not self.parameters.has_key(self.cur_param):
                self.parameters[self.cur_param] = u''
            self.cur_param = None
        self.level-= 1

    def characters(self, content):
        def safe_update(d, elem, content):
            d[elem] = (d.get(elem) or u'') + content
        if self.cur_table:
            if self.cur_param:
                if len(content.strip()) > 0:
                    safe_update(self.parameters[self.cur_table][-1], self.cur_param, content)
        elif self.cur_image:
            if self.cur_param:
                if os.path.exists(content):
                    if os.path.splitext(content)[1].lower() == u'.odg':
                        self.parseODG(content)
                    elif os.path.splitext(content)[1].lower() == u'.png':
                        self.parsePNG(content)
                    else:
                        print (u'Error: Only .png and .odg images are allowed: "%s"' % (content)).encode('cp866', 'replace')
                else:
                    print (u'Error: No such image file: "%s"' % (content)).encode('cp866', 'replace')
        elif self.cur_param:
            if len(content.strip()) > 0:
                safe_update(self.parameters, self.cur_param, content)

    def parsePNG(self, png_path):
        import shutil
        output_filename = '/'.join(['Pictures', os.path.basename(png_path)])
        if not os.path.exists('Pictures'):
            os.mkdir('Pictures')
        shutil.copy2(png_path, output_filename)
        self.parameters[self.cur_image].append(output_filename)

    def parseODG(self, odg_path):
        pngs = []
        output_filename = '/'.join(['Pictures', os.path.splitext(os.path.basename(odg_path))[0] + u'.png'])
        if not os.path.exists('Pictures'):
            os.mkdir('Pictures')
        for try_two_times in (1, 2):
            try:
                import odg2png
                pngs = odg2png.odg2png(odg_path, output_filename)
            except Exception, e:
                if e.typeName == 'com.sun.star.connection.NoConnectException':
                    import time
                    os.system("start start_oo_server.bat")
                    time.sleep(5.0)
                    continue
                else:
                    raise
            break  # success occured
        if pngs:
            self.parameters[self.cur_image].extend(pngs)

def parseParameters_XML(xml_content):
    p = Parser()
    xml.sax.parseString(xml_content, p)
    return p.parameters

def main():
    xml_content = u'''<DoDoc>
    <approver>А.С. Сыров</approver>
    <siam_id>СИЯМ.00496-01 96 01</siam_id>
    <authors type="table">
        <row>
            <position>Инженер</position>
            <name>Demin
            Peter
            Evgenievich</name>
        </row>
        <row>
            <position>2</position>
            <name>Item2</name>
        </row>
    </authors>
    <flow_chart type='image'>
        <image>100000000000031A00000463D338E056.png</image>
    </flow_chart>
</DoDoc>'''
    pprint(parseParameters_XML(xml_content))

if __name__ == '__main__':
    main()
