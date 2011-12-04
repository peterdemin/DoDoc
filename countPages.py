from OpenOffice_document import *

class Page_counter(OpenOffice):
    def __init__(self):
        super(Page_counter, self).__init__()

    def updateAll(self, doc_controller_ = None):
        if doc_controller_:
            doc_controller = doc_controller_
        else:
            doc_controller = self.doc.getCurrentController()
        frame = doc_controller.getFrame()
        self.dispatcher.executeDispatch(frame, ".uno:UpdateAll", "", 0, ())

    def countPages(self):
        '''Method uses duck-typing instead of analyzing file extension'''
        doc_controller = self.doc.getCurrentController()
        if hasattr(doc_controller, "PageCount"):
            self.updateAll(doc_controller)
            return doc_controller.PageCount
        elif hasattr(self.doc, "getDrawPages"):
            draw_pages = self.doc.getDrawPages()
            return draw_pages.getCount()

def countPages(filename):
    o = Page_counter()
    if o.connect():
        if o.open(filename):
            print o.countPages()
            o.close()
    o.disconnect()

def main():
    try:
        import sys
        if len(sys.argv) == 2:
            input = sys.argv[1]
        else:
            print 'countPages prints to stdout amount of pages in passed document.'
            print 'Following document types are accepted: .odt, .odg'
            print 'Usage:'
            print '    python countPages input_filename'
            return
            input = 'Manual_.odt'
        countPages(input)
    except Exception, e:
        import traceback
        import DoDoc_error_reporter
        DoDoc_error_reporter.reportError(traceback.format_exc(30))

if __name__ == '__main__':
    main()
