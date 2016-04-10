#!/usr/bin/env python3
#encoding: UTF-8
import pyinotify
import os
import magic
import re
import shutil
import time
import sys
import datetime
import subprocess
import copy
import json
from guessit import guessit


configDir = str(sys.argv[1])
if (os.path.isdir(configDir) == False):
	print("Error, could not find configuration directory [" + configDir + "]")
	sys.exit(0)

with open(configDir + "/config.json", "rt") as in_file:
    text = in_file.read()
	
config = json.loads(text)
wm = pyinotify.WatchManager()
wdd = {}
notifier = {}
mask = pyinotify.IN_CREATE  | pyinotify.IN_MOVED_TO # watched events
SOURCE_DIR = config.get("source_dir");
TARGET_MOVIE_DIR = config.get("movie_dir")
TARGET_TV_SHOW_DIR = config.get("tv_show_dir")

class EventHandler(pyinotify.ProcessEvent):
	
	def is_video(self,x):
		return {
			b'video/x-msvideo': True,
			b'video/mp4': True,
			b'video/ogg': True,
			b'video/x-matroska': True,
		}.get(x, False)
		
	def is_valid_video_length(self, filename):
		result = subprocess.Popen(["ffprobe", filename], stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
		line = result.stdout.readlines()
		match = re.search("Duration:\s?(([0-9]{2}):([0-9]{2}):([0-9]{2})\.([0-9]{2})),",str(line), re.IGNORECASE)
		if (match is None):
			return False
		else:
			hours = int(match.group(2))
			minutes = int(match.group(3))
			seconds = int(match.group(4))
			miliseconds = int(match.group(5))
			return minutes > 10
	
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
			targetPathName = realMoviePath + "00-99"
			shutil.move(pathName, targetPathName + "/" + srcFileName)
		print('Timestamp: {:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now()) + " File Moved To:", targetPathName + "/" + srcFileName)
	
	def move_tv_show(self, srcPathName, srcFileName, targetFolderName, season):
		realShowPath = os.path.expanduser(TARGET_TV_SHOW_DIR)
		seasonFolderName = ""
		if (season < 9):
			seasonFolderName = "0" + str(season)
		targetPath = realShowPath + targetFolderName + "/Season " + seasonFolderName;
		if (os.path.isdir(targetPath) == False):
			os.makedirs(targetPath)
		shutil.move(srcPathName, targetPath + "/" + srcFileName)
		print('Timestamp: {:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now()) + " File Moved To:", targetPath + "/" + srcFileName)
		
	def move_file(self, event):
		if (event.dir == False and event.name.lower().find("sample") == -1 
			and self.is_video(magic.from_file(event.pathname, mime=True)) == True 
			and self.is_valid_video_length(event.pathname)):
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
					print ('Timestamp: {:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now()) + " Ignoring video file, could not detect type.")
		else:
			print('Timestamp: {:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now()) + " Traversing path", event.pathname)
			if os.path.isdir(event.pathname):
				for i in os.listdir(event.pathname):
					newPathName = event.pathname + "/" + i
					if os.path.isfile(newPathName): 
						print('Timestamp: {:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now()) + " File detected", newPathName)
						newEvent = copy.copy(event);
						newEvent.dir = False
						newEvent.name = i
						newEvent.pathname = newPathName
						self.move_file(newEvent)
					elif(os.path.isdir(newPathName)):
						print('Timestamp: {:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now()) + " Directory detected", newPathName)
						newEvent = copy.copy(event);
						newEvent.dir = True
						newEvent.name = i
						newEvent.pathname = newPathName
						self.move_file(newEvent)
					else:
						print('Timestamp: {:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now()) +  " Error could not detect file type", newPathName)
			else:
				print('Timestamp: {:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now()) + " Ignoring file ", event.pathname, "not valid")		
				
	def process_IN_CREATE(self, event):
		print ('Timestamp: {:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now()) + " Incoming Source File (Create):", event.pathname)
		time.sleep(1) # Ghetto way of waiting for bufffers to close for cp or other piping mechanism
		self.move_file(event)
		
	def process_IN_MOVED_TO(self, event):
		print('Timestamp: {:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now()) + " Incoming Source File (Move):", event.pathname)
		self.move_file(event)

def on_loop(notifier):
	print('Timestamp: {:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now()) + " End event loop")
	pass

def signal_handler(signal, frame):
	wm.rm_watch(os.path.expanduser(SOURCE_DIR), rec=True)
	print("Notifier", notifier)
	notifier.stop()
	sys.exit(0)
		
def main():
	pidDir = "/var/run/";
	logDir = "/var/log/"
	name = "mediamigr8tr"
	
	notifier = pyinotify.Notifier(wm, EventHandler())
	wdd = wm.add_watch(os.path.expanduser(SOURCE_DIR), mask, rec=True)
#	signal.signal(signal.SIGINT, signal_handler)
#	signal.signal(signal.SIGTERM, signal_handler)

	try:
		print('Timestamp: {:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now()) + " Starting Daemon")
		notifier.loop(daemonize=False, callback=on_loop, 
			pid_file=pidDir + name + ".pid", stdout=logDir + name + ".log")
	except pyinotify.NotifierError as err:
		print('Timestamp: {:%Y-%m-%d %H:%M:%S}' + " Error:", err)
		sys.exit(1)

if __name__ == "__main__":
    main()