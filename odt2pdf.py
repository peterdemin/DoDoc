from import_uno import uno
from com.sun.star.beans import PropertyValue

from OpenOffice_document import InputStream
from OpenOffice_document import OutputStream
from OpenOffice_document import Document

def odt2pdf(input_filename, output_filename):
    OOO_CONNECTION = 'socket,host=localhost,port=2002;urp;StarOffice.ComponentContext'
    context = uno.getComponentContext()
    resolver = context.ServiceManager.createInstanceWithContext('com.sun.star.bridge.UnoUrlResolver', context)
    unocontext = resolver.resolve('uno:%s' % OOO_CONNECTION)

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

def main():
    odt2pdf('Variables_variables.odt', 'Variables_variables.pdf')
    print 'done'

if __name__ == '__main__':
    main()
