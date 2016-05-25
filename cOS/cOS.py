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

def ensureEndingSlash(path):
	'''
		Appends a / to the end of a path if it's not there yet.
	'''
	path = unixPath(path)
	if path[-1] != '/':
		path = path + '/'
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
		Dirs always use forward slashses, don't have a leading slash, and have a trailing slash.
	'''
	path = unixPath(path)
	path = removeStartingSlash(path)
	return ensureEndingSlash(path)

def normalizePath(path):
	'''
		Removes starting slash, and replaces all backslashes with forward slashses.
	'''
	path = removeStartingSlash(path)
	return unixPath(path)

def unixPath(path):
	'''
		Changes backslashes to forward slashes and removes successive slashes, ex \\ or \/
	'''
	"""changes backslashes to forward slashes.
	also removes any successive slashes, ex: \\ or \/"""
	url = path.split('://')
	if len(url) > 1:
		return url[0] + '://' + re.sub(r'[\\/]+', '/', url[1])
	return re.sub(r'[\\/]+', '/', path)

def unicodeToString(partialJSON):
	'''
		to byte strings
	'''
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

def getExtension(filename):

	'''
		Returns file extension all lowercase with no whitespace, preceded by a period.
	'''
	if '.' not in filename:
		return ''
	return filename.split('.')[-1].lower().strip()

def normalizeExtension(extension):
	'''
		Returns file extension all lowercase with no whitespace, preceded by a period.
	'''
	extension = extension.lower().strip()
	if extension[0] == '.':
		return extension[1:]
	return extension

'''
	Removes extension from filename.
'''
def removeExtension(filename):
	if '.' not in filename:
		return filename
	return '.'.join(filename.split('.')[:-1])

'''
	Checks that a given file has the given extension.  If not, appends the extension.
'''
def ensureExtension(filename, extension):
	extension = normalizeExtension(extension)
	if (getExtension(filename) != extension):
		return filename + '.' + extension
	return filename

def getConvertFile(outFile):
	'''
		Creates convert file by removing file extension, and appending '_convert.nk'.
	'''
	pi = getFileInfo(outFile)
	return pi['dirname'] + pi['filebase'] + '_convert.nk'


#################### Versioning Operations ######################

# fix: currently increments all versions, should it?
'''
	Returns file with version incremented in all locations in the name.
'''
def incrementVersion(filename):
	version = getVersion(filename) + 1
	return re.sub('[vV][0-9]+', 'v%04d' % version, filename)

'''
	Returns version number of a given filename.
'''
def getVersion(filename):
	match = re.findall('[vV]([0-9]+)', filename)
	if (match):
		return int(match[-1])
	return 0


'''
	Returns highest version from a given root, matching a given extension.
'''
def getHighestVersion(root, extension):
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

################### Information Retrieval ######################

'''
	Returns directory name of a file with a trailing '/'.
'''
def getDir(filename):
	return normalizeDir(os.path.dirname(filename))

'''
	Returns the path, up a single directory.
	If being called on a directory, be sure the directory is normalized before calling.
'''
def upADir(path):
	path = unixPath(path)
	parts = path.split('/')
	if (len(parts) < 3): return path
	return '/'.join(parts[:-2]) + '/'

'''
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
	Returns a dictionary with 'min' (minFrame), 'max' (maxFrame), 'base' (fileName), and 'ext' (ext).

	Parameters:
		path - Generic file in sequence. Ex. text/frame.%04d.exr
'''
def getFrameRange(path):
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
		print 'Invalid padding:'
		print path
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

######################### System Operations ############################


'''
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
	Wrapper for os.mkdir.
'''
def mkdir(dirname):
	try:
		os.mkdir(dirname)
	except Exception as err:
		return err

'''
	Wrapper for os.makedirs.
'''
def makeDirs(path):
	dirName = getFileInfo(path)['dirname']
	try:
		os.makedirs(dirName)
	except Exception as err:
		return err

'''
	Checks if a path is a directory.
'''
def isDir(path):
	return os.path.isdir(path)

'''
	Checks if globalSettings.TEMP exists, and if not, creates it.
'''
def checkTempDir():
	if not os.path.exists(globalSettings.TEMP):
		makeDirs(globalSettings.TEMP)

'''
	Concatenates a directory with a file path using forward slashes.
'''
def join(a, b):
	return normalizeDir(a) + normalizePath(b)

'''
	Returns absolute path of a given path.
'''
def absolutePath(path):
	return normalizeDir(os.path.abspath(path))

'''
	Returns the normalized real path of a given path.
'''
def realPath(path):
	return os.path.realPath(path)

'''
	Lists files in a given path.
'''
def getFiles(path):
	path = normalizePath(path)
	return subprocess.check_output(['ls', path]).split()

'''
	Wrapper for os.remove.  Returns False on error.
'''
def removePath(path):
	try:
		os.remove(path)
	except:
		return False

'''
	Removes a directory.  Returns False on error.
'''
def removeDir(path):
	try:
		shutil.rmtree(path)
	except:
		return False

'''
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
	Returns the current working directory.
'''
def cwd():
	return normalizeDir(os.getcwd())

'''
	Copies the src directory tree to the destination.
'''
def copyTree(src, dst, symlinks=False, ignore=None):
	dir_util.copy_tree(src, dst)

'''
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
	If input is an array, return input.  If not, make it first element of a list.
'''
def ensureArray(val):
	if isinstance(val, (list, tuple)):
		return list(val)
	if (val == None):
		return []
	return [val]

'''
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
				if (getExtension(name) in extensions) and (name not in exclusions):
					if name not in filesToReturn:
						filesToReturn.append(getFileInfo(name))
	return filesToReturn

'''
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
	Returns the process ID of the parent process.
'''
def getParentPID():
	return psutil.Process(os.getpid()).ppid

'''
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

'''
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
	Executes a given python file.
'''
def runPython(pythonFile):
	return os.system(globalSettings.PYTHON + ' ' + pythonFile)


####################### Update Operations #######################

'''
	Updates tools from the git repo if available.
'''
def updateTools(toolsDir=None):
	# return True
	if not globalSettings.IS_NODE:
		print 'Bailing on update, not a node'
		return

	toolsDir = globalSettings.ARK_ROOT

	try:
		print toolsDir + 'bin/hardUpdate.bat'
		os.system(toolsDir + 'bin/hardUpdate.bat')
		print 'Tools updated'
		return True
	except Exception as err:
		print 'Failed to update tools:', err
		pass
		return False

'''
	Returns whether or not the machine running the command is Windows.
'''
def isWindows():
	return sys.platform.startswith('win')


####################### Command Line Utilities #######################

'''
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


if __name__ == '__main__':
	path = 'C:/Trash/sequenceTesting/sequence2.%04d.jpg'
	print getFrameRange(path)
