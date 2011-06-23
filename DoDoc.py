from import_uno import uno
#import unohelper
import os
import re
import sys
import shutil
from pprint import pprint
from com.sun.star.beans import PropertyValue
from Template import Template
import hashlib

import codecs

from OpenOffice_document import InputStream
from OpenOffice_document import OutputStream
from OpenOffice_document import Document
from OpenOffice_document import getTree
from OpenOffice_document import extractAll
from OpenOffice_document import packAll

def convertODT(input_filename, output_filename):
    OOO_CONNECTION = 'socket,host=localhost,port=2002;urp;StarOffice.ComponentContext'
    context = uno.getComponentContext()
    resolver = context.ServiceManager.createInstanceWithContext('com.sun.star.bridge.UnoUrlResolver', context)
    unocontext = resolver.resolve('uno:%s' % OOO_CONNECTION)
    #print 'resolver:', type(resolver)
    #print u', '.join(dir(resolver))
    #print 'unocontext:', type(unocontext)
    #print u', '.join(dir(unocontext))

    unosvcmgr = unocontext.ServiceManager
    desktop = unosvcmgr.createInstanceWithContext('com.sun.star.frame.Desktop', unocontext)
    config = unosvcmgr.createInstanceWithContext('com.sun.star.configuration.ConfigurationProvider', unocontext)

    print 'unosvcmgr:', type(unosvcmgr)
    print u', '.join(dir(unosvcmgr))
    print 'desktop:', type(desktop)
    print u', '.join(dir(desktop))
    print 'config:', type(config)
    print u', '.join(dir(config))

    document = Document(input_filename)
    document.delete_on_close = False

    ### Load inputfile
    instream = InputStream(uno.ByteSequence(document.read()))
    document.close()
    inputprops = [
        PropertyValue('InputStream', 0, instream, 0),
    ]
    del document
    
    doc = desktop.loadComponentFromURL('private:stream','_blank',0, tuple(inputprops))

    fd = open(output_filename, 'wb')
    filter_name = 'writer_pdf_Export'
    outputprops = [
        PropertyValue('FilterData', 0, uno.Any('[]com.sun.star.beans.PropertyValue', tuple(),), 0),
        PropertyValue('FilterName', 0, filter_name, 0),
        PropertyValue('OutputStream', 0, OutputStream(fd), 0),
        PropertyValue('Overwrite', 0, True, 0),
    ]
    if filter_name == 'Text (encoded)':
        outputprops.append(PropertyValue('FilterFlags', 0, 'UTF8, LF', 0))

    doc.storeToURL('private:stream', tuple(outputprops))
    doc.dispose()
    doc.close(True)
    fd.close()


def composeOO_name(file_path):
    noext, ext = os.path.splitext(file_path)
    checksum = hashlib.md5(file_path).hexdigest()[:8].upper()
    width, height = 0x31A, 0x463
    return u'10000000%08X%08X%s%s' % (width, height, checksum, ext)

def copyExternal(dest_dir):
    copy_table = {}
    for src_path in ('svbsa101k2_0.png', 'svbsa101k2_1.png', 'svbsa101k2_2.png'):
        url = '/'.join(['Pictures', composeOO_name(src_path)])
        dest_path = os.path.join(dest_dir, url)
        shutil.copy2(src_path, dest_path)
        copy_table[src_path] = url
    return copy_table

def replaceManifest(manifest_xml, png_list):
    re_png = re.compile(ur'(?imu) <manifest:file\-entry manifest:media\-type="image\/png" manifest:full\-path="(Pictures\/[a-f0-9]+.png)"\/>')

    png_pattern = ' <manifest:file-entry manifest:media-type="image/png" manifest:full-path="%s"/>'
    png_lines = '\n'.join([png_pattern % png for png in png_list])

    return re_png.sub(png_lines, manifest_xml)

def cleanPictures(odt_path, used):
    pic_path = os.path.join(odt_path, 'Pictures')
    existing_pics = os.listdir(pic_path)
    for pic in existing_pics:
        pic_path = u'/'.join(['Pictures', pic])
        if not pic_path in used:
            print '-', pic_path
            os.unlink(os.path.join(odt_path, pic_path))

def main():
    parameters = {
            u'name' : u'World',
            u'table1' :
                (
                    {'id' : '1', 'name' : 'SIAM.00479', 'description' : 'Test1'},
                    {'id' : '2', 'name' : 'SIAM.00172', 'description' : 'Test2'}
                ),
            }

    extractAll('1.odt', '1_out')
    copied = copyExternal('1_out')

    manifest_path = os.path.join('1_out', 'META-INF/manifest.xml')
    manifest_xml = open(manifest_path, 'r').read()
    open(manifest_path, 'w').write(replaceManifest(manifest_xml, copied.values()))

    pprint(copied)
    parameters[u'flow_chart'] = []
    for k, v in copied.items():
        parameters[u'flow_chart'].append({'name' : k, 'url' : v})
    pprint(parameters)

    content_xml = open(os.path.join('1_out', 'content.xml'), 'r').read()
    t = Template(content_xml, parameters)
    rendered_content_xml = t.render()
    cleanPictures('1_out', t.imageUrls())
    codecs.open(os.path.join('1_out', 'content.xml'), 'w', 'utf-8').write(rendered_content_xml)
    packAll('1_out', '1_out.odt')
    print 'convert'
    convertODT('1_out.odt', '1_out.pdf')
    print 'done'

if __name__ == '__main__':
    main()
