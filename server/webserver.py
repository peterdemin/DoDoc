import os
import time
import re
import cgi
import time
import mimetypes
import email.parser
import json
import hashlib
import BaseHTTPServer
from SocketServer import ThreadingMixIn

class MyHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super(MyHandler, self).__init__(*args, **kwargs)
        print '__init__'

    def getHandler(self, request_path):
        for pattern, handler in self.handlers.iteritems():
            m = pattern.match(request_path)
            if m:
                return lambda: handler(self, *m.groups())
        return None

    def do_GET(self):
        try:
            url_handler = self.getHandler(self.path)
            if url_handler:
                return url_handler()
            if self.path == "/favicon.ico":
                self.send_response(200)
                self.send_header('Content-type', 'image/vnd.microsoft.icon')
                self.end_headers()
                self.wfile.write(open('favicon.ico', 'rb').read())
                return
            if self.path.endswith(".html"):
                f = open(os.curdir + os.sep + self.path) #self.path has /test.html
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(f.read())
                f.close()
                return
            elif self.path.endswith(".odt"):
                filepath = os.curdir + os.sep + self.path
                filesize = os.stat(filepath).st_size
                f = open(filepath, 'rb')
                self.send_response(200)
                self.send_header('Content-Type', 'application/octet-stream')
                self.send_header('Content-Length', str(filesize))
                self.end_headers()
                self.wfile.write(f.read())
                self.wfile.flush()
                self.connection.shutdown(1)
                f.close()
            if self.path.endswith(".esp"):   #our dynamic content
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write("hey, today is the" + str(time.localtime()[7]))
                self.wfile.write(" day in the year " + str(time.localtime()[0]))
                return
            return
        except IOError:
            self.send_error(404,'File Not Found: %s' % self.path)

    def sendText(self, text):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(text)

    def do_POST(self):
        print 'do_POST'
        url_handler = self.getHandler(self.path)
        if url_handler:
            url_handler()
        else:
            print 'Can NOT handle', self.path

    def add(self):
        size = int(self.headers['content-length'])
        content = 'content-type: %s\n\n' % (self.headers['content-type'])
        content+= self.rfile.read(size)
        open('request_add.txt', 'wb').write(content)
        message = email.parser.Parser().parsestr(content)
        payload = message.get_payload()
        new_filename = None
        self.send_response(200)
        self.end_headers()
        post_processing = {}
        result = {}
        for part in payload:
            parameters = dict(filter(lambda b: len(b)==2, [a.strip().split('=') for a in part['Content-Disposition'].split(';')]))
            if parameters.has_key('name') and parameters['name'] == '"upfile"':
                filename = parameters['filename'].strip('"')
                basename, ext = os.path.splitext(filename)
                if ext.lower() == '.odg':
                    file_content = part.get_payload(decode=True)
                    new_dirname = hashlib.md5(file_content).hexdigest()
                    result[filename] = new_dirname
                    if not os.path.exists(new_dirname):
                        os.mkdir(new_dirname)
                        open(os.path.join(new_dirname, 'in-progress.lock'), 'wt').write('!')
                        new_filename = os.path.join(new_dirname, filename)
                        open(new_filename, 'wb').write(file_content)
                        post_processing[filename] = new_filename
                elif ext.lower() == '.xml':
                    file_content = part.get_payload(decode=True)
                    new_filename = hashlib.md5(file_content).hexdigest()
                    result[filename] = new_filename
                    if not os.path.exists(new_filename):
                        open(new_filename, 'wb').write(file_content)
        if len(result):
            self.wfile.write(json.dumps(result))
        else:
            self.wfile.write(json.dumps({'error' : 'no payload'}))
        self.wfile.flush()
        self.connection.shutdown(1)
        if len(post_processing):
            print post_processing.values()
            self.convertODGs(post_processing.values())
            for filename in post_processing.itervalues():
                os.remove(os.path.join(os.path.dirname(filename), 'in-progress.lock'))

    def convertODGs(self, odg_filenames):
        from DoDoc.odg2wmf import Odg2wmf
        result = None
        o = Odg2wmf()
        if o.connect():
            for input in odg_filenames:
                print input
                if o.open(input):
                    output = input + '.wmf'
                    result = o.saveWMF(output)
                    o.close()
        o.disconnect()

    def dodoc(self):
        size = int(self.headers['content-length'])
        content = 'content-type: %s\n\n' % (self.headers['content-type'])
        content+= self.rfile.read(size)
        open('request_dodoc.txt', 'wb').write(content)
        message = email.parser.Parser().parsestr(content)
        payload = message.get_payload()
        self.send_response(200)
        self.end_headers()
        result = {}
        file_mappings, command = {}, {}
        for part in payload:
            parameters = dict(filter(lambda b: len(b)==2, [a.strip().split('=') for a in part['Content-Disposition'].split(';')]))
            if parameters.has_key('name'):
                if parameters['name'] == '"session"':
                    file_mappings = json.loads(part.get_payload(decode=True))
                if parameters['name'] == '"command"':
                    command = json.loads(part.get_payload(decode=True))
        if len(command):
            if(file_mappings.has_key(command['xml'])):
                command['xml'] = file_mappings[command['xml']]
        for dirname in file_mappings.itervalues():
            watchdog = int(50 / 0.1)
            while not os.path.exists(dirname):
                time.sleep(0.1)
                watchdog-= 1
                if watchdog == 0:
                    return self.wfile.write(json.dumps({'error' : dirname + ' seems to be broken'}))
            while os.path.exists(os.path.join(dirname, 'in-progress.lock')):
                time.sleep(0.1)
                watchdog-= 1
                if watchdog == 0:
                    return self.wfile.write(json.dumps({'error' : dirname + ' seems to be broken'}))
        result_odt = '%s_%s.odt' % (os.path.splitext(os.path.basename(command['template']))[0], command['xml'])
        result_pdf = '%s_%s.pdf' % (os.path.splitext(os.path.basename(command['template']))[0], command['xml'])
        self.wfile.write(json.dumps({'odt' : result_odt, 'pdf' : result_pdf}))
        self.wfile.flush()
        self.connection.shutdown(1)
        if not os.path.exists(result_odt):
            from DoDoc import DoDoc
            template_params = parseDoDoc_XML(open(command['xml'], 'rb').read(), file_mappings)
            template = os.path.join('templates', command['template'])
            #print result_odt
            DoDoc.renderTemplate(template, template_params, result_odt)
        if not os.path.exists(result_pdf):
            #print result_pdf
            from DoDoc.odt2pdf import odt2pdf
            odt2pdf(result_odt, result_pdf)

    def ping(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write('pong')

    def address_string(self):
        return self.client_address[0]

    handlers = {
                re.compile(r'(?i)/dodoc/') : dodoc,
                re.compile(r'(?i)/add/') : add,
                re.compile(r'(?i)/ping/') : ping,
               }

import xml.sax
import glob
from DoDoc.DoDoc_parameters_parser import Parser, expandImages_in_tables

class MappingParser(Parser):
    def __init__(self, mappings):
        self.mappings = mappings
        Parser.__init__(self)

    def __parseODG(self, odg_path):
        if mappings.has_key(odg_path):
            dir_name = mappings[odg_path]
            return glob.glob(os.path.join(dir_name, '*.wmf'))

def parseDoDoc_XML(xml_content, file_mappings):
    p = MappingParser(file_mappings)
    xml.sax.parseString(xml_content, p)
    return expandImages_in_tables(p.tree)
    return p.tree

class ThreadingHTTPServer(ThreadingMixIn, BaseHTTPServer.HTTPServer):
    """HTTP server, that uses multiple processes to handle requests"""

def _bare_address_string(self):
    host, port = self.client_address[:2]
    return str(host)

BaseHTTPServer.BaseHTTPRequestHandler.address_string = _bare_address_string

def main():
    try:
        #server = HTTPServer(('', 80), MyHandler)
        server = ThreadingHTTPServer(('', 80), MyHandler)
        print 'started httpserver...'
        server.serve_forever()
    except KeyboardInterrupt:
        print '^C received, shutting down server'
        server.socket.close()

if __name__ == '__main__':
    main()

