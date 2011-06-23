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

def basefilename(path):
    return os.path.splitext(os.path.basename(path))[0]

def parseParameters(xml_file_path):
    xml_text = open(xml_file_path, 'rb').read()
    pp = Parameters_parser()
    xml.sax.parseString(xml_text, pp)
    return pp.parameters

def renderTemplate(template_path, flow_charts, template_parameters, result_path):
    template_basename = basefilename(template_path)
    extractAll(template_path, template_basename)

    content_xml_path = os.path.join(template_basename, 'content.xml')
    content_xml = open(content_xml_path, 'r').read()
    t = Template(content_xml, template_parameters)
    rendered_content_xml = t.render()
    codecs.open(content_xml_path, 'w', 'utf-8').write(rendered_content_xml)

    for flow_chart_path in flow_charts:
        dest_path = os.path.join(template_basename, 'Pictures', flow_chart_path)
        shutil.copy2(flow_chart_path, dest_path)
    replaceManifest(template_basename, flow_charts)
    cleanPictures(template_basename, t.imageUrls())

    packAll(template_basename, result_path)
    shutil.rmtree(template_basename)

def replaceManifest(dest_dir, png_list):
    manifest_path = os.path.join(dest_dir, 'META-INF', 'manifest.xml')
    manifest_text = open(manifest_path, 'rb').read()

    re_png = re.compile(ur'(?imu) <manifest:file\-entry manifest:media\-type="image\/png" manifest:full\-path="(Pictures\/[a-f0-9]+.png)"\/>')

    png_pattern = ' <manifest:file-entry manifest:media-type="image/png" manifest:full-path="%s"/>'
    png_lines = '\n'.join([png_pattern % png for png in png_list])

    replaced, repls_amount = re_png.subn(png_lines, manifest_text, 1)
    open(manifest_path, 'wb').write(replaced)

def cleanPictures(odt_path, used):
    pic_path = os.path.join(odt_path, 'Pictures')
    existing_pics = os.listdir(pic_path)
    for pic in existing_pics:
        pic_path = u'/'.join(['Pictures', pic])
        if not pic_path in used:
            print '-', pic_path
            os.unlink(os.path.join(odt_path, pic_path))


def main():
    if len(sys.argv) == 3:
        template_path = sys.argv[1]
        flow_chart_path = sys.argv[2]
        params_path = sys.argv[3]
    else:
        template_path = 'templates/TT.odt'
        #template_path = 'parameters.odt'
        flow_chart_path = 'stumuz.odg'
        params_path = 'stumuz.xml'

    template_params = {}
    template_params['param'] = parseParameters(params_path)

    flow_chart_name = basefilename(flow_chart_path)
    flow_chart_page_filenames = convertODG(flow_chart_path, flow_chart_name+'.png')
    if len(flow_chart_page_filenames):
        template_params['flow_chart'] = []
        for name in flow_chart_page_filenames:
            template_params['flow_chart'].append({'name' : name, 'url' : 'Pictures/' + name})

    result_path = u'%s_%s.odt' % (basefilename(template_path), basefilename(params_path))
    renderTemplate(template_path, flow_chart_page_filenames, template_params, result_path)

if __name__ == '__main__':
    main()
