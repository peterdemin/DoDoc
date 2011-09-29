import os

def odg2png(input_filename, output_filename):
    from start_uno import runWithStarted_soffice
    return runWithStarted_soffice(odg2png_unchecked, input_filename, output_filename)

def odg2png_unchecked(desktop, input_filename, output_filename):
    from import_uno import uno
    from OpenOffice_document import OutputStream
    from com.sun.star.beans import PropertyValue
    from start_uno import loadDocument

    doc = loadDocument(desktop, input_filename)

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
    import sys
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
