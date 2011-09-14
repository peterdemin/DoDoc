import os
import sys
import subprocess

def odg2png(input_filename, output_filename):
    try:
        return odg2png_unchecked(input_filename, output_filename)
    except Exception, e:
        if hasattr(e, 'typeName') and (e.typeName == 'com.sun.star.connection.NoConnectException'):
            import time
            soffice_process = subprocess.Popen(["soffice.exe", "-headless", "-nofirststartwizard", "-accept=socket,host=localhost,port=2002;urp;"])
            #time.sleep(5.0)
            result = odg2png_unchecked(input_filename, output_filename)
            try:
                soffice_process.kill()
            except WindowsError, e:
                pass # WindowsError (code 5) may occur, if openoffice was opened by user
            return result
        else:
            raise
    return None

def odg2png_unchecked(input_filename, output_filename):
    from import_uno import uno

    from com.sun.star.io import IOException, XOutputStream, XSeekable, XInputStream
    from com.sun.star.beans import PropertyValue

    from OpenOffice_document import InputStream
    from OpenOffice_document import OutputStream
    from OpenOffice_document import Document

    OOO_CONNECTION = 'socket,host=localhost,port=2002;urp;StarOffice.ComponentContext'
    context = uno.getComponentContext()
    resolver = context.ServiceManager.createInstanceWithContext('com.sun.star.bridge.UnoUrlResolver', context)
    unocontext = resolver.resolve('uno:%s' % OOO_CONNECTION)
    unosvcmgr = unocontext.ServiceManager
    desktop = unosvcmgr.createInstanceWithContext('com.sun.star.frame.Desktop', unocontext)
    config = unosvcmgr.createInstanceWithContext('com.sun.star.configuration.ConfigurationProvider', unocontext)

    ### Load inputfile
    document = Document(input_filename)
    document.delete_on_close = False
    instream = InputStream(uno.ByteSequence(document.read()))
    inputprops = [
                  PropertyValue('InputStream', 0, instream, 0),
                  PropertyValue('Hidden', 0, True, 0),
                 ]
    document.close()
    doc = desktop.loadComponentFromURL('private:stream','_blank',0, tuple(inputprops))

    doc_controller = doc.getCurrentController()
    draw_pages = doc.getDrawPages()
    pages_amount  = draw_pages.getCount()

    created_files = []

    for page_id in range(pages_amount):
        noext, ext = os.path.splitext(output_filename)
        cur_output_filename = composeOO_name(u'%s_%d%s' % (noext, page_id, ext))
        doc_controller.setCurrentPage(draw_pages.getByIndex(page_id))

        dirname = os.path.dirname(cur_output_filename)
        if len(dirname):
            if not os.path.exists(dirname):
                os.makedirs(dirname)
        fd = open(cur_output_filename, 'wb')
        filter_name = 'draw_png_Export'
        outputprops = [
            #PropertyValue('FilterData',
            #    (("Compression", 0, 6, com.sun.star.beans.PropertyState.DIRECT_VALUE),
            #    ("Interlaced", 0, true, com.sun.star.beans.PropertyState.DIRECT_VALUE))
            #"MediaType", "image/png" 
            PropertyValue('FilterData', 0, uno.Any('[]com.sun.star.beans.PropertyValue', tuple(),), 0),
            PropertyValue('FilterName', 0, filter_name, 0),
            PropertyValue('OutputStream', 0, OutputStream(fd), 0),
            PropertyValue('Overwrite', 0, True, 0),
        ]
        if filter_name == 'Text (encoded)':
            outputprops.append(PropertyValue('FilterFlags', 0, 'UTF8, LF', 0))

        doc.storeToURL('private:stream', tuple(outputprops))
        created_files.append(cur_output_filename)
        fd.close()
    doc.dispose()
    doc.close(True)
    return created_files

def composeOO_name(file_path):
    import hashlib
    dirname = os.path.dirname(file_path)
    if(len(dirname)):
        dirname+= '/'
    noext, ext = os.path.splitext(file_path)
    checksum = hashlib.sha1(file_path).hexdigest()[:8].upper()
    width, height = 0x31A, 0x463
    return u'%s10000000%08X%08X%s%s' % (dirname, width, height, checksum, ext)

def main():
    from pprint import pprint
    input = 'svbsa101k2.odg'
    output = 'Pictures/svbsa101k2.png'
    if len(sys.argv) == 3:
        input = sys.argv[1]
        output = sys.argv[2]
    else:
        print 'Usage:'
        print '    python odg2png input_odg_filename output_png_filename'
    pprint( odg2png(input, output) )

if __name__ == '__main__':
    main()
