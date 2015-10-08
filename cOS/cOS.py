#-----------------------------------------------------------------------------
# ieOS.py
# By Grant Miller (blented@gmail.com)
# v 1.00
# Created On: 2012/02/06
# Modified On: 2014/05/20
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Required Files:
# ieCommon, globalSettings
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Description:
# Various file system helper functions
#-----------------------------------------------------------------------------

import os
import time
import sys
import subprocess
import glob
import shutil
from distutils import dir_util
import types
import re

# globalSettings
#-----------------------------------------------------------------------------

import arkInit
arkInit.init()
import settingsManager
globalSettings = settingsManager.globalSettings()
# import ieCommon
import arkUtil
try:
	import psutil
except:
	pass


##################### Normalization Operations #######################

'''
	Method: ensureEndingSlash

	Appends a / to the end of a path if it's not there yet.
'''
def ensureEndingSlash(path):
	path = unixPath(path)
	if path[-1] != '/':
		path = path + '/'
	return path

'''
	Method: removeStartingSlash

	Removes backslashes and forward slashes from the beginning of directory names.
'''
def removeStartingSlash(path):
	if (path[0] == '\\' or path[0] == '/'):
		path = path[1:]
	return path

'''
	Method: filePrep

	Replaces backslashes with forward slashes in path names.
'''
def filePrep(path):
	return arkUtil.defaultStringReplace(path).replace('\\','/')

'''
	Method: normalizeDir

	Dirs always use forward slashses, don't have a leading slash, and have a trailing slash.
'''
def normalizeDir(path):
	path = filePrep(path)
	path = removeStartingSlash(path)
	return ensureEndingSlash(path)

'''
	Method: normalizePath

	Removes starting slash, and replaces all backslashes with forward slashses.
'''
def normalizePath(path):
	path = removeStartingSlash(path)
	return filePrep(path)

'''
	Method: unixPath

	Changes backslashes to forward slashes and removes successive slashes, ex \\ or \/
'''
def unixPath(path):
	"""changes backslashes to forward slashes.
	also removes any successive slashes, ex: \\ or \/"""
	url = path.split('://')
	if len(url) > 1:
		return url[0] + '://' + re.sub(r'[\\/]+', '/', url[1])
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
	return re.sub('[Qq]:/',globalSettings.UNIVERSAL_ROOT, unixPath(path))

'''
	Method: osPath

	Swaps unix root ($root) with Universal Root (Q:/)
'''
def osPath(path):
	"""swaps $root/ with Q:/
		intent is that paths are translated on Windows, Mac, and Linux"""
	# fix: should get the root drive from somewhere, case insensitive regex
	return path.replace(globalSettings.UNIVERSAL_ROOT, globalSettings.ROOT)

'''
	Method: unicodeDictToString
	Converts the output of a json.loads operation (returning unicode encoding)
	to byte strings.
'''
def unicodeToString(partialJSON):
	inputType = type(partialJSON)
	if isinstance(partialJSON, types.StringTypes):
		return str(partialJSON)
	elif inputType == types.ListType:
		return [unicodeToString(x) for x in partialJSON]
	elif inputType == types.DictType:
		# uncomment in Sublime 3
		# return {unicodeToString(x): unicodeToString(partialJSON[x]) for x in partialJSON}
		return dict([(unicodeToString(x), unicodeToString(partialJSON[x])) for x in partialJSON])
	else:
		return partialJSON


###################### Extension Operations ##########################

'''
	Method: normalizeExtension

	Takes in an extension, and makes is lowercase, and precedes it with a '.'
'''
def normalizeExtension(ext):
	ext = ext.lower()
	if (ext[0] != '.'): return '.' + ext
	return ext

'''
	Method: stripExtension

	Removes the extension from a path.  If there is no extension, returns ''
'''
def stripExtension(path):
	if '.' in path:
		return '.'.join(path.split('.')[:-1])
	return path

'''
	Method: fileExtention

	Returns file extension of a file (without the '.').
'''
def fileExtension(filename):
	return os.path.splitext(filename)[1][1:].lower()

'''
	Method: getConvertFile

	Creates convert file by removing file extension, and appending '_convert.nk'.
'''
def getConvertFile(outFile):
	pi = getFileInfo(outFile)
	return pi['dirname'] + pi['filebase'] + '_convert.nk'


#################### Versioning Operations ######################

# fix: currently increments all versions, should it?
'''
	Method: incrementVersion

	Returns file with version incremented in all locations in the name.
'''
def incrementVersion(filename):
	version = getVersion(filename) + 1
	return re.sub('[vV][0-9]+', 'v%03d' % version, filename)

'''
	Method: getVersion

	Returns version number of a given filename.
'''
def getVersion(filename):
	match = re.findall('[vV]([0-9]+)', filename)
	if (match):
		return int(match[-1])
	return 0


################### Information Retrieval ######################

'''
	Method: getDir

	Returns directory name of a file with a trailing '/'.
'''
def getDir(filename):
	return normalizeDir(os.path.dirname(filename))

'''
	Method: upADir

	Returns the path, up a single directory.
	If being called on a directory, be sure the directory is normalized before calling.
'''
def upADir(path):
	path = unixPath(path)
	parts = path.split('/')
	if (len(parts) < 3): return path
	return '/'.join(parts[:-2]) + '/'

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

def getFileInfo(path):
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
	Method: getFrameRange

	Returns a dictionary with 'min' (minFrame), 'max' (maxFrame), 'base' (fileName), and 'ext' (ext).

	Parameters:
		path - Generic file in sequence. Ex. text/frame.%04d.exr
'''
def getFrameRange(path):
	baseInFile, ext = os.path.splitext(path)
	# fix: this is done terribly, should be far more generic
	percentLoc = baseInFile.find('%')

	if percentLoc == -1:
		raise Exception('Frame padding not found in: ' + path)

	# second character after the %
	# ex: %04d returns 4
	try:
		padding = int(baseInFile[percentLoc + 2])
	except Exception as e:
		print 'Invalid padding:'
		print e
		return False

	minFrame = 9999999
	maxFrame = -9999999
	for f in glob.iglob(baseInFile[0:percentLoc] + '*'):
		frame = f[percentLoc:(percentLoc + padding)]
		if frame.isdigit():
			frame = int(frame)
			maxFrame = max(maxFrame,frame)
			minFrame = min(minFrame,frame)

	if minFrame == 9999999 or maxFrame == -9999999:
		return False

	return {'min': minFrame,
			'max': maxFrame,
			'base': baseInFile,
			'ext': ext}

######################### System Operations ############################


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
	Method: mkdir

	Wrapper for os.mkdir.
'''
def mkdir(dirname):
	try:
		os.mkdir(dirname)
	except Exception as err:
		return err

'''
	Method: makeDirs

	Wrapper for os.makedirs.
'''
def makeDirs(path):
	dirName = getFileInfo(path)['dirname']
	try:
		os.makedirs(dirName)
	except Exception as err:
		return err

'''
	Method: isDir

	Checks if a path is a directory.
'''
def isDir(path):
	return os.path.isdir(path)

'''
	Method: checkTempDir

	Checks if globalSettings.TEMP exists, and if not, creates it.
'''
def checkTempDir():
	if not os.path.exists(globalSettings.TEMP):
		makeDirs(globalSettings.TEMP)

'''
	Method: join

	Concatenates a directory with a file path using forward slashes.
'''
def join(a, b):
	return normalizeDir(a) + normalizePath(b)

'''
	Method: absolutePath

	Returns absolute path of a given path.
'''
def absolutePath(path):
	return normalizeDir(os.path.abspath(path))

'''
	Method: realPath

	Returns the normalized real path of a given path.
'''
def realPath(path):
	return os.path.realPath(path)

'''
	Method: getFiles

	Lists files in a given path.
'''
def getFiles(path):
	path = normalizePath(path)
	return subprocess.check_output(['ls', path]).split()

'''
	Method: removePath

	Wrapper for os.remove.  Returns False on error.
'''
def removePath(path):
	try:
		os.remove(path)
	except:
		return False

'''
	Method: removeDir

	Removes a directory.  Returns False on error.
'''
def removeDir(path):
	try:
		shutil.rmtree(path)
	except:
		return False

'''
	Method: emptyDir

	Removes all files and folders from a directory.

	Parameters:
		folder - directory from which to delete
		onlyFiles - False by default, if only files should be deleted
		waitTime - 5 by default, how many seconds to wait.
'''
def emptyDir(folder,onlyFiles=False, waitTime=5):
	# if onlyFiles:
	# 	print 'Deleting all files in: %s' % folder
	# else:
	# 	print 'Deleting all files and folders in: %s' % folder

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
	Method: cwd

	Returns the current working directory.
'''
def cwd():
	return normalizeDir(os.getcwd())

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
	src = ensureEndingSlash(src)
	dest = ensureEndingSlash(dest)

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
	Method: ensureArray

	If input is an array, return input.  If not, make it first element of a list.
'''
def ensureArray(val):
	if isinstance(val, (list, tuple)):
		return list(val)
	if (val == None):
		return []
	return [val]

'''
	Method: collectFiles

	Gets all files in the searchPaths with given extensions.

	Parameters:

		searchPaths - list of paths to search
		extensions - list of extensions for which to look
		exclusions - files to exclude from final list
'''
def collectFiles(searchPaths, extensions, exclusions):

	filesToReturn = []
	searchPaths = ensureArray(searchPaths)
	extensions = ensureArray(extensions)
	exclusions = ensureArray(exclusions)

	for path in searchPaths:
		for root, dirs, files in os.walk(path):
			for name in files:
				name = join(normalizeDir(root), normalizePath(name))
				if (fileExtension(name) in extensions) and (name not in exclusions):
					if name not in filesToReturn:
						filesToReturn.append(getFileInfo(name))
	return filesToReturn

'''
	Method: collectAllFiles

	Returns all files within a specified searchDir.
'''
def collectAllFiles(searchDir):

	searchDir = normalizeDir(searchDir)

	filesToReturn = []
	for root, dirs, files in os.walk(searchDir):
		for name in files:
				name = join(normalizeDir(root), normalizePath(name))
				if name not in filesToReturn:
					filesToReturn.append(getFileInfo(name))
	return filesToReturn




##################### Process Operations ########################

'''
	Method: getParentPID

	Returns the process ID of the parent process.
'''
def getParentPID():
	return psutil.Process(os.getpid()).ppid

'''
	Method: killJobProcesses

	Kills all other processes currently on the render node.
'''
def killJobProcesses(nodesOnly=True):
	"""Ruthlessly kills off all other processes on the render node"""
	if 'psutil' in globals():
		print 'No psutil module found'
		return False
	if not nodesOnly or 'RENDER' in os.environ['COMPUTERNAME']:
		currentProcess = os.getpid()
		processParent = getParentPID()
		for p in psutil.process_iter():
			try:
				name = p.name.lower()
				if '3dsmax' in name or \
					'nuke' in name or \
					'modo' in name or \
					'ffmpeg' in name or \
					('cmd.exe' in name and p.pid != processParent) or \
					('python.exe' in name and p.pid != currentProcess) or \
					'maxwell' in name:
					print 'Terminating %s' % name
					p.terminate()
			except:
				pass

'''
	Method: runCommand

	Executes a program using psutil.Popen, disabling Windows error dialogues.
'''
def runCommand(processArgs,env=None):
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
			key = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, keyVal, 0, globalSettings.KEY_ALL_ACCESS)
		except:
			key = _winreg.CreateKey(_winreg.HKEY_LOCAL_MACHINE, keyVal)
		# 1 (True) is the value
		_winreg.SetValueEx(key, 'ForceQueue', 0, _winreg.REG_DWORD, 1)

	# fix: use this everywhere
	command = ''
	if arkUtil.varType(processArgs) == 'list':
		command = '"' + processArgs[0] + '" '
		for i in range(1, len(processArgs)):
			processArgs[i] = str(processArgs[i])
			command += str(processArgs[i]) + ' '
		print 'command:\n', command
	else:
		print 'command:\n', processArgs

	return psutil.Popen(processArgs,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,env=env)

'''
	Method: runPython

	Executes a given python file.
'''
def runPython(pythonFile):
	return os.system(globalSettings.PYTHON + ' ' + pythonFile)


####################### Update Operations #######################

'''
	Method: updateTools

	Updates tools from the git repo if available.
'''
def updateTools(toolsDir=None):
	if not globalSettings.IS_NODE:
		print 'Bailing on update, not a node'
		return

	if not toolsDir:
		toolsDir = globalSettings.ARK_ROOT

	print toolsDir + 'bin/hardUpdate.bat'
	os.system(toolsDir + 'bin/hardUpdate.bat')
	print 'Tools updated'
	# if the tools haven't been installed to the root, copy them now
	# try:
	# 	import git
	# except:
	# 	git = None

	# if git:
	# 	try:
	# 		print '\nTools installed: %s, updating with git python' % toolsDir
	# 		repo = git.Repo(toolsDir)
	# 		print repo.git.pull()
	# 		return True
	# 	except Exception as err:
	# 		print '\nError updating tools with git python: ', err
	# if os.path.isdir(toolsDir + '.git'):
	# 	print '\nTools installed: %s, updating with git command line' % toolsDir
	# 	os.system(toolsDir.split(':')[0] + ': && \
	# 				cd ' + toolsDir + ' && ' +
	# 				'"' + globalSettings.GIT_EXE + '"' + ' pull')
	# 	return True

	return False

'''
	Method: isWindows

	Returns whether or not the machine running the command is Windows.
'''
def isWindows():
	return sys.platform.startswith('win')


####################### Command Line Utilities #######################

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
			key = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, keyVal, 0, globalSettings.KEY_ALL_ACCESS)
		except:
			key = _winreg.CreateKey(_winreg.HKEY_LOCAL_MACHINE, keyVal)
		# 1 (True) is the value
		_winreg.SetValueEx(key, 'ForceQueue', 0, _winreg.REG_DWORD, 1)

	# else:
	#     subprocess_flags = 0
	command = ''
	if arkUtil.varType(processArgs) == 'list':
		command = '"' + processArgs[0] + '" '
		for i in range(1, len(processArgs)):
			processArgs[i] = str(processArgs[i])
			command += str(processArgs[i]) + ' '
		print 'command:\n', command
	else:
		print 'command:\n', processArgs

	# return subprocess.Popen(processArgs,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env)
	return psutil.Popen(processArgs,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env)
