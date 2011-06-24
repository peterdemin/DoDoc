#!usr/bin/python
# -*- coding: utf8 -*-
encoding='utf8'
'''утф-8'''

import os
import re
import sys
import codecs
import shutil
from pprint import pprint

import xml.sax.handler
import xml.sax

from OpenOffice_document import extractAll
from OpenOffice_document import packAll

from Template import Template

from DoDoc import convertODT
from DoDraw import convertODG

TAG_PARAM = 'param'
TAG_USED_PM = 'usedPm'

from ftplib import FTP

class ARM_archive(object):
    #re_siam_dir = re.compile(ur'(?iu)Инв\. \_ [0-9]+ СИЯМ\.([0-9]{5}\-[0-9]{2} [0-9]{2} [0-9]{2})')
    re_siam_dir = re.compile(ur'(?iu)Инв\. \_ [0-9]+ СИЯМ\.(.+)')
    #re_siam_dir = re.compile(ur'(?iu)Инв\.(.+)')
    re_siam_TT_dir = re.compile(ur'(?iu)Инв\. \_ [0-9]+ ?СИЯМ\.([0-9]{5}\-[0-9]{2} 96 [0-9]{2})')

    def __init__(self):
        self.ftp = FTP()
        self.ftp.connect('172.2.0.200')
        self.ftp.login('petrovab', 'dfxG3')

    def listdir(self, path):
        if type(path) == unicode:
            path = path.encode('cp1251')
        result = []
        len_path = len(path)
        for item in self.ftp.nlst(path):
            yield item[len_path+1:].decode('cp1251')
            #result.append(item.decode('cp1251'))
        #return result

    def listSIAMs(self):
        for item in self.listdir(u'СИЯМ'):
            m = self.re_siam_dir.match(item)
            if m:
                yield(m.group(1))

    def listTTs(self):
        for item in self.listdir(u'СИЯМ'):
            m = self.re_siam_TT_dir.match(item)
            if m:
                yield(m.group(1))

class Parameters_parser(xml.sax.handler.ContentHandler):
    def __init__(self):
        self.parameters = []
        self.cur_param = None
        self.cur_key = None
        self.level = 0

    def startElement(self, name, attrs):
        if name == TAG_PARAM:
            self.cur_param = {}
        else:
            self.cur_key = None
            if not name == TAG_USED_PM:
                if self.level == 2:
                    if (self.cur_param != None):
                        self.cur_key = name
                        self.cur_param[self.cur_key] = ''
        self.level+= 1

    def endElement(self, name):
        if name == TAG_PARAM:
            if self.cur_param != None:
                self.parameters.append(self.cur_param)
                self.cur_param = None
        self.cur_key = None
        self.level-= 1

    def characters(self, content):
        if self.level == 3:
            self.cur_param[self.cur_key] = content # .strip()

def parseParameters(xml_file_path):
    xml_text = open(xml_file_path, 'rb').read()
    pp = Parameters_parser()
    xml.sax.parseString(xml_text, pp)
    return pp.parameters

def renderTemplate(template_path, template_parameters, result_path):
    template_basename = basefilename(template_path)
    extractAll(template_path, template_basename)

    content_xml_path = os.path.join(template_basename, 'content.xml')
    content_xml = open(content_xml_path, 'r').read()
    t = Template(content_xml, template_parameters)
    rendered_content_xml = t.render()
    codecs.open(content_xml_path, 'w', 'utf-8').write(rendered_content_xml)

    packAll(template_basename, result_path)
    shutil.rmtree(template_basename)

def basefilename(path):
    return os.path.splitext(os.path.basename(path))[0]

def main():
    if len(sys.argv) == 2:
        template_path = sys.argv[1]
        params_path = sys.argv[2]
    else:
        template_path = 'templates/Notification.odt'
        params_path = 'stumuz_notification.xml'

    arm = ARM_archive()
    for item in sorted(arm.listTTs()):
        print item

    #template_params = parseParameters(params_path)

    result_path = u'%s_%s.odt' % (basefilename(template_path), basefilename(params_path))
    #renderTemplate(template_path, template_params, result_path)

if __name__ == '__main__':
    main()
