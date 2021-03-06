#!usr/bin/python
# -*- coding: utf8 -*-
encoding='utf8'

VERSION = '2.5.1'

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
    """Returns name part of filename in given path"""
    return os.path.splitext(os.path.basename(path))[0]

def renderTemplate(template_path, template_parameters, result_path):
    """
    Renders template with given data.
    template_path       - Path to template .odt file;
    template_parameters - Parsed data to fill the template;
    result_path         - Path to result .odt file
    Term "render" means creating new document by filling template with data.
    Function perfoms following steps:
    1) Extract content of template to temporary directory;
    2) Render file styles.xml;
    3) Render file content.xml;
    4) Copy used pictures to "Pictures" directory;
    5) Remove unused pictures from "Pictures" directory;
    6) Update "META-INF/manifest.xml" with new pictures;
    7) Pack temporary directory to result_path.
    """
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

    image_replacements = t.imageUrls()
    for key in image_replacements.iterkeys():
        value = image_replacements[key]
        for flow_chart_path in value:
            dest_path = os.path.join(temp_dir, 'Pictures', os.path.basename(flow_chart_path))
            shutil.copy2(flow_chart_path, dest_path)
    replaceManifest(temp_dir, image_replacements)
    cleanPictures(temp_dir, image_replacements.keys())

    packAll(temp_dir, result_path)
    if os.path.exists('Pictures'):
        shutil.rmtree('Pictures')
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)

def replaceManifest(dest_dir, image_replacements):
    import re
    re_image = re.compile(ur'(?imu) <manifest:file\-entry manifest:media\-type="image\/\w+" manifest:full\-path="(Pictures\/[a-f0-9]+\.\w+)"\/>')
    image_pattern = ' <manifest:file-entry manifest:media-type="image/%(ext)s" manifest:full-path="%(path)s"/>'

    manifest_path = os.path.join(dest_dir, 'META-INF', 'manifest.xml')
    manifest_lines = open(manifest_path, 'rb').readlines()
    result = []

    for line in [a.rstrip() for a in manifest_lines]:
        m = re_image.match(line)
        if m:
            source_image = m.group(1)
            if image_replacements.has_key(source_image):
                #print '-', source_image
                for dest_image in image_replacements[source_image]:
                    local_path = '/'.join(['Pictures', os.path.basename(dest_image)])
                    ext = os.path.splitext(dest_image)[1][1:]
                    result.append(image_pattern % {'path' : local_path, 'ext' : ext})
                    #print '+', dest_image
            else:
                result.append(line)
        else:
            result.append(line)

    open(manifest_path, 'wb').write('\n'.join(result))

def cleanPictures(odt_path, to_delete):
    pic_path = os.path.join(odt_path, 'Pictures')
    if os.path.exists(pic_path):
        existing_pics = os.listdir(pic_path)
        for pic in existing_pics:
            pic_path = '/'.join(['Pictures', pic])
            if pic_path in to_delete:
                #print '-', pic_path
                os.unlink(os.path.join(odt_path, pic_path))
            else:
                #print '~', pic_path
                pass

def DoDoc(template_path, xml_path, result_path):
    """
    Main function.
    template_path       - Path to template .odt file;
    xml_path            - Path to .xml with data to fill the template;
    result_path         - Path to result .odt file.
    Function calls DoDoc_parameters_parser.parseParameters_XML() to parse
    input data from xml_path.
    Then calls renderTemplate() to generate output file at result_path.
    """

    try:
        open(result_path, "ab").close()
    except IOError, e:
        print (u'ERROR: Can not open output file: "%s"' % (os.path.abspath(result_path))).encode('cp866', 'replace')
        raise
    else:
        template_params = parseParameters_XML(open(xml_path, 'rb').read())
        renderTemplate(template_path, template_params, result_path)

def main():
    try:
        from optparse import OptionParser
        opts = OptionParser()
        opts.add_option("-t", "--template", dest="template_path",   help="input ODT template file path")
        opts.add_option("-x", "--xml",      dest="xml_path",        help="input XML parameters file path")
        opts.add_option("-o", "--output",   dest="result_path",     help="output ODT result file path")
        opts.add_option("-v", "--version",  action="store_true", dest="version", default=False, help="print current version")
        (options, args) = opts.parse_args()
        if options.version:
            print VERSION
            return
        if options.template_path:
            template_path = options.template_path
        else:
            print 'ERROR: template path not specified. Use --help for command line arguments help.'
            return
        if options.xml_path:
            xml_path = options.xml_path
        else:
            print 'ERROR: xml path not specified. Use --help for command line arguments help.'
            return
        if options.result_path:
            result_path = options.result_path
        else:
            print 'WARNING: result path not specified. Use --help for command line arguments help.'
            result_path = os.path.join(os.path.dirname(xml_path), u'%s_%s.odt' % (basefilename(template_path), basefilename(xml_path)))
            print 'Using "%s" by default.' % (result_path,)
        DoDoc(template_path, xml_path, result_path)
    except Exception, e:
        import traceback
        import DoDoc_error_reporter
        DoDoc_error_reporter.reportError(traceback.format_exc(30))


if __name__ == '__main__':
    main()
