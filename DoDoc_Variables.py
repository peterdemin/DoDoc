#!usr/bin/python
# -*- coding: utf8 -*-
encoding='utf8'

import os
import sys
import codecs
import shutil
from pprint import pprint

import xml.sax.handler
import xml.sax

from OpenOffice_document import extractAll
from OpenOffice_document import packAll

from Template import Template

from DoDoc_parameters_parser import parseParameters_XML

def basefilename(path):
    return os.path.splitext(os.path.basename(path))[0]

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

def main():
    if len(sys.argv) == 3:
        template_path = sys.argv[1]
        params_path = sys.argv[2]
    else:
        template_path = 'templates/Variables.odt'
        params_path = 'variables.xml'

    template_params = parseParameters_XML(codecs.open(params_path, 'r', 'utf8').read())
    #pprint(template_params)

    result_path = u'%s_%s.odt' % (basefilename(template_path), basefilename(params_path))
    renderTemplate(template_path, template_params, result_path)

if __name__ == '__main__':
    main()
