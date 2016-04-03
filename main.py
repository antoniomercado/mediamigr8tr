#!/usr/bin/env python3
#encoding: UTF-8
import pyinotify
import os
import magic
import re
import shutil
import time
import signal
import sys
from guessit import guessit

wm = pyinotify.WatchManager()
mask = pyinotify.IN_CREATE  | pyinotify.IN_MOVED_TO # watched events
SOURCE_DIR = '/home/tony/completed';
TARGET_MOVIE_DIR = '/home/tony/media/Movies/';
TARGET_TV_SHOW_DIR = '/home/tony/media/TV Shows/';

class EventHandler(pyinotify.ProcessEvent):
	def is_video(self,x):
		return {
			b'video/x-msvideo': True,
			b'video/mp4': True,
			b'video/ogg': True,
			b'video/x-matroska': True,
		}.get(x, False)
		
	def move_movie(self, firstLetter, pathName, srcFileName):
		realMoviePath = os.path.expanduser(TARGET_MOVIE_DIR)
		if (firstLetter.isdigit() == False):
			targetPathName = realMoviePath + firstLetter.upper()
			if (os.path.isdir(targetPathName) == True):
				shutil.move(pathName, targetPathName + "/" + srcFileName)
			elif (os.path.isdir(realMoviePath + firstLetter.lower()) == True):
				targetPathName = realMoviePath + firstLetter.lower()
				shutil.move(pathName, targetPathName + "/" + srcFileName)
			else:
				os.makedirs(targetPathName)
				shutil.move(pathName, targetPathName + "/" + srcFileName)
		else:
			if(os.path.isdir(realMoviePath + "00-99") == False):
				os.makedirs(realMoviePath + "00-99")
			targetPath = realMoviePath + "00-99"
			shutil.move(pathName, targetPath + "/" + srcFileName)
		print("File Moved To:", targetPath + "/" + srcFileName)
	
	def move_tv_show(self, srcPathName, srcFileName, targetFolderName, season):
		realShowPath = os.path.expanduser(TARGET_TV_SHOW_DIR)
		seasonFolderName = ""
		if (season < 9):
			seasonFolderName = "0" + str(season)
		targetPath = realShowPath + targetFolderName + "/Season " + seasonFolderName;
		if (os.path.isdir(targetPath) == False):
			os.makedirs(targetPath)
		shutil.move(srcPathName, targetPath + "/" + srcFileName)
		print("File Moved To:", targetPath + "/" + srcFileName)
		
	def move_file(self, event):
		if (event.dir == False and event.name.lower().find("sample") == -1 
			and self.is_video(magic.from_file(event.pathname, mime=True)) == True):
				match = guessit(event.name);
				print(match)
				if (match.get("type") == 'movie'):
					prefixMatch = re.search("^((The|A|An)\s)",match.get("title"), re.IGNORECASE)
					if (prefixMatch is not None):
						title = match.get("title").replace(prefixMatch.group(1),"")
						firstLetter = title[0];
					else:
						firstLetter = match.get('title')[0];
					self.move_movie(firstLetter, event.pathname, event.name)
				elif (match.get("type") == 'episode'):
					titlePieces = match.get("title").split()
					newTitle = ""
					for i,piece in enumerate(titlePieces):
						if (i > 0):
							newTitle += " "
						newTitle += piece[0].upper() + piece[1:]
					self.move_tv_show(event.pathname, event.name, newTitle, match.get("season"))
				else:
					print ("Ignoring video file, could not detect type.")
				
	def process_IN_CREATE(self, event):
		print ("Incoming Source File (Create):", event.pathname)
		time.sleep(1) # Ghetto way of waiting for bufffers to close for cp or other piping mechanism
		self.move_file(event)
		
	def process_IN_MOVED_TO(self, event):
		print("Incoming Source File (Move):", event.pathname)
		self.move_file(event)

def on_loop(notifier):
	pass

def signal_handler(signal, frame):
	wm.rm_watch(wdd[os.path.expanduser(SOURCE_DIR)], rec=True)
	notifier.stop()
	sys.exit(0)
		
def main():
	pidDir = "/var/run/";
	logDir = "/var/log/"
	name = "mediamigr8tr"
	
	notifier = pyinotify.Notifier(wm, EventHandler())
	wdd = wm.add_watch(os.path.expanduser(SOURCE_DIR), mask, rec=True)
	signal.signal(signal.SIGINT, signal_handler)
	signal.signal(signal.SIGTERM, signal_handler)

	try:
		print("Starting Daemon")
		notifier.loop(daemonize=True, callback=on_loop, 
			pid_file=pidDir + name + ".pid", stdout=logDir + name + ".log")
	except pyinotify.NotifierError as err:
		print("error here")
		print >> sys.stderr, err.args
		sys.exit(1)

if __name__ == "__main__":
    main()