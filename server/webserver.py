import os
import time
import re
import time
import socket
import threading
import mimetypes
import email.parser
import json
import hashlib
import SocketServer
import BaseHTTPServer

# monkey-patching bug:
BaseHTTPServer.BaseHTTPRequestHandler.address_string = lambda self: self.client_address[0]

class Tasks(object):
    def __init__(self):
        self.workers = []
        self.workers_lock = threading.RLock()

    def createWorker(self):
        worker = {}
        worker['busy'] = False
        worker['event'] = threading.BoundedSemaphore(1)
        worker['event'].acquire()
        worker['payload'] = None
        with self.workers_lock:
            self.workers.append(worker)
        return worker

    def removeWorker(self, worker):
        with self.workers_lock:
            for i, w in enumerate(self.workers):
                if w['event'] == worker['event']:
                    self.workers.pop(i)

    def addTask(self, payload, callback = None):
        while(True):
            with self.workers_lock:
                for w in self.workers:
                    if not w['busy']:
                        w['busy'] = True
                        w['payload'] = payload
                        if(callback):
                            w['callback'] = callback
                        else:
                            if w.has_key('callback'):
                                w.pop('callback')
                        w['event'].release()
                        return
            # Everyone is busy
            time.sleep(0.1)
        
tasks  = Tasks()


class MyHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        BaseHTTPServer.BaseHTTPRequestHandler.__init__(self, *args, **kwargs)

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
                self.waitWhile_exists(filepath + '.in-progress.lock')
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

    def waitWhile_exists(self, filename):
        while(os.path.exists(filename)):
            time.sleep(0.1)

    def sendText(self, text):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(text)

    def do_POST(self):
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
                        tasks.addTask(json.dumps({'op' : 'odg2wmf', 'odg' : new_filename, 'wmf' : new_filename + '.odg'}))
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

        result_odt = '%s_%s.odt' % (os.path.splitext(os.path.basename(command['template']))[0], command['xml'])
        result_pdf = '%s_%s.pdf' % (os.path.splitext(os.path.basename(command['template']))[0], command['xml'])
        if not os.path.exists(result_odt):
            open(result_odt + '.in-progress.lock', 'wt').write('webserver.dodoc')
            tasks.addTask(json.dumps({'op' : 'dodoc',
                                      'xml' : command['xml'],
                                      'template' : command['template'],
                                      'session' : file_mappings}))
        if not os.path.exists(result_pdf):
            open(result_pdf + '.in-progress.lock', 'wt').write('webserver.dodoc')
            tasks.addTask(json.dumps({'op' : 'odt2pdf',
                                      'odt' : result_odt,
                                      'pdf' : result_pdf}))
        self.wfile.write(json.dumps({'odt' : result_odt, 'pdf' : result_pdf}))
        self.wfile.flush()
        self.connection.shutdown(1)

    def ping(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write('pong')

    def shutdown(self):
        global terminate_server
        self.send_response(200)
        self.end_headers()
        self.wfile.write('shutting down')
        #server.shutdown()
        terminate_server = True

    def address_string(self):
        return self.client_address[0]

    handlers = {
                re.compile(r'(?i)/dodoc/') : dodoc,
                re.compile(r'(?i)/add/') : add,
                re.compile(r'(?i)/ping/') : ping,
                re.compile(r'(?i)/shutdown/') : shutdown,
               }

unused_uno_port = 2003
uno_lock = threading.RLock()

def getUnused_port():
    global unused_uno_port
    with uno_lock:
        r = unused_uno_port
        unused_uno_port+= 1
        return r

class SocketHandler(SocketServer.StreamRequestHandler):
    def handle(self):
        #print 'Worker connected:', self.client_address
        if(self.setupWorker()):
            print 'Worker added:', self.client_address
            while(True):
                payload = self.getTask()
                #print 'Got task:', self.client_address
                if self.isWorker_online():
                    #print 'Worker online:', self.client_address
                    self.wfile.write(payload + '\n')
                    result = self.rfile.readline().strip()
                    self.finishTask(result)
                else:
                    #print 'Worker offline:', self.client_address
                    tasks.removeWorker(self.task)
                    if self.task.has_key('callback'):
                        tasks.addTask(self.task['payload'], self.task['callback'])
                    else:
                        tasks.addTask(self.task['payload'])
                    print 'Task returned to queue:', self.client_address
                    break
        print 'Worker offline:', self.client_address

    def isWorker_online(self):
        try:
            self.wfile.write(json.dumps({'op' : 'ping'}) + '\n')
            answer = json.loads(self.rfile.readline().strip())
            if answer['result'] == u'pong':
                return True
        except socket.error, e:
            if e.errno == 10054:
                #print 'Worker offline.'
                pass
            else:
                raise
        return False

    def getTask(self):
        self.task['event'].acquire()
        return self.task['payload']

    def finishTask(self, result):
        self.task['busy'] = False
        if self.task.has_key('callback'):
            self.task['callback'](result)

    def setupWorker(self):
        self.wfile.write(json.dumps({'port' : getUnused_port()}) + '\n')
        answer = json.loads(self.rfile.readline().strip())
        if answer['result'] == True:
            self.task = tasks.createWorker()
            return True
        else:
            return False

class ThreadingSocketServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    """Socket server, that uses multiple processes to handle requests"""

def startServer():
    try:
        #server = SocketServer.TCPServer(('localhost', 5555), SocketHandler)
        server = ThreadingSocketServer(('localhost', 5555), SocketHandler)
        server.serve_forever()
    except socket.error, e:
        if e.errno == 10048:
            print 'Server allready running'
        else:
            raise

class ThreadingHTTPServer(SocketServer.ThreadingMixIn, BaseHTTPServer.HTTPServer):
    """HTTP server, that uses multiple processes to handle requests"""

def main():
    server_thread = threading.Thread(target=startServer)
    server_thread.start()
    try:
        server = BaseHTTPServer.HTTPServer(('', 8080), MyHandler)
        #server = ThreadingHTTPServer(('', 80), MyHandler)
        print 'started httpserver...'
        server.serve_forever()
    except KeyboardInterrupt:
        print '^C received, shutting down server'
        server.socket.close()
    server_thread.join()

if __name__ == '__main__':

    #import cProfile
    #cProfile.run('main()', 'temp_profile')

    #import pstats
    #p = pstats.Stats('temp_profile')
    #p.strip_dirs().sort_stats('cumulative').print_stats(50)

    main()
