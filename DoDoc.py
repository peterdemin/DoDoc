from import_uno import uno
#import unohelper
import os
import sys
import shutil
from pprint import pprint
from com.sun.star.beans import PropertyValue
from Template import Template

import codecs

from OpenOffice_document import InputStream
from OpenOffice_document import OutputStream
from OpenOffice_document import Document
from OpenOffice_document import getTree
from OpenOffice_document import extractAll
from OpenOffice_document import packAll

def convert(input_filename, output_filename):
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

    return

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

    #print 'done'
    #del doc
    #del fd
    #print 'del1'
    #del config
    #del desktop
    #del unosvcmgr
    #del unocontext
    #del resolver
    #del context
    #print 'del2'

def main():
    shutil.copy2('1.odt', '1_out.odt')
    extractAll('1_out.odt', '1_out')
    content_xml = open(os.path.join('1_out', 'content.xml'), 'r').read()
    t = Template(content_xml)
    rendered_content_xml = t.render()
    codecs.open(os.path.join('1_out', 'content.xml'), 'w', 'utf-8').write(rendered_content_xml)
    packAll('1_out', '1_out.odt')
    convert('1_out.odt', '1_out.pdf')

if __name__ == '__main__':
    main()
