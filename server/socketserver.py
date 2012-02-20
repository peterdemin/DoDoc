import time
import socket
import SocketServer
import threading

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

class SocketHandler(SocketServer.StreamRequestHandler):
    def handle(self):
        self.setupWorker()
        while(True):
            payload = self.getTask()
            if self.isWorker_online():
                self.wfile.write(payload + '\n')
                result = self.rfile.readline().strip()
                self.finishTask(result)
            else:
                tasks.removeWorker(task)
                if self.task['callback']:
                    tasks.addTask(self.task['payload'], self.task['callback'])
                else:
                    tasks.addTask(self.task['payload'])
                break

    def isWorker_online(self):
        self.wfile.write(json.dumps({'op' : 'ping'}) + '\n')
        answer = json.loads(self.rfile.read())
        if answer['result'] == u'pong':
            return True

    def getTask(self):
        self.task['event'].acquire()
        return self.task['payload']

    def finishTask(self, result):
        self.task['busy'] = False
        if self.task.has_key('callback'):
            self.task['callback'](result)

    def setupWorker(self):
        self.task = tasks.createWorker()


def startServer():
    try:
        server = SocketServer.TCPServer(('localhost', 5555), SocketHandler)
        server.serve_forever()
    except socket.error, e:
        if e.errno == 10048:
            print 'Server allready running'
        else:
            raise

def printIt(arg):
    print "Worker returned", arg

server_thread = threading.Thread(target=startServer)
server_thread.start()
tasks.addTask('print "Task processed!"', printIt)
server_thread.join()
print 'Server thread stoped'
