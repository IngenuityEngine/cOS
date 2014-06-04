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

import ieInit
ieInit.init()
import ieGlobals
import ieCommon
try:
	import psutil
except:
	pass

'''
	Method: setEnvironmentVariable

	Sets a given environment variable for the OS.

	Parameters:
		key - environment variable
		val - value for the environment variable
'''
def setEnvironmentVariable(key, val):
	val = str(val)
	os.environ[key] = val
	return os.system('setx %s "%s"' % (key, val))

'''
	Method: fileExtention

	Returns file extension of a file (without the '.').
'''
def fileExtension(filename):
	return os.path.splitext(filename)[1][1:].lower()

'''
	Method: mkdir

	Wrapper for os.mkdir.
'''
def mkdir(dirname):
	if not os.path.isdir(dirname):
		os.mkdir(dirname)

'''
	Method: getVersion

	Returns version number of a given filename.
'''
def getVersion(filename):
	match = re.findall('[vV]([0-9]+)', filename)
	if (match):
		return int(match[-1])
	return 0

# fix: currently increments all versions, should it?
'''
	Method: incrementVersion

	Returns file with version incremented in all locations in the name.
'''
def incrementVersion(filename):
	version = getVersion(filename) + 1
	return re.sub('[vV][0-9]+', 'v%03d' % version, filename)

'''
	Method: getDir

	Returns directory name of a file with a trailing '/'.
'''
def getDir(filename):
	return os.path.dirname(filename) + '/'

'''
	Method: checkTempDir

	Checks if ieGlobals.IETEMP exists, and if not, creates it.
'''
def checkTempDir():
	if not os.path.exists(ieGlobals.IETEMP):
		os.makedirs(ieGlobals.IETEMP)

'''
	Method: getParentPID

	Returns the process ID of the parent process.
'''
def getParentPID():
	return psutil.Process(os.getpid()).ppid

'''
	Method: getFrameRange

	Returns a dictionary with 'min' (minFrame), 'max' (maxFrame), 'base' (fileName), and 'ext' (ext).

	Parameters:
		file - Generic file in sequence. Ex. text/frame.%04d.exr
'''
def getFrameRange(path):
	baseInFile, ext = os.path.splitext(path)
	# fix: this is done terribly, should be far more generic
	percentLoc = baseInFile.find('%')

	if percentLoc == -1:
		raise Exception('Frame padding not found in: ' + path)

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


'''
	Method: killJobProcesses

	Kills all other processes currently on the render node.
'''
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
'''
	Method: emptyFolder

	Removes all files and folders from a directory.

	Parameters:
		folder - directory from which to delete
		onlyFiles - False by default, if only files should be deleted
		waitTime - 5 by default, how many seconds to wait.
'''
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

'''
	Method: pathInfo

	Returns a dictionary of the path's dirname, basename, extension, filename and filebase.
'''
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

'''
	Method: makeDirs

	Wrapper for os.makedirs.
'''
def makeDirs(path):
	dirName = pathInfo(path)['dirname']
	try:
		os.makedirs(dirName)
	except Exception as err:
		return err

'''
	Method: stripExtension

	Removes the extension from a path.  If there is no extension, returns ''
'''
def stripExtension(path):
	if '.' in path:
		return '.'.join(path.split('.')[:-1])
	return path

'''
	Method: filePrep

	Replaces backslashes with forward slashes in path names.
'''
def filePrep(path):
	return ieCommon.defaultStringReplace(path).replace('\\','/')

'''
	Method: unixPath

	Changes backslashes to forward slashes and removes successive slashes, ex \\ or \/

'''
def unixPath(path):
	"""changes backslashes to forward slashes.
	also removes any successive slashes, ex: \\ or \/"""
	return re.sub(r'[\\/]+', '/', path)

'''
	Method: universalPath

	Swaps Universal Root (Q:/) with unix root ($root).
'''
def universalPath(path):
	"""swaps Q:/ with $root/
		intent is that paths are translated on Windows, Mac, and Linux"""
	# fix: should get the root drive from somewhere, case insensitive regex
	path = path.lower()
	return re.sub('[Qq]:/',ieGlobals.UNIVERSAL_ROOT, unixPath(path))

'''
	Method: osPath

	Swaps unix root ($root) with Universal Root (Q:/)
'''
def osPath(path):
	"""swaps $root/ with Q:/
		intent is that paths are translated on Windows, Mac, and Linux"""
	# fix: should get the root drive from somewhere, case insensitive regex
	return path.replace(ieGlobals.UNIVERSAL_ROOT, ieGlobals.ROOT)

# fix: implement
# def join():
# 	pass

'''
	Method: normalizeDir

	Appends a / to the end of a path if it's not there yet.
'''
def normalizeDir(path):
	path = unixPath(path)
	if path[-1] != '/':
		path = path + '/'
	return path

'''
	Method: copyTree

	Copies the src directory tree to the destination.
'''
def copyTree(src, dst, symlinks=False, ignore=None):
	dir_util.copy_tree(src, dst)

'''
	Method: duplicateDir

	Duplicates a directory, copying files that don't already exist.
'''
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

'''
	Method: runPython

	Executes a given python file.
'''
def runPython(pythonFile):
	return os.system(ieGlobals.IEPYTHON + ' ' + pythonFile)

'''
	Method: startSubprocess

	Executes a program using psutil.Popen, disabling Windows error dialogues.
'''
def startSubprocess(processArgs,env=None):
	"""Runs a program through psutil.Popen, disabling Windows error dialogs"""

	if env:
		env = dict(os.environ.items() + env.items())
	else:
		env = os.environ

	if sys.platform.startswith('win'):
		# Don't display the Windows GPF dialog if the invoked program dies.
		# See comp.os.ms-windows.programmer.win32
		# How to suppress crash notification dialog?, Jan 14,2004 -
		# Raymond Chen's response [1]
		import ctypes, _winreg

		SEM_NOGPFAULTERRORBOX = 0x0002 # From MSDN
		ctypes.windll.kernel32.SetErrorMode(SEM_NOGPFAULTERRORBOX);

		keyVal = r'SOFTWARE\Microsoft\Windows\Windows Error Reporting'
		try:
			key = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, keyVal, 0, ieGlobals.KEY_ALL_ACCESS)
		except:
			key = _winreg.CreateKey(_winreg.HKEY_LOCAL_MACHINE, keyVal)
		# 1 (True) is the value
		_winreg.SetValueEx(key, 'ForceQueue', 0, _winreg.REG_DWORD, 1)

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

	return psutil.Popen(processArgs,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,env=env)

'''
	Method: getConvertFile

	Creates convert file by removing file extension, and appending '_convert.nk'.
'''
def getConvertFile(outFile):
	pi = pathInfo(outFile)
	return pi['dirname'] + pi['filebase'] + '_convert.nk'

'''
	Method: getArgs

	Generates a string of flag arguments from an iterable of tuples k, v tuples.
	Arguments are of the form -k1 v1 -k2 v2...etc.
'''
def genArgs(argData):
	args = ''
	for k,v in argData.iteritems():
		args += '-%s %s ' % (k,v)
	return args[:-1]

'''
	Method: updateTools

	Updates tools from the git repo if available.
'''
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