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
    temp_dir = basefilename(result_path)
    extractAll(template_path, temp_dir)

    styles_xml_path = os.path.join(temp_dir, 'styles.xml')
    styles_xml = open(styles_xml_path, 'r').read()
    t = Template(styles_xml, template_parameters)
    rendered_styles_xml = t.render()
    codecs.open(styles_xml_path, 'w', 'utf-8').write(rendered_styles_xml)

    content_xml_path = os.path.join(temp_dir, 'content.xml')
    content_xml = open(content_xml_path, 'r').read()
    t = Template(content_xml, template_parameters)
    rendered_content_xml = t.render()
    codecs.open(content_xml_path, 'w', 'utf-8').write(rendered_content_xml)

    png_replacements = t.imageUrls()
    for key in png_replacements.iterkeys():
        value = png_replacements[key]
        for flow_chart_path in value:
            dest_path = os.path.join(temp_dir, flow_chart_path)
            shutil.copy2(flow_chart_path, dest_path)
    shutil.rmtree('Pictures')
    replaceManifest(temp_dir, png_replacements)
    cleanPictures(temp_dir, png_replacements.keys())

    packAll(temp_dir, result_path)
    shutil.rmtree(temp_dir)

def replaceManifest(dest_dir, png_replacements):
    import re
    re_png = re.compile(ur'(?imu) <manifest:file\-entry manifest:media\-type="image\/png" manifest:full\-path="(Pictures\/[a-f0-9]+.png)"\/>')
    png_pattern = ' <manifest:file-entry manifest:media-type="image/png" manifest:full-path="%s"/>'

    manifest_path = os.path.join(dest_dir, 'META-INF', 'manifest.xml')
    manifest_lines = open(manifest_path, 'rb').readlines()
    result = []

    for line in [a.rstrip() for a in manifest_lines]:
        m = re_png.match(line)
        if m:
            source_png = m.group(1)
            if png_replacements.has_key(source_png):
                #print '-', source_png
                for dest_png in png_replacements[source_png]:
                    result.append(png_pattern % (dest_png))
                    #print '+', dest_png
            else:
                result.append(line)
        else:
            result.append(line)

    open(manifest_path, 'wb').write('\n'.join(result))

def cleanPictures(odt_path, to_delete):
    pic_path = os.path.join(odt_path, 'Pictures')
    existing_pics = os.listdir(pic_path)
    for pic in existing_pics:
        pic_path = '/'.join(['Pictures', pic])
        if pic_path in to_delete:
            #print '-', pic_path
            os.unlink(os.path.join(odt_path, pic_path))
        else:
            #print '~', pic_path
            pass

def main():
    if len(sys.argv) == 3:
        template_path = sys.argv[1]
        params_path = sys.argv[2]
    else:
        template_path = 'templates/TT.odt'
        params_path = 'stumuz_TT.xml'

    template_params = parseParameters_XML(codecs.open(params_path, 'r', 'utf8').read())
    #pprint(template_params)

    result_path = u'%s_%s.odt' % (basefilename(template_path), basefilename(params_path))
    renderTemplate(template_path, template_params, result_path)

if __name__ == '__main__':
    main()
