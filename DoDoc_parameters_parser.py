#!usr/bin/python
# -*- coding: utf8 -*-
encoding='utf8'

import os
import xml.sax
from pprint import pprint

class Parser(xml.sax.handler.ContentHandler):
    tag_csv   = u'ROW_FROM_CSV'
    tag_cdr   = u'ROW_FROM_CDR'
    tag_row   = u'ROW'
    tag_image = u'IMAGE'

    def __init__(self):
        self.tree = {}
        self.cur_name = None
        self.table_names = []   # nested tables names
        self.tables = []        # nested tables
        self.cur_row = {}       # current row elements
        self.in_image = None
        self.cur_images = []
        self.image_pathes = set()
        self.content = u''
        self.odg2png = None
        self.level = 0

    def startElement(self, name, attrs):
        self.level+= 1
        if name == self.tag_row:
            if self.cur_name:
                self.in_row.append(self.cur_name)
                self.cur_row.append({})
            #    if not self.tree.has_key(self.in_row):
            #        self.tree[self.in_row] = []
            else:
                raise ValueError(u'ERROR: "%s" tag name is reserved!' % (self.tag_row))
        elif name == self.tag_csv:
            if self.in_row:
                print u'ERROR: Nested %ss are not allowed!' % (self.tag_row)
                return
            if self.cur_name:
                self.in_row = self.cur_name
                self.cur_row = {}
                if not self.tree.has_key(self.in_row):
                    self.tree[self.in_row] = []
                self.__parseCSV(attrs)
            else:
                print u'ERROR: "%s" tag name is reserved!' % (self.tag_csv)
        elif name == self.tag_cdr:
            if self.in_row:
                print u'ERROR: Nested %ss are not allowed!' % (self.tag_row)
                return
            if self.cur_name:
                self.in_row = self.cur_name
                self.cur_row = {}
                if not self.tree.has_key(self.in_row):
                    self.tree[self.in_row] = []
                self.__parseCDR(attrs)
            else:
                print u'ERROR: "%s" tag name is reserved!' % (self.tag_cdr)
        elif name == self.tag_image:
            if self.cur_name:
                self.in_image = self.cur_name
                if self.in_row:
                    self.cur_row[self.in_image] = []
                else:
                    self.tree[self.in_image] = []
            else:
                print u'ERROR: "%s" tag name is reserved!' % (self.tag_image)
        else:
            if len(self.in_row):
                if self.cur_row[-1].has_key(name):
                    raise ValueError(u'Key "%s" allready exists in %s "%s"' % (name, self.tag_row, self.in_row))
            elif self.tree.has_key(name):
                raise ValueError(u'Key "%s" allready exists' % (name))
            self.cur_name = name
        self.content = u''

    def endElement(self, name):
        self.level-= 1
        def safe_update(d, elem, content):
            assert(type(content) == unicode)
            old_content = d.get(elem) or u''
            if type(old_content) == unicode:
                d[elem] = old_content + content
        if name == self.tag_row:
            if len(self.in_row) > 1:
                self.in_row[-1].append(self.cur_row[-1])
            else:
                self.tree[self.in_row[0]].append(self.cur_row[0])
                self.cur_name = self.in_row
                self.in_row = None
        elif name == self.tag_csv:
            self.cur_name = self.in_row
            self.in_row = None
        elif name == self.tag_cdr:
            self.cur_name = self.in_row
            self.in_row = None
        elif name == self.tag_image:
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
            safe_update(self.cur_row[-1], self.cur_name, self.content)
        else:
            if self.cur_name == name:
                safe_update(self.tree, self.cur_name, self.content)
            else:
                #print '!=', self.cur_name, name
                pass
            self.cur_name = None
        self.content = u''
        if self.level == 0:
            if self.odg2png:
                self.odg2png.disconnect()

    def characters(self, text):
        self.content+= text

    def __parseIMAGE(self):
        path = self.content
        if os.path.exists(path):
            if os.path.splitext(path)[1].lower() == u'.odg':
                return self.__parseODG(path)
            elif os.path.splitext(path)[1].lower() == u'.png':
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
        if not self.odg2png:
            import odg2png
            self.odg2png = odg2png.Odg2png()
            self.odg2png.connect()
        if self.odg2png.open(odg_path):
            pngs = self.odg2png.savePNG(output_filename)
            self.odg2png.close()
        return pngs

    def __parseCSV(self, attrs):
        if attrs.has_key(u'filename'):
            if os.path.exists(attrs[u'filename']):
                if attrs.has_key(u'divider'):
                    column_divider = attrs[u'divider']
                else:
                    column_divider = u';'
                rows = readFile(attrs[u'filename']).splitlines()
                for row in rows:
                    columns = row.split(column_divider)
                    self.cur_row = dict([(unicode(i+1), c) for i, c in enumerate(columns)])
                    self.tree[self.in_row].append(self.cur_row)
            else:
                print (u'Error: No such table file: "%s"' % (attrs[u'filename'])).encode('cp866', 'replace')
        else:
            print (u'Error in "%s": No table filename specified' % (self.tag_csv)).encode('cp866', 'replace')

    def __parseCDR(self, attrs):
        import re
        re_row_divider = re.compile(ur'[\+\-]{20,}')
        divider = u'¦'
        if attrs.has_key(u'filename'):
            if os.path.exists(attrs[u'filename']):
                first_row = True
                rows = [a.strip() for a in readFile(attrs[u'filename']).splitlines()]
                self.cur_row = {}
                for row in rows:
                    if row.startswith(divider):
                        columns = row.split(divider)
                        if len(columns) == 3 and re_row_divider.match(columns[1]):
                            if len(self.cur_row.keys()):
                                if first_row:
                                    first_row = False
                                else:
                                    self.tree[self.in_row].append(self.cur_row)
                            self.cur_row = {}
                        elif len(columns) >= 3:
                            for i, col in enumerate(columns[1:-1]):
                                id = unicode(i+1)
                                self.cur_row[id] = (self.cur_row.get(id) or u'') + u' ' + col.strip()
                    else:
                        first_row = True
            else:
                print (u'Error: No such table file: "%s"' % (attrs[u'filename'])).encode('cp866', 'replace')
        else:
            print (u'Error in "%s": No table filename specified' % (self.tag_csv)).encode('cp866', 'replace')

def readFile(filename, forced_encoding = None):
    import codecs
    charmaps = ['cp1251', 'cp866', 'utf8']
    if forced_encoding:
        charmaps = [forced_encoding] + charmaps
        forced_encoding = None
    for cmap in charmaps:
        try:
            content = codecs.open(filename, 'r', cmap).read()
        except UnicodeDecodeError:
            continue
        except TypeError, e:
            print u'readFile() TypeError:'
            print u'Filename: "%s"' % (filename)
            print u'Charmap:  "%s"' % (cmap)
            raise e
        else:
            return content
    raise UnicodeDecodeError

def parseParameters_XML(xml_content):
    p = Parser()
    xml.sax.parseString(xml_content, p)
    return expandImages_in_tables(p.tree)

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

def testImage_in_table():
    params = { u'table' : [ { u'fc1' : [u'1.png', u'2.png'],            u'fc2' : [u'3.png', u'4.png', u'5.png'] },
                            { u'fc1' : [u'6.png', u'7.png', u'8.png'],  u'fc2' : [u'9.png'] },
                            { u'a' : u'aa', u'b' : u'bb' },
                          ],
             }
    pprint(expandImages_in_tables(params))

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
            <arguments type="table">
                <ROW>
                    <name>a</name>
                    <value>1</value>
                </ROW>
                <ROW>
                    <name>b</name>
                    <value>2</value>
                </ROW>
            </arguments>
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
    <csv>
        <ROW_FROM_CSV filename="example.csv"/>
    </csv>
    <flow_chart type='image'>
        <IMAGE>1.png</IMAGE>
        <IMAGE>2.png</IMAGE>
    </flow_chart>
</DoDoc>'''
    pprint(parseParameters_XML(xml_content))

if __name__ == '__main__':
    main()
