#!usr/bin/python
# -*- coding: utf8 -*-
encoding='utf8'

import os
import xml.sax
from pprint import pprint

class Parser(xml.sax.handler.ContentHandler):
    tag_row = 'ROW'
    tag_image = 'IMAGE'

    def __init__(self):
        self.tree = {}
        self.cur_name = None
        self.in_row = None
        self.cur_row = None
        self.in_image = None
        self.cur_images = []
        self.image_pathes = set()
        self.content = ''

    def startElement(self, name, attrs):
        if name == self.tag_row:
            if self.in_row:
                print 'ERROR: Nested %ss are not allowed!' % (self.tag_row)
                return
            else:
                if self.cur_name:
                    self.in_row = self.cur_name
                    self.cur_row = {}
                    if not self.tree.has_key(self.in_row):
                        self.tree[self.in_row] = []
                else:
                    print 'ERROR: "%s" tag name is reserved!' % (self.tag_row)
        elif name == 'IMAGE':
            if self.cur_name:
                self.in_image = self.cur_name
                if self.in_row:
                    self.cur_row[self.in_image] = []
                else:
                    self.tree[self.in_image] = []
            else:
                print 'ERROR: "IMAGE" tag name is reserved!'
        else:
            self.cur_name = name
        self.content = u''

    def endElement(self, name):
        def safe_update(d, elem, content):
            old_content = d.get(elem) or ''
            if type(old_content) == unicode:
                d[elem] = old_content + content
        if name == self.tag_row:
            self.tree[self.in_row].append(self.cur_row)
            self.cur_name = self.in_row
            self.in_row = None
        elif name == 'IMAGE':
            self.cur_images.extend(self.__parseIMAGE())
            #print self.cur_images
        elif name == self.in_image:
            if self.in_row:
                self.cur_row[self.in_image].extend(self.cur_images)
            else:
                self.tree[self.in_image].extend(self.cur_images)
            self.in_image = None
            self.cur_images = []
        elif name == self.in_row:
            assert(self.in_row == None)
            self.cur_name = None
        elif self.in_row:
            self.cur_row[self.cur_name] = self.content
        else:
            if self.cur_name == name:
                safe_update(self.tree, self.cur_name, self.content)
            else:
                #print '!=', self.cur_name, name
                pass
            self.cur_name = None
        self.content = u''

    def characters(self, text):
        self.content+= text

    def __parseIMAGE(self):
        path = self.content.decode('utf8')
        if os.path.exists(path):
            if os.path.splitext(path)[1].lower() == '.odg':
                return self.__parseODG(path)
            elif os.path.splitext(path)[1].lower() == '.png':
                return self.__parsePNG(path)
            else:
                print (u'Error: Only .png and .odg images are allowed: "%s"' % (path)).encode('cp866', 'replace')
        else:
            print (u'Error: No such image file: "%s"' % (path)).encode('cp866', 'replace')
        return []

    def __parsePNG(self, png_path):
        import shutil
        output_filename = u'/'.join([u'Pictures', os.path.basename(png_path)])
        if not os.path.exists('Pictures'):
            os.mkdir('Pictures')
        shutil.copy2(png_path, output_filename)
        return [output_filename]

    def __parseODG(self, odg_path):
        pngs = []
        output_filename = u'/'.join([u'Pictures', os.path.splitext(os.path.basename(odg_path))[0] + '.png'])
        if not os.path.exists('Pictures'):
            os.mkdir('Pictures')
        import odg2png
        pngs = odg2png.odg2png(odg_path, output_filename)
        return pngs

def parseParameters_XML(xml_content):
    p = Parser()
    xml.sax.parseString(xml_content, p)
    return expandImages_in_tables(p.tree)

def testImage_in_table():
    params = { u'table' : [ { u'fc1' : [u'1.png', u'2.png'],            u'fc2' : [u'3.png', u'4.png', u'5.png'] },
                            { u'fc1' : [u'6.png', u'7.png', u'8.png'],  u'fc2' : [u'9.png'] },
                            { u'a' : u'aa', u'b' : u'bb' },
                          ],
             }
    pprint(expandImages_in_tables(params))

def is_table(value):
    if type(value) == list:
        if len(value):
            if type(value[0]) == dict:
                return True
    return False

def is_image(value):
    if type(value) == list:
        if len(value):
            if type(value[0]) == unicode:
                return True
            else:
                return False
        else:
            return True
    else:
        return False
    return False

def expandImages_in_tables(params):
    result = {}
    for k, v in params.iteritems():
        if is_table(v):
            id = 1
            sub_id = 1
            result[k] = []
            for row in v:
                image_rows = 0
                row['ID'] = unicode(id)
                row['AMOUNT'] = unicode(len(v))
                for rk, rv in row.iteritems():
                    if is_image(rv):
                        #print rk, 'in', k, len(rv)
                        image_rows = max(len(rv), image_rows)
                if image_rows in (0, 1):
                    #row['SUB_ID'] = unicode(1)
                    #row['SUB_AMOUNT'] = unicode(1)
                    result[k].append(row)
                else:
                    for image_id in range(image_rows):
                        cur_row = {}
                        for rk, rv in row.iteritems():
                            if is_image(rv):
                                if len(rv) > image_id:
                                    cur_row[rk] = [rv[image_id]]
                                else:
                                    cur_row[rk] = []
                            else:
                                cur_row[rk] = rv
                        cur_row['SUB_ID'] = unicode(sub_id)
                        cur_row['SUB_AMOUNT'] = unicode(image_rows)
                        result[k].append(cur_row)
                        sub_id+= 1
                id += 1
                sub_id = 1
        else:
            result[k] = v
    return result

def main():
    #return testImage_in_table()
    xml_content = '''
<DoDoc>
    <approver>А.С. Сыров</approver>
    <siam_id>СИЯМ.00496-01 96 01</siam_id>
    <authors type="table">
        <ROW>
            <position>Инженер</position>
            <name>Demin
            Peter
            Evgenievich</name>
        </ROW>
        <ROW>
            <position>2</position>
            <name>Item2</name>
            <flow_chart type='image'>
                <IMAGE>1.png</IMAGE>
                <IMAGE>1.png</IMAGE>
            </flow_chart>
        </ROW>
    </authors>
    <flow_chart type='image'>
        <IMAGE>1.png</IMAGE>
        <IMAGE>2.png</IMAGE>
    </flow_chart>
</DoDoc>'''
    pprint(parseParameters_XML(xml_content))

if __name__ == '__main__':
    main()
