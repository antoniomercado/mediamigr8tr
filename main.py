#!/usr/bin/env python3
#encoding: UTF-8
import logging
from multiprocessing import Pipe
from multiprocessing import Process
import os
import time

_DEFAULT_LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
_LOGGER = logging.getLogger(__name__)

# change this file name
FileName = 'stream.txt'

# adapted from http://www.valuedlessons.com/2008/04/events-in-python.html


# the Event class take care of adding, removing and executing the functions
class Event:
	def __init__(self):
		self.handlers = set()
	def handle(self, handler):
		self.handlers.add(handler)
		return self
	
	def unhandle(self, handler):
		try:
			self.handlers.remove(handler)
		except:
			raise ValueError("Handler is not handling this event, so cannot unhandle it.")
		return self
	
	def fire(self, * args, ** kargs):
		for handler in self.handlers:
			handler(*args, ** kargs)
	
	def getHandlerCount(self):
		return len(self.handlers)
	
	__iadd__ = handle
	__isub__ = unhandle
	__call__ = fire
	__len__  = getHandlerCount
  
# the stream class takes care of the
# function to fire in case of an event
class Stream:
	def __init__(self, fname):
		self.fname = fname
		self.fd = open(fname, 'r')
		self.get_stream()
	def get_stream(self):
		# this is the actual function to fire
		print (self.fd.read())
	def restart(self):
		self.fd.seek(0)
  
# the MockFileWatcher creats the multiprocessing deamon to alert on file change
class MockFileWatcher:
	def __init__(self, source_path, sleeptime=0.1):
		self.fileChanged = Event()
		self.source_path = source_path
		self.running = False
		self.deamon = False
		self.fd = None
		self.sleep = sleeptime
        # the next two lines can be set outside the class
		self.stream = Stream(source_path)
		self.fileChanged += self.stream.get_stream # add event handler
		def watchFiles(self):
			# open the file in non-blocking read mode
			self.fd = os.open(self.source_path, os.O_RDONLY | os.O_NONBLOCK)
        # go to the end
		os.lseek(self.fd, 0, 2)
		self.running = True
		self.deamon = False
#while self.running:
	# try to read
	#if	os.read(self.fd, 1) != '':
		# New data was added
		#os.lseek(self.fd, 0, 2) # go to the end of file
		#self.fileChanged() # fire the event
	# see if the parent process has a message
	#if self.chiled_conn.poll():
	#	# execute the message
	#	eval(self.chiled_conn.recv())
	# sleep for a while
	#time.sleep(self.sleep)
	def watchFilesDeamon(self):
        # start the deamon
		self.parent_conn, self.chiled_conn = Pipe()
		p = Process(target=self.watchFiles)
		p.start()
		self.p = p
		self.deamon = True
		return p
	def stop(self):
        # stop deamon/process
		if self.deamon:
			self.parent_conn.send('self.stop()')
			print ("Hold while stopping child process...")
			# hold depends on the sleeping time
			if self.parent_conn.recv():
				pass
				#print "chiled is stopped"
			self.p.terminate() # terminate multiprocessing
			self.deamon = False
        # stop process
		self.running = False
		self.fd = None
        # if this is the process make sure parent know we are done
		if not self.deamon:  self.chiled_conn.send(True)       
		return True

def _configure_logging():
    _LOGGER.setLevel(logging.DEBUG)

    ch = logging.StreamHandler()

    formatter = logging.Formatter(_DEFAULT_LOG_FORMAT)
    ch.setFormatter(formatter)

    _LOGGER.addHandler(ch)
	
def main():
	_configure_logging()
	pass

if __name__ == "__main__":
    main()