from OpenOffice_document import *

class Odg2wmf(OpenOffice):
    def __init__(self):
        super(Odg2wmf, self).__init__()

    def saveWMF(self, filename):
        doc_controller  = self.doc.getCurrentController()
        draw_pages      = self.doc.getDrawPages()
        pages_amount    = draw_pages.getCount()
        (noext, ext) = os.path.splitext(filename)
        created_files = []
        for page_id in range(pages_amount):
            cur_output_filename = self.composeOO_name(u'%s_%d%s' % (noext, page_id, ext))
            doc_controller.setCurrentPage(draw_pages.getByIndex(page_id))
            if self.saveCurrent_page(cur_output_filename):
                created_files.append(cur_output_filename)
        return created_files

    def saveCurrent_page(self, filename):
        try:
            output_stream = OutputStream(open(filename, 'wb'))
            outputprops = [
                PropertyValue('FilterData', 0, uno.Any('[]com.sun.star.beans.PropertyValue', tuple(),), 0),
                PropertyValue('FilterName', 0, 'draw_wmf_Export', 0),
                PropertyValue('OutputStream', 0, output_stream, 0),
                PropertyValue('Overwrite', 0, True, 0),
            ]
            self.doc.storeToURL('private:stream', tuple(outputprops))
            return True
        except IOError, e:
            error(u'Error: Can not open output file: "%s"' % (os.path.abspath(filename)))
            return False

    def composeOO_name(self, file_path):
        import hashlib
        dirname = os.path.dirname(file_path)
        if(len(dirname)):
            dirname+= '/'
        noext, ext = os.path.splitext(file_path)
        checksum = hashlib.sha1(file_path).hexdigest()[:8].upper()
        width, height = 0x31A, 0x463
        return u'%s10000000%08X%08X%s%s' % (dirname, width, height, checksum, ext)

def odg2wmf(input, output):
    result = None
    try:
        o = Odg2wmf()
        if o.connect():
            if o.open(input):
                result = o.saveWMF(output)
                o.close()
        o.disconnect()
    except Exception, e:
        import traceback
        import DoDoc_error_reporter
        DoDoc_error_reporter.reportError(traceback.format_exc(30))
    return result

def main():
    import sys
    if len(sys.argv) == 3:
        input = sys.argv[1]
        output = sys.argv[2]
    else:
        print 'Usage:'
        print '    python odg2wmf input_odg_filename output_wmf_filename'
        #return
        input = 'svbsa101k2.odg'
        output = 'svbsa101k2.wmf'
    print '\n'.join(odg2wmf(input, output))

if __name__ == '__main__':
    main()
