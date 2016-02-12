import threading
import time
import os
import signal
import sys
import Queue

file2tail = 'none'

class RotateWatchThread(threading.Thread):

    def __init__(self):
        super(RotateWatchThread, self).__init__()

    def run(self):
        time.sleep(0.1)
        thequeue.put("RotateWatchThread: Starting..")
        self._stop = threading.Event()
        try:
            (mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime) = os.stat(file2tail)
            previous_inode = "%s" % (ino)
        except:
            thequeue.put("RotateWatchThread: ERROR: Could not load file: "+file2tail)
            sys.exit(1)
        while not self.stopped():
            time.sleep(5)
            try:
                (mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime) = os.stat(file2tail)
                current_inode = "%s" % (ino)
            except:
                thequeue.put("RotateWatchThread: File removed?")
                current_inode = previous_inode


            if previous_inode != current_inode:

                thequeue.put("RotateWatchThread: File was rotated!")
                self.TailThread.stop()
                time.sleep(2)
                self.TailThread.start()
                previous_inode = current_inode

    def stop(self):
        thequeue.put("RotateWatchThread: Stopping..")
        self._stop.set()

    def stopped(self):
        return self._stop.isSet()

    def load_tail(self, TailThread):
        self.TailThread = TailThread
        time.sleep(0.1)
        thequeue.put("RotateWatchThread: Loaded TailFileThread")


class TailFileThread(threading.Thread):

    def __init__(self):
        super(TailFileThread, self).__init__()  

    def run(self):
        thequeue.put("TailFileThread: Starting..")
        self._stop = threading.Event()

        fileopen = False

        try:
            thefile = open(file2tail)
            fileopen = True
        except:
            thequeue.put("TailFileThread: ERROR: Could not open file: "+file2tail)
            self.stop()

        if fileopen:
            thefile.seek(0,2)      # Go to the end of the file
            while True:
                line = thefile.readline()
                if not line:
                    if self.stopped():
                        thequeue.put("TailFileThread: Breaking TailFile..")
                        break
                    time.sleep(0.05)    # Sleep briefly
                    continue
                self.parse(line.split('\n')[0])

        threading.Thread.__init__(self)

    def stop(self):
        thequeue.put("TailFileThread: Stopping..")
        self._stop.set()

    def stopped(self):
        return self._stop.isSet()

    def trigger_function(self, custom_func):
        self.parse = custom_func

class InterruptWatch():

    def __init__(self, a, b):
        self.a = a
        self.b = b

    def signal_handler(self, signal, frame):
        thequeue.put('InterruptWatch: You pressed Ctrl+C, stopping threads..')
        self.a.stop()
        self.b.stop()
        time.sleep(2)
        safeprint.stop()
        

    def start(self):
        signal.signal(signal.SIGINT, self.signal_handler)
        thequeue.put('InterruptWatch: Starting..')

        signal.pause()




thequeue = Queue.Queue('derp')


class SafePrintThread(threading.Thread):

    def __init__(self):
        super(SafePrintThread, self).__init__()  

    def run(self):
        print "SafePrintThread: Starting.."
        self._stop = threading.Event()
        
        while True:
            if self.stopped():
                print "SafePrintThread: Breaking PrintQueue.."
                time.sleep(1)
                break
            
            try:
                value = thequeue.get(True, 1)
            except:
                continue

            thequeue.task_done()

            print value


    def stop(self):
        thequeue.put("SafePrintThread: Stopping..")
        self._stop.set()

    def stopped(self):
        return self._stop.isSet()

#Instance Thread TailFile
safeprint = SafePrintThread()

#Start both threads
safeprint.start()


