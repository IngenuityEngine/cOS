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

# fix: why is this try / catched?
try:
	import psutil
except:
	pass


# Normalization
##################################################

def ensureEndingSlash(path):
	'''
	Ensures that the path has a trailing '/'
	'''
	path = unixPath(path)
	if path[-1] != '/':
		path += '/'
	return path

def removeStartingSlash(path):
	'''
	Removes backslashes and forward slashes from the
	beginning of directory names.
	'''
	if (path[0] == '\\' or path[0] == '/'):
		path = path[1:]
	return path

def normalizeDir(path):
	'''
	Dirs always use forward slashses and have a trailing slash.
	'''
	path = unixPath(path)
	return ensureEndingSlash(path)

def normalizePath(path):
	'''
	Removes starting slash, and replaces all backslashes
	with forward slashses.
	'''
	path = removeStartingSlash(path)
	return unixPath(path)

def unixPath(path):
	'''
	Changes backslashes to forward slashes and
	removes successive slashes, ex \\ or \/
	'''
	url = path.split('://')
	if len(url) > 1:
		return url[0] + '://' + re.sub(r'[\\/]+', '/', url[1])
	return re.sub(r'[\\/]+', '/', path)

def unicodeToString(data):
	'''
	Replaces unicode with a regular string
	for a variety of data types
	'''
	inputType = type(data)
	if isinstance(data, types.StringTypes):
		return str(data)
	elif inputType == types.ListType:
		return [unicodeToString(x) for x in data]
	elif inputType == types.DictType:
		# fix: uncomment in Sublime 3
		# return {unicodeToString(x): unicodeToString(data[x]) for x in data}
		return dict([(unicodeToString(x), unicodeToString(data[x])) for x in data])
	else:
		return data


# Extensions
##################################################

def getExtension(path):
	'''
	Returns file extension all lowercase with no whitespace
	'''
	path = path.split('.')
	if len(path) > 1:
		return path.pop().lower()
	return ''

def normalizeExtension(extension):
	'''
	Returns file extension all lowercase with no whitespace
	'''
	extension = extension.lower().strip()
	if extension[0] == '.':
		return extension[1:]
	return extension

def removeExtension(filename):
	'''
	Removes extension from filename.
	'''
	if '.' not in filename:
		return filename
	return '.'.join(filename.split('.')[:-1])

def ensureExtension(filename, extension):
	'''
	Checks that a given file has the given extension.
	If not, appends the extension.
	'''
	extension = normalizeExtension(extension)
	if (getExtension(filename) != extension):
		return filename + '.' + extension
	return filename

# Versioning
##################################################

def getVersion(filename):
	'''
	Returns version number of a given filename.
	'''
	match = re.findall('[vV]([0-9]+)', filename)
	if (match):
		return int(match[-1])
	return 0

def incrementVersion(filename):
	'''
	Increments a file's version number
	'''
	version = getVersion(filename) + 1
	return re.sub('[vV][0-9]+', 'v%04d' % version, filename)

def getHighestVersion(root, extension):
	'''
	Returns highest version from a given root, matching a given extension.
	'''
	# fix: should have normalize extension
	# ensure dot on extension
	if extension[0] != '.':
		extension = '.' + extension

	root = normalizeDir(root)
	highestVersion = -99999999
	path = False
	for f in glob.iglob(root + '*' + extension):
		fileVersion = getVersion(f)
		if fileVersion > highestVersion:
			path = unixPath(f)
			highestVersion = fileVersion

	return path

# Information
##################################################

def getDir(filename):
	'''
	Returns directory name of a file with a trailing '/'.
	'''
	return normalizeDir(os.path.dirname(filename))

def upADir(path):
	'''
	Returns the path, up a single directory.
	'''
	path = unixPath(path)
	parts = path.split('/')
	if (len(parts) < 3):
		return path
	return '/'.join(parts[:-2]) + '/'

def getFileInfo(path, options=None):
	'''
	Returns object with file's basename, extension, name, dirname and path.
	With options, can also return root, relative dirname, and relative path, and
	make all fields lowercase.
	'''
	fileInfo = {}
	fileInfo['path'] = normalizePath(path)
	pathParts = fileInfo['path'].split('/')
	fileInfo['dirname'] = '/'.join(pathParts[:-1]) + '/'
	fileInfo['basename'] = pathParts[-1]
	fileInfo['extension'] = normalizeExtension(pathParts[-1].split('.')[-1].strip().lower())
	fileInfo['name'] = fileInfo['basename'].replace('.' + fileInfo['extension'], '')
	fileInfo['filebase'] = fileInfo['path'].replace('.' + fileInfo['extension'], '')

	# fix: relative path could be improved but it's a start
	if options and \
			'root' in options and \
			options['root']:
		fileInfo['root'] = normalizeDir(options['root'])
		fileInfo['relativeDirname'] = './' + removeStartingSlash(normalizeDir(fileInfo['dirname'].replace(fileInfo['root'], '')))
		fileInfo['relativePath'] = './' + removeStartingSlash(normalizePath(fileInfo['path'].replace(fileInfo['root'], '')))

	if options and \
			'lowercaseNames' in options and \
		options['lowercaseNames']:
		# uncomment in Sublime 3
		# fileInfo = {x: x.lower() for x in fileInfo}
		fileInfo = dict([(x, x.lower()) for x in fileInfo])

	return fileInfo

def getFrameRange(path):
	'''
	Returns a dictionary with min, max, duration,
	base, ext, and complete

	Parameters:
		path - Generic file in sequence. Ex. text/frame.%04d.exr
	'''
	baseInFile, ext = os.path.splitext(path)
	# fix: this is done terribly, should be far more generic
	percentLoc = baseInFile.find('%')
	extension = getExtension(path)

	if percentLoc == -1:
		raise Exception('Frame padding not found in: ' + path)

	# second character after the %
	# ex: %04d returns 4
	padding = re.findall(r'%([0-9]+)d', path)
	if len(padding):
		padding = int(padding[0])
	else:
		print 'Invalid padding:', path
		return False

	minFrame = 9999999
	maxFrame = -9999999
	files = list(glob.iglob(baseInFile[0:percentLoc] + '*.' + extension))
	for f in files:
		frame = f[percentLoc:(percentLoc + padding)]
		if frame.isdigit():
			frame = int(frame)
			maxFrame = max(maxFrame,frame)
			minFrame = min(minFrame,frame)

	if minFrame == 9999999 or maxFrame == -9999999:
		return False

	duration = maxFrame - minFrame + 1
	count = len(files)
	return {
			'min': minFrame,
			'max': maxFrame,
			'duration': duration,
			'base': baseInFile,
			'ext': ext,
			'complete': duration == count,
		}



# System Operations
##################################################

# fix: needs to work for linux / osx
def setEnvironmentVariable(key, val):
	'''
	Sets a given environment variable for the OS.

	Parameters:
		key - environment variable
		val - value for the environment variable
	'''
	val = str(val)
	os.environ[key] = val
	return os.system('setx %s "%s"' % (key, val))

def mkdir(dirname):
	'''
	Wrapper for os.mkdir.
	'''
	try:
		os.mkdir(dirname)
	except Exception as err:
		return err

def makeDirs(path):
	'''
	Wrapper for os.makedirs.
	'''
	dirName = getFileInfo(path)['dirname']
	try:
		os.makedirs(dirName)
	except Exception as err:
		return err

def isDir(path):
	'''
	Checks if a path is a directory.
	'''
	return os.path.isdir(path)

'''
Concatenates a directory with a file path using forward slashes.
'''
def join(a, b):
	return normalizeDir(a) + normalizePath(b)

def absolutePath(path):
	'''
	Returns absolute path of a given path.
	'''
	return normalizeDir(os.path.abspath(path))

def realPath(path):
	'''
	Returns the normalized real path of a given path.
	'''
	return os.path.realPath(path)

def getFiles(path):
	'''
	Lists files in a given path.
	'''
	path = normalizePath(path)
	return subprocess.check_output(['ls', path]).split()

def removePath(path):
	'''
	Wrapper for os.remove.  Returns False on error.
	'''
	try:
		os.remove(path)
	except:
		return False

def removeDir(path):
	'''
	Removes a directory.  Returns False on error.
	'''
	try:
		shutil.rmtree(path)
	except:
		return False

def emptyDir(folder,onlyFiles=False, waitTime=5):
	'''
	Removes all files and folders from a directory.

	Parameters:
		folder - directory from which to delete
		onlyFiles - False by default, if only files should be deleted
		waitTime - 5 by default, how many seconds to wait.
	'''
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
def cwd():
	'''
	Returns the current working directory.
	'''
	return normalizeDir(os.getcwd())

def copyTree(src, dst, symlinks=False, ignore=None):
	'''
	Copies the src directory tree to the destination.
	'''
	dir_util.copy_tree(src, dst)

def duplicateDir(src, dest):
	'''
	Duplicates a directory, copying files that don't already exist.
	'''
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

def ensureArray(val):
	'''
	If input is an array, return input.  If not, make it first element of a list.
	'''
	if isinstance(val, (list, tuple)):
		return list(val)
	if (val == None):
		return []
	return [val]

def collectFiles(searchPaths, extensions, exclusions):
	'''
	Gets all files in the searchPaths with given extensions.

	Parameters:

		searchPaths - list of paths to search
		extensions - list of extensions for which to look
		exclusions - files to exclude from final list
	'''

	filesToReturn = []
	searchPaths = ensureArray(searchPaths)
	extensions = ensureArray(extensions)
	exclusions = ensureArray(exclusions)

	for path in searchPaths:
		for root, dirs, files in os.walk(path):
			for name in files:
				name = join(normalizeDir(root), normalizePath(name))
				if (getExtension(name) in extensions) and (name not in exclusions):
					if name not in filesToReturn:
						filesToReturn.append(getFileInfo(name))
	return filesToReturn

def collectAllFiles(searchDir):
	'''
	Returns all files within a specified searchDir.
	'''

	searchDir = normalizeDir(searchDir)

	filesToReturn = []
	for root, dirs, files in os.walk(searchDir):
		for name in files:
				name = join(normalizeDir(root), normalizePath(name))
				if name not in filesToReturn:
					filesToReturn.append(getFileInfo(name))
	return filesToReturn




# Process Operations
##################################################
def getParentPID():
	'''
	Returns the process ID of the parent process.
	'''
	return psutil.Process(os.getpid()).ppid

def killJobProcesses(nodesOnly=True):
	'''
	Kills all other processes currently on the render node.
	'''
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
					'houdini' in name or \
					'mantra' in name or \
					'maya' in name or \
					'vray' in name or \
					'ffmpeg' in name or \
					('cmd.exe' in name and p.pid != processParent) or \
					('python.exe' in name and p.pid != currentProcess) or \
					'maxwell' in name:
					print 'Terminating %s' % name
					p.terminate()
			except:
				pass

def runCommand(processArgs,env=None):
	'''
	Executes a program using psutil.Popen, disabling Windows error dialogues.
	'''

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
		# fix: the value shouldn't be 19, it used to be
# KEY_ALL_ACCESS which was getting pulled from global settings
		try:
			key = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, keyVal, 0, 19)
		except:
			key = _winreg.CreateKey(_winreg.HKEY_LOCAL_MACHINE, keyVal)
		# 1 (True) is the value
		_winreg.SetValueEx(key, 'ForceQueue', 0, _winreg.REG_DWORD, 1)

	# fix: use this everywhere
	command = ''
	if type(processArgs) == list:
		command = '"' + processArgs[0] + '" '
		for i in range(1, len(processArgs)):
			processArgs[i] = str(processArgs[i])
			command += str(processArgs[i]) + ' '
		print 'command:\n', command
	else:
		print 'command:\n', processArgs

	return psutil.Popen(processArgs,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,env=env)

def runPython(pythonFile):
	'''
	Executes a given python file.
	'''
	return os.system('python ' + pythonFile)


####################### Update Operations #######################

def isWindows():
	'''
	Returns whether or not the machine running the command is Windows.
	'''
	return sys.platform.startswith('win')


####################### Command Line Utilities #######################

def genArgs(argData):
	'''
	Generates a string of flag arguments from an iterable of tuples k, v tuples.
	Arguments are of the form -k1 v1 -k2 v2...etc.
	'''
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
		# fix: this shouldn't be 19
		# used to be pulled from global settings
		# also duplicated in runProgram, should pick one
		try:
			key = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, keyVal, 0, 19)
		except:
			key = _winreg.CreateKey(_winreg.HKEY_LOCAL_MACHINE, keyVal)
		# 1 (True) is the value
		_winreg.SetValueEx(key, 'ForceQueue', 0, _winreg.REG_DWORD, 1)

	# else:
	#     subprocess_flags = 0
	command = ''
	if type(processArgs) == list:
		command = '"' + processArgs[0] + '" '
		for i in range(1, len(processArgs)):
			processArgs[i] = str(processArgs[i])
			command += str(processArgs[i]) + ' '
		print 'command:\n', command
	else:
		print 'command:\n', processArgs

	# return subprocess.Popen(processArgs,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env)
	return psutil.Popen(processArgs,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env)


if __name__ == '__main__':
	path = 'C:/Trash/sequenceTesting/sequence2.%04d.jpg'
	print getFrameRange(path)
