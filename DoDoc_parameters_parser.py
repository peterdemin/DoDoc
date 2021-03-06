#!usr/bin/python
# -*- coding: utf8 -*-
encoding='utf8'

import os
import xml.sax
from pprint import pprint

def parseParameters_XML(xml_content):
    """
    Function parsers xml_content to generate inner data structure for filling template.
    """
    p = Parser()
    xml.sax.parseString(xml_content, p)
    return expandImages_in_tables(p.tree)
    return p.tree

class Parser(xml.sax.handler.ContentHandler):
    """
    Input XML parser.
    Result is in self.tree dict.
    """
    tag_csv   = u'ROWS_FROM_CSV'
    tag_cdr   = u'ROWS_FROM_CDR'
    tag_row   = u'ROW'
    tag_image = u'IMAGE'

    def __init__(self):
        self.tree = {}
        self.cur_name = None
        self.table_names = []   # nested tables names
        self.tables = []        # nested tables
        self.cur_row = {}       # current row elements
        self.cur_table = []     # current rows list
        self.in_image = None
        self.cur_images = []
        self.image_pathes = set()
        self.content = u''
        self.odg2wmf = None
        self.level = 0

    def pushTable(self):
        if len(self.table_names):
            self.cur_table.append(self.cur_row)
            self.tables.append(self.cur_table)
            self.cur_table = []
            self.cur_row = {}

    def popTable(self):
        if len(self.tables):
            closed_table = self.cur_table
            self.cur_table = self.tables[-1]
            self.cur_row = self.cur_table[-1]
            self.cur_row[self.table_names[-1]] = closed_table
            self.tables.pop(-1)
            self.table_names.pop(-1)
            self.cur_table.pop(-1)
        else:
            self.tree[self.table_names[-1]] = self.cur_table
            self.table_names.pop(-1)
            self.cur_table = []
            self.cur_row = {}

    def startElement(self, name, attrs):
        self.level+= 1
        if name == self.tag_row:
            if self.cur_name:
                if len(self.table_names) == 0 or (self.cur_name != self.table_names[-1]):
                    self.pushTable()
                    self.table_names.append(self.cur_name)
                self.cur_row = {}
            else:
                raise ValueError(u'ERROR: "%s" tag name is reserved!' % (self.tag_row))
        elif name == self.tag_csv:
            if self.cur_name:
                if len(self.table_names) == 0 or (self.cur_name != self.table_names[-1]):
                    self.pushTable()
                    self.table_names.append(self.cur_name)
                self.__parseCSV(attrs)
            else:
                print u'ERROR: "%s" tag name is reserved!' % (self.tag_csv)
        elif name == self.tag_cdr:
            if self.cur_name:
                if len(self.table_names) == 0 or (self.cur_name != self.table_names[-1]):
                    self.pushTable()
                    self.table_names.append(self.cur_name)
                self.__parseCDR(attrs)
            else:
                print u'ERROR: "%s" tag name is reserved!' % (self.tag_csv)
        elif name == self.tag_image:
            if self.cur_name:
                self.in_image = self.cur_name
                if len(self.table_names):
                    self.cur_row[self.in_image] = []
                else:
                    self.tree[self.in_image] = []
            else:
                print u'ERROR: "%s" tag name is reserved!' % (self.tag_image)
        else:
            if len(self.table_names):
                if self.cur_row.has_key(name):
                    raise ValueError(u'Key "%s" allready exists in %s "%s"' % (name, self.tag_row, self.table_names[-1]))
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
            self.cur_table.append(self.cur_row)
            self.cur_name = self.table_names[-1]
        elif len(self.table_names) and (name == self.table_names[-1]):
            self.popTable()
        elif name == self.tag_csv:
            self.cur_name = self.table_names[-1]
        elif name == self.tag_cdr:
            self.cur_name = self.table_names[-1]
        elif name == self.tag_image:
            self.cur_images.extend(self.parseIMAGE())
        elif name == self.in_image:
            if len(self.table_names):
                self.cur_row[self.in_image].extend(self.cur_images)
            else:
                self.tree[self.in_image].extend(self.cur_images)
            self.in_image = None
            self.cur_images = []
        elif len(self.table_names):
            safe_update(self.cur_row, name, self.content)
        else:
            if self.cur_name == name:
                safe_update(self.tree, name, self.content)
            self.cur_name = None
        self.content = u''
        if self.level == 0:
            if self.odg2wmf:
                self.odg2wmf.disconnect()

    def characters(self, text):
        self.content+= text

    def parseIMAGE(self):
        path = self.content
        if os.path.exists(path):
            if os.path.splitext(path)[1].lower() == u'.odg':
                return self.__parseODG(path)
            elif os.path.splitext(path)[1].lower() in [u'.wmf', u'.gif', u'.png']:
                return self.__parseImage_ready(path)
            else:
                print (u'Error: Only .wmf, .gif, .png and .odg images are allowed: "%s"' % (path)).encode('cp866', 'replace')
        else:
            print (u'Error: No such image file: "%s"' % (path)).encode('cp866', 'replace')
        return []

    def __parseImage_ready(self, image_path):
        import shutil
        output_filename = u'/'.join([u'Pictures', os.path.basename(image_path)])
        if not os.path.exists('Pictures'):
            os.mkdir('Pictures')
        shutil.copy2(image_path, output_filename)
        return [output_filename]

    def __parseODG(self, odg_path):
        output_filename = u'/'.join([u'Pictures', os.path.splitext(os.path.basename(odg_path))[0] + '.wmf'])
        if not os.path.exists('Pictures'):
            os.mkdir('Pictures')
        if not self.odg2wmf:
            import odg2wmf
            self.odg2wmf = odg2wmf.Odg2wmf()
            self.odg2wmf.connect()
        wmfs = []
        if self.odg2wmf.open(odg_path):
            wmfs = self.odg2wmf.saveWMF(output_filename)
            self.odg2wmf.close()
        return wmfs

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
                    self.cur_table.append(self.cur_row)
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
                                    self.cur_table.append(self.cur_row)
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

def expandTable(table):
    id = 1
    sub_id = 1
    expanded = []
    for row in table:
        image_rows = 0
        row['ID'] = unicode(id)
        row['AMOUNT'] = unicode(len(table))
        for cell in row.itervalues():
            if is_image(cell):
                #print rk, 'in', k, len(rv)
                image_rows = max(len(cell), image_rows)
        if image_rows in (0, 1):
            # Do not inject sub ids single row
            #row['SUB_ID'] = unicode(1)
            #row['SUB_AMOUNT'] = unicode(1)
            expanded.append(row)
        else:
            for image_id in range(image_rows):
                cur_row = {}
                for rk, rv in row.iteritems():
                    if is_image(rv):
                        if len(rv) > image_id:
                            cur_row[rk] = [rv[image_id]]
                        else:
                            cur_row[rk] = []
                    elif is_table(rv):
                        cur_row[rk] = expandTable(rv)
                    else:
                        cur_row[rk] = rv
                cur_row['SUB_ID'] = unicode(sub_id)
                cur_row['SUB_AMOUNT'] = unicode(image_rows)
                expanded.append(cur_row)
                sub_id+= 1
        id += 1
        sub_id = 1
    return expanded

def expandImages_in_tables(params):
    result = {}
    for k, v in params.iteritems():
        if is_table(v):
            result[k] = expandTable(v)
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
    <authors>
        <ROW>
            <a>1</a>
        </ROW>
        <ROW>
            <a>2</a>
            <arguments>
                <ROW>
                    <b>4</b>
                </ROW>
                <ROW>
                    <b>5</b>
                </ROW>
                <ROW>
                    <b>6</b>
                </ROW>
            </arguments>
        </ROW>
        <ROW>
            <a>3</a>
            <flow_chart type='image'>
                <IMAGE>1.png</IMAGE>
                <IMAGE>1.png</IMAGE>
            </flow_chart>
        </ROW>
        <ROWS_FROM_CSV filename="example.csv"/>
    </authors>
    <test>TEST</test>
</DoDoc>'''

    pprint(parseParameters_XML(xml_content))

if __name__ == '__main__':
    main()
