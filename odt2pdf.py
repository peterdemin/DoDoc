def odt2pdf(input_filename, output_filename):
    from start_uno import runWithStarted_soffice
    return runWithStarted_soffice(odt2pdf_unchecked, input_filename, output_filename)

def odt2pdf_unchecked(desktop, input_filename, output_filename):
    from import_uno import uno
    from OpenOffice_document import OutputStream
    from com.sun.star.beans import PropertyValue
    from start_uno import loadDocument

    doc = loadDocument(desktop, input_filename)

    context = uno.getComponentContext()
    dispatcher = context.ServiceManager.createInstanceWithContext('com.sun.star.frame.DispatchHelper', context)
    frame = doc.getCurrentController().getFrame()
    dispatcher.executeDispatch(frame, ".uno:UpdateAll", "", 0, ())

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
    import sys
    input = 'Variables_variables.odt'
    output = 'Variables_variables.pdf'
    if len(sys.argv) == 3:
        input = sys.argv[1]
        output = sys.argv[2]
    else:
        print 'Usage:'
        print '    python odt2pdf input_odt_filename output_pdf_filename'
    odt2pdf(input, output)
    #print 'done'

if __name__ == '__main__':
    main()
