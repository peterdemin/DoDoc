from import_uno import uno
#import uno
import unohelper

from com.sun.star.io import IOException, XOutputStream, XSeekable, XInputStream
from com.sun.star.beans import PropertyValue

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

    #print 'desktop:', type(desktop)
    #print u', '.join(dir(desktop))
    #print 'config:', type(config)
    #print u', '.join(dir(config))

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

    #pprint(dir(doc))

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

if __name__ == '__main__':
    main()
