import os
import sys
import time
import json
import socket
import DoDoc.DoDoc_parameters_parser
import DoDoc.odg2wmf
import DoDoc.odt2pdf
import DoDoc.DoDoc
import xml.sax
import glob

uno_port = 2002

def odg2wmf(con, odg):
    global uno_port
    lock_name = os.path.join(os.path.dirname(odg), 'in-progress.lock')
    input = odg
    output = input + '.wmf'
    o = DoDoc.odg2wmf.Odg2wmf()
    o.setConnection(con)
    print 'start', input
    if o.open(input):
        result = o.saveWMF(output)
        o.close()
        print 'done', output
    o.disconnect()
    os.remove(lock_name)

def odt2pdf(con, input, output):
    global uno_port
    input_lock  = input + '.in-progress.lock'
    while os.path.exists(input_lock):
        time.sleep(0.1)
    output_lock = output + '.in-progress.lock'
    o = DoDoc.odt2pdf.Odt2pdf()
    o.setConnection(con)
    print 'start', input
    if o.open(input):
        result = o.savePDF(output)
        o.close()
        print 'done', output
    else:
        print 'Can NOT open input file'
        return False
    o.disconnect()
    os.remove(output_lock)

def dodoc(template, xml, mappings):
    if(mappings.has_key(xml)):
        xml = mappings[xml]
    for dirname in mappings.itervalues():
        lock_name = os.path.join(dirname, 'in-progress.lock')
        watchdog = int(50 / 0.1)
        while not os.path.exists(dirname):
            time.sleep(0.1)
            watchdog-= 1
            if watchdog == 0:
                print 'Error', dirname, 'seems to be broken'
                return False
        while os.path.exists(lock_name):
            time.sleep(0.1)
            watchdog-= 1
            if watchdog == 0:
                print 'Error', dirname, 'seems to be broken'
                return False
    result_odt = '%s_%s.odt' % (os.path.splitext(os.path.basename(template))[0], xml)
    result_pdf = '%s_%s.pdf' % (os.path.splitext(os.path.basename(template))[0], xml)
    if not os.path.exists(result_odt):
        template_params = parseDoDoc_XML(open(command['xml'], 'rb').read(), mappings)
        template = os.path.join('templates', command['template'])
        #print result_odt
        DoDoc.DoDoc.renderTemplate(template, template_params, result_odt)
        odt_lock  = result_odt + '.in-progress.lock'
        os.remove(odt_lock)

class MappingParser(DoDoc.DoDoc_parameters_parser.Parser):
    def __init__(self, mappings):
        self.mappings = mappings
        DoDoc.DoDoc_parameters_parser.Parser.__init__(self)

    def parseIMAGE(self):
        print 'subclassed __parseImage_ready from', self.__class__
        path = self.content
        if os.path.splitext(path)[1].lower() == u'.odg':
            return self.__parseODG(path)
        elif os.path.splitext(path)[1].lower() in [u'.wmf', u'.gif', u'.png']:
            return self.__parseImage_ready(path)
        else:
            print (u'Error: Only .wmf, .gif, .png and .odg images are allowed: "%s"' % (path)).encode('cp866', 'replace')
        return []

    def __parseODG(self, odg_path):
        print 'subclassed __parseODG from', self.__class__
        if self.mappings.has_key(odg_path):
            dir_name = self.mappings[odg_path]
            wmfs = glob.glob(os.path.join(dir_name, '*.wmf'))
            print 'mapped', wmfs
            return wmfs

def parseDoDoc_XML(xml_content, file_mappings):
    p = MappingParser(file_mappings)
    xml.sax.parseString(xml_content, p)
    return DoDoc.DoDoc_parameters_parser.expandImages_in_tables(p.tree)
    return p.tree


HOST, PORT = "127.0.0.1", 5555

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((HOST, PORT))
print 'Connected'
command = json.loads(sock.recv(4096).strip())
uno_port = command['port']
print 'Port received:', uno_port
o = DoDoc.OpenOffice_document.OpenOffice()
uno_connected = o.connect(uno_port)
sock.send(json.dumps({'result': uno_connected}) + "\n")
if uno_connected:
    try:
        print 'Started'
        while(True):
            print 'Waiting for command'
            command = json.loads(sock.recv(4096).strip())
            if command['op'] == 'odg2wmf':
                odg2wmf(o.connection(), command['odg'])
                sock.send(json.dumps({'result' : True}) + '\n')
            elif command['op'] == 'odt2pdf':
                odt2pdf(o.connection(), command['odt'], command['pdf'])
                sock.send(json.dumps({'result' : True}) + '\n')
            elif command['op'] == 'dodoc':
                result = dodoc(command['template'], command['xml'], command['session'])
                sock.send(json.dumps({'result' : result}) + '\n')
            else:
                sock.send(json.dumps({'result' : False, 'reason' : 'Unrecognized op'}) + '\n')
                print 'Unrecognized op:', command['op']
    except Exception, e:
        print "Exception occured:"
        import traceback
        print traceback.format_exc(30)
    o.disconnect()
sock.close()
