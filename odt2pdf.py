from OpenOffice_document import *

class Odt2pdf(OpenOffice):
    def __init__(self):
        super(Odt2pdf, self).__init__()

    def updateAll(self):
        frame = self.doc.getCurrentController().getFrame()
        self.dispatcher.executeDispatch(frame, ".uno:UpdateAll", "", 0, ())

    def savePDF(self, filename):
        try:
            output_stream = OutputStream(open(filename, 'wb'))
            self.updateAll()
            outputprops = [
                PropertyValue('FilterData', 0, uno.Any('[]com.sun.star.beans.PropertyValue', tuple(),), 0),
                PropertyValue('FilterName', 0, 'writer_pdf_Export', 0),
                PropertyValue('OutputStream', 0, output_stream, 0),
                PropertyValue('Overwrite', 0, True, 0),
            ]
            self.doc.storeToURL('private:stream', tuple(outputprops))
            return True
        except IOError, e:
            error(u'Error: Can not open output file: "%s"' % (os.path.abspath(filename)))
            return False

def odt2pdf(input, output):
    try:
        o = Odt2pdf()
        if o.connect():
            if o.open(input):
                o.savePDF(output)
                o.close()
        o.disconnect()
    except Exception, e:
        import traceback
        import DoDoc_error_reporter
        DoDoc_error_reporter.reportError(traceback.format_exc(30))
    
def main():
    import sys
    if len(sys.argv) == 3:
        input = sys.argv[1]
        output = sys.argv[2]
    else:
        print 'Usage:'
        print '    python odt2pdf input_odt_filename output_pdf_filename'
        return
        input = 'test.odt'
        output = 'test.pdf'
    odt2pdf(input, output)

if __name__ == '__main__':
    main()
