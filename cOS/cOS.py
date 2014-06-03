#-----------------------------------------------------------------------------
# ieOS.py
# By Grant Miller (blented@gmail.com)
# v 1.00
# Created On: 02/06/2012
# Modified On: 02/06/2012
# tested using Nuke X 6.3v4 & 3dsMax 2012
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Required Files:
# ieCommon, ieGlobals
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Description:
# Various file system helper functions
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Revision History:
#
# v 1.00 Initial version
#
#-----------------------------------------------------------------------------

import os
import time
import sys
import subprocess
import glob
import shutil
from distutils import dir_util
import re

# ieGlobals
#-----------------------------------------------------------------------------
import arkInit
arkInit.init()
import ieGlobals
import ieCommon
try:
	import psutil
except:
	pass


def setEnvironmentVariable(key, val):
	val = str(val)
	os.environ[key] = val
	return os.system('setx %s "%s"' % (key, val))

def fileExtension(filename):
	return os.path.splitext(filename)[1][1:].lower()

def mkdir(dirname):
	if not os.path.isdir(dirname):
		os.mkdir(dirname)

def getVersion(filename):
	match = re.findall('[vV]([0-9]+)', filename)
	if (match):
		return int(match[-1])
	return 0

# fix: currently increments all versions, should it?
def incrementVersion(filename):
	version = getVersion(filename) + 1
	return re.sub('[vV][0-9]+', 'v%03d' % version, filename)

def getDir(filename):
	return os.path.dirname(filename) + '/'

def checkTempDir():
	if not os.path.exists(ieGlobals.IETEMP):
		os.makedirs(ieGlobals.IETEMP)

def getParentPID():
	return psutil.Process(os.getpid()).ppid

def getFrameRange(file):
	baseInFile, ext = os.path.splitext(file)
	# fix: this is done terribly, should be far more generic
	percentLoc = baseInFile.find('%')

	if percentLoc == -1:
		raise Exception('Frame padding not found in: ' + file)

	# second character after the %
	# ex: %04d returns 4
	padding = int(baseInFile[percentLoc + 2])

	minFrame = 9999999
	maxFrame = -9999999
	for f in glob.iglob(baseInFile[0:percentLoc] + '*'):
		frame = f[percentLoc:(percentLoc + padding)]
		if frame.isdigit():
			frame = int(frame)
			maxFrame = max(maxFrame,frame)
			minFrame = min(minFrame,frame)

	return {'min': minFrame,
			'max': maxFrame,
			'base': baseInFile,
			'ext': ext}

def killJobProcesses(nodesOnly=True):
	"""Ruthlessly kills off all other processes on the render node"""
	if not psutil:
		print 'No psutil module found'
	if not nodesOnly or 'RENDER' in os.environ['COMPUTERNAME']:
		currentProcess = os.getpid()
		processParent = getParentPID()
		for p in psutil.process_iter():
			try:
				if '3dsmax' in p.name or \
					'Nuke' in p.name or \
					'ffmpeg' in p.name or \
					('cmd.exe' in p.name and p.pid != processParent) or \
					('python.exe' in p.name and p.pid != currentProcess) or \
					'maxwell' in p.name:
					print 'Terminating %s' % p.name
					p.terminate()
			except:
				pass

# Creates a glob of files then removes them
def emptyFolder(folder,onlyFiles=False, waitTime=5):
	if onlyFiles:
		print 'Deleting all files in: %s' % folder
	else:
		print 'Deleting all files and folders in: %s' % folder

	startTime = time.time()
	for root, dirs, files in os.walk(folder):
		if (time.time() > startTime + waitTime):
			break
		for f in files:
			if (time.time() > startTime + waitTime):
				break
			try:
				os.unlink(os.path.join(root, f))
			except:
				pass
		if not onlyFiles:
			for d in dirs:
				if (time.time() > startTime + waitTime):
					break
				try:
					shutil.rmtree(os.path.join(root, d))
				except:
					pass

def pathInfo(path):
	pathInfo = {}
	path = path.replace('\\','/')
	pathParts = path.split('/')
	pathInfo['dirname'] = '/'.join(pathParts[:-1]) + '/'
	pathInfo['basename'] = pathParts[-1]
	pathInfo['extension'] = pathParts[-1].split('.')[-1].strip().lower()
	pathInfo['filename'] = path
	pathInfo['filebase'] = '.'.join(pathParts[-1].split('.')[:-1])

	return pathInfo

def makeDirs(path):
	dirName = pathInfo(path)['dirname']
	try:
		os.makedirs(dirName)
	except Exception as err:
		return err

def stripExtension(path):
	if 'str' in ieCommon.varType(path):
		return '.'.join(path.split('.')[:-1])
	return path

def filePrep(path):
	return ieCommon.defaultStringReplace(path).replace('\\','/')


def unixPath(path):
	"""changes backslashes to forward slashes.
	also removes any successive slashes, ex: \\ or \/"""
	return re.sub(r'[\\/]+', '/', path)

def universalPath(path):
	"""swaps Q:/ with $root/
		intent is that paths are translated on Windows, Mac, and Linux"""
	# fix: should get the root drive from somewhere, case insensitive regex
	path = path.lower()
	return re.sub('[Qq]:/',ieGlobals.UNIVERSAL_ROOT, unixPath(path))

def osPath(path):
	"""swaps $root/ with Q:/
		intent is that paths are translated on Windows, Mac, and Linux"""
	# fix: should get the root drive from somewhere, case insensitive regex
	return path.replace(ieGlobals.UNIVERSAL_ROOT, ieGlobals.ROOT)

# fix: implement
# def join():
# 	pass


def normalizeDir(path):
	path = unixPath(path)
	if path[-1] != '/':
		path = path + '/'
	return path

def copyTree(src, dst, symlinks=False, ignore=None):
	# for item in os.listdir(src):
	# 	s = os.path.join(src, item)
	# 	d = os.path.join(dst, item)
	# 	if os.path.isdir(s):
	# 		shutil.copytree(s, d, symlinks, ignore)
	# 	else:
	# 		shutil.copy2(s, d)
	dir_util.copy_tree(src, dst)
	# srcFiles = src + '/*'
	# for filename in glob.glob(srcFiles):
	#     if os.path.isdir(filename):
	#         copyTree()
	#     try:
	#         shutil.copy2(filename,filename.replace(src,dst))
	#         if verbose:
	#             print 'Copied %s to %s' % (filename,dst)
	#     except:
	#         if verbose:
	#             print 'Could not copy %s to %s' % (filename,dst)

def duplicateDir(src, dest):
	"""Duplicates a directory, copying files that don't already exist
 and deleting files not present in src"""
	src = normalizeDir(src)
	dest = normalizeDir(dest)

	for root, dirs, files in os.walk(src):
		for n in dirs:
			srcFolder = root + '/' + n
			print 'dir:', srcFolder
			destFolder = srcFolder.replace(src, dest)
			if not os.path.isdir(destFolder):
				try:
					os.makedirs(destFolder)
					print 'mkdir:', destFolder
				except Exception as err:
					print err
					print 'Could not mkdir: ', destFolder

		for n in files:
			srcFilename = root + '/' + n
			print 'file:', srcFilename
			destFilename = srcFilename.replace(src, dest)
			if not os.path.isfile(destFilename):
				try:
					print 'copy:', srcFilename
					shutil.copy(srcFilename, destFilename)
				except Exception as err:
					print err
					print 'Could not copy: ', srcFilename
			else:
				print 'exists:', srcFilename

	# fix: should delete old crap
	# for root, dirs, files in os.walk(src):
	# 	for n in dirs:
	# 		folder = src + root + n
	# 		if not os.path.isdir(folder):
	# 			print 'delete folder:', dest + root + n
	# 		# 	os.makedirsfolder

	# 	for n in files:
	# 		filename = src + root + '/' + n
	# 		if not os.path.isdir(folder):
	# 			print 'delete:', dest + root + '/' + n
	# 		# 	shutil.copy(src + root + n, filename)

def runPython(pythonFile):
	return os.system(ieGlobals.IEPYTHON + ' ' + pythonFile)

def startSubprocess(processArgs,env=None):
	"""Runs a program through psutil.Popen, disabling Windows error dialogs"""

	if env:
		env = dict(os.environ.items() + env.items())
	else:
		env = os.environ

	# for arg in processArgs:
	# 	print arg

	if sys.platform.startswith('win'):
		# Don't display the Windows GPF dialog if the invoked program dies.
		# See comp.os.ms-windows.programmer.win32
		# How to suppress crash notification dialog?, Jan 14,2004 -
		# Raymond Chen's response [1]
		import ctypes, _winreg

		SEM_NOGPFAULTERRORBOX = 0x0002 # From MSDN
		ctypes.windll.kernel32.SetErrorMode(SEM_NOGPFAULTERRORBOX);

		# if creationFlags != None:
		#     subprocess_flags = creationFlags
		# else:
		#     subprocess_flags = 0x8000000 # hex constant equivalent to win32con.CREATE_NO_WINDOW

		keyVal = r'SOFTWARE\Microsoft\Windows\Windows Error Reporting'
		try:
			key = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, keyVal, 0, ieGlobals.KEY_ALL_ACCESS)
		except:
			key = _winreg.CreateKey(_winreg.HKEY_LOCAL_MACHINE, keyVal)
		# 1 (True) is the value
		_winreg.SetValueEx(key, 'ForceQueue', 0, _winreg.REG_DWORD, 1)
	# else:
	#     subprocess_flags = 0

	# fix: use this everywhere
	command = ''
	if ieCommon.varType(processArgs) == 'list':
		command = '"' + processArgs[0] + '" '
		for i in range(1, len(processArgs)):
			processArgs[i] = str(processArgs[i])
			command += str(processArgs[i]) + ' '
		print 'command:\n', command
	else:
		print 'command:\n', processArgs

	# return subprocess.Popen(processArgs,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env)
	return psutil.Popen(processArgs,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,env=env)

def getConvertFile(outFile):
	pi = pathInfo(outFile)
	return pi['dirname'] + pi['filebase'] + '_convert.nk'

def genArgs(argData):
	args = ''
	for k,v in argData.iteritems():
		args += '-%s %s ' % (k,v)
	return args[:-1]

def updateTools(toolsDir=None):
	if not toolsDir:
		toolsDir = ieGlobals.IETOOLS

	# if the tools haven't been installed to the root, copy them now
	try:
		import git
	except:
		git = None

	if git:
		try:
			print '\nTools installed: %s, updating with git python' % toolsDir
			repo = git.Repo(toolsDir)
			print repo.git.pull()
			return True
		except Exception as err:
			print '\nError updating tools with git python: ', err
	if os.path.isdir(toolsDir + '.git'):
		print '\nTools installed: %s, updating with git command line' % toolsDir
		os.system(toolsDir.split(':')[0] + ': && \
					cd ' + toolsDir + ' && ' +
					'"' + ieGlobals.GIT_EXE + '"' + ' pull')
		return True

	return False