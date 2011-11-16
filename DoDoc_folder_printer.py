#!usr/bin/python
# -*- coding: utf8 -*-
encoding='utf8'
'''утф-8'''

import os
from OpenOffice_document import *

class Odt_printer(OpenOffice):
    def __init__(self):
        super(Odt_printer, self).__init__()

    def startPrinting(self, filename):
        frame = self.doc.getCurrentController().getFrame()
        self.dispatcher.executeDispatch(frame, ".uno:UpdateAll", "", 0, ())
        props = [
                 PropertyValue('Hidden', 0, True, 0),
                 ]
        self.dispatcher.executeDispatch(frame, ".uno:Print", "", 0, tuple(props))
        return True

def printODT(inputs):
    o = Odt_printer()
    #print 'connect'
    if o.connect():
        #print 'open'
        for input in inputs:
            if o.open(input):
                #print 'print'
                o.startPrinting(input)
                import time
                #print 'sleeping...'
                time.sleep(10)
                #print 'close'
                o.close()
    #print 'disconnect'
    o.disconnect()

def odts_in_folder(folder_name):
    odts = []
    if os.path.exists(folder_name):
        if os.path.isdir(folder_name):
            for item in os.listdir(folder_name):
                item_path = os.path.join(folder_name, item)
                if os.path.isdir(item_path):
                    odts.extend(odts_in_folder(item_path))
                else:
                    noext, ext = os.path.splitext(item_path)
                    if ext.lower() == '.odt':
                        odts.append(item_path)
        elif os.path.isfile(folder_name):
            noext, ext = os.path.splitext(folder_name)
            if ext.lower() == '.odt':
                odts.append(folder_name)
    return odts

def main():
    import sys
    if len(sys.argv) == 2:
        folder_name = sys.argv[1]
    else:
        print 'DoDoc_folder_printer prints all *.odt files in given folder.'
        print 'Usage:'
        print '    python DoDoc_folder_printer.py folder_name'
        return
        #folder_name = 'printme'
    inputs = odts_in_folder(folder_name)
    printODT(inputs)

if __name__ == '__main__':
    main()
