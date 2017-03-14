import os
import time
import sys
import subprocess
import glob
import shutil
from distutils import dir_util
import re
import fnmatch
import Queue
import threading

try:
	import psutil
except:
	pass

# Helpers
##################################################
def ensureArray(val):
	'''
	If input is an array, return input.  If not, make it first element of a list.
	'''
	if isinstance(val, (list, tuple)):
		return list(val)
	if (val == None):
		return []
	return [val]

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
	# lower case drive leters
	if path[1] == ':':
		path = path[0].lower() + path[1:]

	# ensureEndingSlash already makes sure
	# the path is a unixPath
	return ensureEndingSlash(path)

def normalizePath(path):
	'''
	Replaces all backslashes
	with forward slashses.
	Removed: removeStartingSlash
	'''
	return unixPath(path)

def unixPath(path):
	'''
	Changes backslashes to forward slashes and
	removes successive slashes, ex \\ or \/
	'''
	# lower case drive leters
	if not path:
		return ''
	if len(path) > 1 and path[1] == ':':
		path = path[0].lower() + path[1:]

	# bit hacky, but basically we want to keep
	# :// for http:// type urls
	# so we split on that, replace the slashes in the parts
	# then join it all back together
	parts = path.split('://')
	replaced = [re.sub(r'[\\/]+', '/', p) for p in parts]
	return '://'.join(replaced)


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
	try:
		if str(int(filename)) == filename:
			return int(filename)
	except:
		pass

	try:
		if int(filename) == filename:
			return int(filename)
	except:
		pass

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

def getHighestVersionFilePath(root, extension=''):
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

def createVersionedFilename(filename, version, padding=4, extension=''):

	'''
	Returns filename with version and extension
	'''
	return filename + '_v' + str(version).zfill(padding) + '.' + extension

# Information
##################################################

def getDirName(filename):
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

def getPathInfo(path, options={}):
	'''
	Returns object with file's basename, extension, name, dirname and path.
	With options, can also return root, relative dirname, and relative path, and
	make all fields lowercase.
	'''
	if len(path) == 0:
		return {
			'path': '',
			'dirname': '',
			'basename': '',
			'extension': '',
			'name': '',
			'filebase': '',
			'root': '',
			'relativeDirname': '',
			'relativePath': '',
		}
	pathInfo = {}
	pathInfo['path'] = normalizePath(path)
	pathParts = pathInfo['path'].split('/')
	pathInfo['dirname'] = '/'.join(pathParts[:-1]) + '/'
	pathInfo['basename'] = pathParts[-1]
	pathInfo['extension'] = normalizeExtension(pathParts[-1].split('.')[-1].strip().lower())
	pathInfo['name'] = pathInfo['basename'].replace('.' + pathInfo['extension'], '')
	pathInfo['filebase'] = pathInfo['path'].replace('.' + pathInfo['extension'], '')

	# fix: relative path could be improved but it's a start
	if options.get('root'):
		pathInfo['root'] = normalizeDir(options['root'])
		pathInfo['relativeDirname'] = './' + removeStartingSlash(normalizeDir(pathInfo['dirname'].replace(pathInfo['root'], '')))
		pathInfo['relativePath'] = './' + removeStartingSlash(normalizePath(pathInfo['path'].replace(pathInfo['root'], '')))

	if options.get('lowercaseNames'):
		# uncomment in Sublime 3
		# pathInfo = {x: x.lower() for x in pathInfo}
		pathInfo = dict([(x, x.lower()) for x in pathInfo])

	return pathInfo

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
		print 'Frame padding not found in: ' + path
		return False

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
		print 'No frames found:', path
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

def getSequenceBaseName(filename):
	regex_baseName = re.compile('(.+)[_\.][0-9]+\.[a-z0-9]+$')
	try:
		baseName = regex_baseName.search(filename).group(1)
		return baseName
	except:
		raise IndexError('The filename given does not have the \
			format <name>_<frameNumber>.<extension> or \
			<name>.<frameNumber>.<extension>: %s' % filename)

def getFrameNumber(filename):
	regex_FrameNumber = re.compile('.+[_\.]([0-9]+)\.[a-z0-9]+$')
	try:
		frame = regex_FrameNumber.search(filename).group(1)
		return frame
	except:
		raise IndexError('The filename given does not have the \
			format <name>_<frameNumber>.<extension> or \
			<name>.<frameNumber>.<extension>: %s' % filename)

def isFrameRangeText(filename):
	regex = re.compile('^[a-zA-Z0-9._/:%]+ [0-9]+-[0-9]+$')
	return regex.match(filename) is not None

def getFrameRangeText(filename):
	frameRange = getFrameRange(filename)
	if not frameRange:
		raise Exception('Invalid filename: ' + filename)
	print 'Frame Range:', frameRange
	return filename + ' %d-%d' % \
		(frameRange['min'], frameRange['max'])

# System Operations
##################################################

# fix: needs to work for linux / osx
def setEnvironmentVariable(key, val, permanent=True):
	'''
	Sets a given environment variable for the OS.

	Parameters:
		key - environment variable
		val - value for the environment variable
	'''
	val = str(val)
	os.environ[key] = val

	if not permanent:
		return True

	# set the environment variable permanently
	# super simple on windows, just use setx
	if isWindows():
		os.system('setx %s "%s"' % (key, val))

	# set variables in the /etc/environment file
	# on mac and linux
	elif isMac() or isLinux():
		os.system('export %s=%s' % (key, val))
		environmentFile = '/etc/environment'
		setString = key + '=' + val + '\n'

		# read all the lines in
		with open(environmentFile) as f:
			lines = f.readlines()

		found = False
		i = 0
		while i < len(lines):
			if lines[i].startswith(key + '='):
				# if we've already set the variable
				# just remove the line
				if found:
					del lines[i]
				# otherwise ensure the line is set
				# to the correct value
				else:
					lines[i] = setString
				found = True
			i += 1

		# if we never found the variable
		# append a line to set it
		if not found:
			lines.append(setString)

		# then write all the lines back to the
		# environmentFile
		with open(environmentFile, 'w') as f:
			for line in lines:
				f.write(line.replace(' ',''))

def makeDir(dirname):
	'''
	Wrapper for os.makeDir.
	'''
	try:
		os.mkdir(dirname)
		return True
	except Exception as err:
		return err

def makeDirs(path):
	'''
	Wrapper for os.makedirs.
	'''
	dirName = getDirName(path)
	try:
		os.makedirs(dirName)
	except Exception as err:
		return err

def join(a, b):
	'''
	Concatenates a directory with a file path
	using forward slashes.
	'''
	b = removeStartingSlash(b)
	return normalizeDir(a) + normalizePath(b)

def removeFile(path):
	'''
	Wrapper for os.remove, returns the error instead of
	throwing it
	'''
	if os.path.isdir(path):
		return Exception('Path is a directory, not a file')
	try:
		os.remove(path)
		return True
	except Exception as err:
		# If error is "not exists", don't raise, just return
		if not os.path.exists(path):
			return err
		else:
			raise err

def removeDir(path):
	'''
	Removes a directory.  Returns the error instead of
	throwing it
	'''
	if os.path.isfile(path):
		return Exception('Path is a file, not a directory')
	try:
		shutil.rmtree(path)
		return True
	except Exception as err:
		# If error is "not exists", don't raise, just return
		if not os.path.exists(path):
			return err
		else:
			raise err

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

def copy(src, dst):
	return shutil.copy2(src, dst)

def copyTree(src, dst, symlinks=False, ignore=None):
	'''
	Copies the src directory tree to the destination.
	'''
	dir_util.copy_tree(src, dst)

def rename (oldPath, newPath, callback):
	oldPath = normalizePath(oldPath)
	newPath = normalizePath(newPath)
	os.rename(oldPath, newPath)

def cwd():
	'''
	Returns the current working directory.
	'''
	return normalizeDir(os.getcwd())

def getUserHome():
	userHome = os.environ.get('HOME') or os.environ.get('HOMEPATH') or os.environ.get('USERPROFILE')
	return normalizeDir(userHome)

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


def getFolderContents(filepath, includeFiles=True, includeFolders=True):
	'''
	Returns files and folders directly under the path.
	'''
	paths = []
	files = os.listdir(filepath)
	for f in files:
		filename = os.path.join(filepath, f)
		isDir = os.path.isdir(filename)
		if includeFolders and isDir:
			paths.append(normalizeDir(filename))
		elif includeFiles and not isDir:
			paths.append(normalizePath(filename))

	return paths

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
						filesToReturn.append(getPathInfo(name))
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
					filesToReturn.append(getPathInfo(name))
	return filesToReturn

def collapseFiles(fileList):
	fileList.sort()
	collapsedList = []

	i = 0
	# New Logic to rename sequential files in QList
	while i < len(fileList):
		filePieces = fileList[i].split('.')
		if len(filePieces) <= 2:
			collapsedList.append(fileList[i])
			i += 1
		else:
			try:
				int(filePieces[-2])
				fileSections = fileList[i].partition(filePieces[-2])
				leftFileSection = fileSections[0]
				rightFileSection = fileSections[2]
				j = i
				while j<len(fileList) and \
					leftFileSection==fileSections[0] and \
					rightFileSection == fileSections[2]:
					j+=1
					try:
						filePiece = fileList[j].split('.')[-2]
						newFileSections = fileList[j].partition(filePiece)
						leftFileSection = newFileSections[0]
						rightFileSection = newFileSections[2]
					except IndexError:
						pass

				collapsedList.append(fileSections[0] +
									'%0' + str(len(fileSections[1])) + 'd' +
									fileSections[2] + ' ' +
									str(int(filePieces[-2])) + '-' +
									str(int(filePieces[-2]) + j - i - 1))
				i = j

			except ValueError:
				collapsedList.append(fileList[i])
				i+=1

	return collapsedList


# def getDirs(path):
# 	return getFiles(path, fileExcludes=['*'], depth=0)

# fix: add depth
def getFiles(path,
		fileIncludes=[],
		folderIncludes=[],
		fileExcludes=[],
		folderExcludes=[],
		includeAfterExclude=False,
		depth = -1):
	'''
	if the folder or file include/exclude lists have an *
	getFiles() will use wildcard matching, otherwise it will
	use simple "in"-style matching

	Ex:

	'''

	def shouldInclude(path, root, isDir=False):
		fullPath = unixPath(os.path.join(root, path))

		if fileIncludes and not isDir:
			for pattern in fileIncludes:
				if ('*' in pattern and \
					(fnmatch.fnmatch(fullPath, pattern) or \
					fnmatch.fnmatch(path, pattern))) or \
					pattern in fullPath:
					return True
			if not includeAfterExclude:
				return False

		if folderIncludes and isDir:
			for pattern in folderIncludes:
				if ('*' in pattern and \
					(fnmatch.fnmatch(fullPath, pattern) or \
					fnmatch.fnmatch(path, pattern))) or \
					pattern in fullPath:
					return True
			if not includeAfterExclude:
				return False

		if isDir:
			for pattern in folderExcludes:
				if ('*' in pattern and \
					(fnmatch.fnmatch(fullPath, pattern) or \
					fnmatch.fnmatch(path, pattern))) or \
					pattern in fullPath:
					return False
		else:
			for pattern in fileExcludes:
				if ('*' in pattern and \
					(fnmatch.fnmatch(fullPath, pattern) or \
					fnmatch.fnmatch(path, pattern))) or \
					pattern in fullPath:
					return False

		return True

# custom walk method with depth
# link for reference: http://stackoverflow.com/questions/229186/os-walk-without-digging-into-directories-below
	def walklevel(some_dir, depth=-1):
		some_dir = some_dir.rstrip(os.path.sep)
		assert os.path.isdir(some_dir)
		num_sep = some_dir.count(os.path.sep)
		for root, dirs, files in os.walk(some_dir):
			dirs[:] = [d for d in dirs if shouldInclude(d, root, True)]
			yield root, dirs, files
			num_sep_this = root.count(os.path.sep)
			if depth > -1:
				if num_sep + depth <= num_sep_this:
					del dirs[:]

	if fileIncludes:
		fileIncludes = ensureArray(fileIncludes)
	if folderIncludes:
		folderIncludes = ensureArray(folderIncludes)
	if fileExcludes:
		fileExcludes = ensureArray(fileExcludes)
	if folderExcludes:
		folderExcludes = ensureArray(folderExcludes)

	allFiles = []
	for root, dirs, files in walklevel(path, depth):
		for f in files:
			path = unixPath(os.path.join(root, f))
			if shouldInclude(f, root, False):
				allFiles.append(path)

	return allFiles

# Processes
##################################################
def getParentPID():
	'''
	Returns the process ID of the parent process.
	'''
	# Try/catch for old versions of old versions of psutil
	try:
		psutil.Process(os.getpid()).ppid
	except TypeError as err:
		print 'Psutil version 1.2 supported. Please revert.'
		raise err

def runCommand(processArgs,env=None):
	'''
	Executes a program using psutil.Popen, disabling Windows error dialogues.
	'''
	command = ' '.join(ensureArray(processArgs))
	os.system(command)

# returns the output (STDOUT + STDERR) of a given command
def getCommandOutput(command, cwd=None, shell=True, **kwargs):
	try:
		print 'command:\n', command
		output = subprocess.check_output(
			command,
			cwd=cwd,
			stderr=subprocess.STDOUT,
			shell=shell,
			**kwargs)
		if output and \
			len(output) > 0 and \
			output[-1] == '\n':
			output = output[:-1]
		if not output:
			output = ''
		return (output.lower(), False)
	except subprocess.CalledProcessError as err:
		return (False, err.output.lower())
	except Exception as err:
		return (False, err)

# fix: should use a better methodology for this
# pretty sure python has some way of running a file
def runPython(pythonFile):
	'''
	Executes a given python file.
	'''
	return os.system('python ' + pythonFile)

def waitOnProcess(process,
	checkInFunc=False,
	checkErrorFunc=False,
	timeout=False,
	loggingFunc=False,
	checkInInterval=10,
	outputBufferLength=10000):

	if not loggingFunc:
		def loggingFunc(*args):
			print ' '.join([str(arg) for arg in args])

	def queueOutput(out, outQueue):
		if out:
			for line in iter(out.readline, ''):
				outQueue.put(line)
			out.close()

	def checkProcess(process):
		if not process.is_running():
			print 'Process stopped'
			return False
		# STATUS_ZOMBIE doesn't work on Windows
		if not isWindows():
			return process.status() != psutil.STATUS_ZOMBIE
		return True

	def getQueueContents(queue, printContents=True):
		contents = ''
		lines = 0
		maxLines = 200
		while not queue.empty() and lines < maxLines:
			line = queue.get_nowait()
			contents += line
			if printContents:
				# remove the newline at the end
				print line[:-1]
			lines += 1

		if lines >= maxLines:
			print '\n\n\nbailed on getting the rest of the queue'
			queue.queue.clear()
		return contents

	lastUpdate = 0

	out = newOut = ''
	err = newErr = ''

	processStartTime = int(time.time())

	# threads dies with the program
	outQueue = Queue.Queue()
	processThread = threading.Thread(target=queueOutput, args=(process.stdout, outQueue))
	processThread.daemon = True
	processThread.start()

	errQueue = Queue.Queue()
	errProcessThread = threading.Thread(target=queueOutput, args=(process.stderr, errQueue))
	errProcessThread.daemon = True
	errProcessThread.start()

	re_whitespace = re.compile('^[\n\r\s]+$')

	while checkProcess(process):
		newOut = getQueueContents(outQueue, printContents=False)
		newErr = getQueueContents(errQueue, printContents=False)
		out += newOut
		err += newErr

		if newOut:
			loggingFunc(newOut[:-1])
		if newErr:
			notOnlyWhitespace = re_whitespace.match(newErr)
			# only care about non-white space errors
			if notOnlyWhitespace:
				if checkErrorFunc:
					checkErrorFunc(newErr[:-1])
				else:
					loggingFunc('\n\nError:')
					loggingFunc(newErr[:-1])
					loggingFunc('\n')

		# check in to see how we're doing
		if time.time() > lastUpdate + checkInInterval:
			# only keep the last 10,000 lines of log
			out = out[-outputBufferLength:]
			err = err[-outputBufferLength:]

			lastUpdate = time.time()
			if checkInFunc and not checkInFunc(out, err):
				try:
					process.kill()
				except:
					loggingFunc('Could not kill, please forcefully close the executing program')
				return (False, 'Check in failed')

			# if we've been rendering longer than the time alotted, bail
			processTime = (int(time.time()) - processStartTime) / 60.0
			if timeout and processTime >= timeout:
				loggingFunc('Process timed out.  Total process time: %.2f min' % processTime)
				return (False, 'timed out')

	# call wait to kill the zombie process on *nix systems
	process.wait()

	sys.stdout.flush()
	sys.stderr.flush()

	newOut = getQueueContents(outQueue, printContents=False)
	newErr = getQueueContents(errQueue, printContents=False)
	out += newOut
	err += newErr

	if newOut:
		loggingFunc(newOut[:-1])
	if newErr and checkErrorFunc:
		checkErrorFunc(err)

	return (out, err)

def startSubprocess(processArgs, env=None, shell=False):
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
		import ctypes

		SEM_NOGPFAULTERRORBOX = 0x0002 # From MSDN
		SEM_FAILCRITICALERRORS = 0x0001
		try:
			# equivalent to 0x0003
			ctypes.windll.kernel32.SetErrorMode(SEM_NOGPFAULTERRORBOX | SEM_FAILCRITICALERRORS)
		except:
			print 'Error setting Windows Error Mode'
			raise
		CREATE_NO_WINDOW = 0x08000000
		subprocess_flags = CREATE_NO_WINDOW

		# Here for posterity but this seems to always fail, so not active at the moment
		# This is supposed to suppress the Microsoft popup ('submit error to Microsoft')
		# try:
		# 	import _winreg
		# 	keyVal = r'SOFTWARE\Microsoft\Windows\Windows Error Reporting'
		# 	try:
		# 		key = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, keyVal, 0, _winreg.KEY_ALL_ACCESS)
		# 	except:
		# 		key = _winreg.CreateKey(_winreg.HKEY_LOCAL_MACHINE, keyVal)
		# 	# 1 (True) is the value
		# 	_winreg.SetValueEx(key, 'ForceQueue', 0, _winreg.REG_DWORD, 1)
		# except:
		# 	print 'Error setting Microsoft Error Reporting, passing...'

	else:
		subprocess_flags = 0

	command = ''
	if type(processArgs) == list:
		# wrap program w/ quotes if it has spaces
		if ' ' in processArgs[0]:
			command = '"' + processArgs[0] + '" '
		else:
			command = processArgs[0] + ' '

		for i in range(1, len(processArgs)):
			processArgs[i] = str(processArgs[i])
			command += str(processArgs[i]) + ' '
		print 'command:\n', command
	else:
		print 'command:\n', processArgs

	return psutil.Popen(
		processArgs,
		stdout=subprocess.PIPE,
		stderr=subprocess.PIPE,
		env=env,
		shell=shell,
		creationflags=subprocess_flags)

# IO
##################################################
def readFile(path):
	with open(path) as fileHandle:
		return fileHandle.readlines()

# OS
##################################################
def isWindows():
	'''
	Returns whether or not the machine running the command is Windows.
	'''
	return sys.platform.startswith('win')

def isLinux():
	'''
	Returns whether or not the machine running the command is Windows.
	'''
	return sys.platform.startswith('linux')

def isMac():
	'''
	Returns whether or not the machine running the command is Windows.
	'''
	return sys.platform.startswith('darwin')

# Command Line Utilities
##################################################

# fix: shouldn't really be using this, should
# generally call subprocess or some other way
def genArgs(argData):
	'''
	Generates a string of flag arguments from a dictionary.
	Arguments are of the form -k1 v1 -k2 v2
	'''
	args = ''
	for k,v in argData.iteritems():
		args += '-%s %s ' % (k,v)
	return args[:-1]

# fix: breaks on single dash arguments, improve
def getArgs(args=None):
	i = 1
	if not args:
		args = sys.argv
	options = {'__file__':args[0]}
	while (i < sys.argv.__len__() - 1):
		options[args[i].replace('-','').replace(':', '')] = args[i + 1]
		i += 2
	return options

def getTotalRam():
	'''
	Get the total system memory in GB on Linux and Windows

	From:
	http://stackoverflow.com/questions/2017545/get-memory-usage-of-computer-in-windows-with-python
	'''
	if isLinux():
		totalMemory = os.popen('free -m').readlines()[1].split()[1]
		return float(totalMemory) / 1024
	elif isWindows():
		import ctypes

		class MemoryUse(ctypes.Structure):
			_fields_ = [
				('dwLength', ctypes.c_ulong),
				('dwMemoryLoad', ctypes.c_ulong),
				('ullTotalPhys', ctypes.c_ulonglong),
				('ullAvailPhys', ctypes.c_ulonglong),
				('ullTotalPageFile', ctypes.c_ulonglong),
				('ullAvailPageFile', ctypes.c_ulonglong),
				('ullTotalVirtual', ctypes.c_ulonglong),
				('ullAvailVirtual', ctypes.c_ulonglong),
				('sullAvailExtendedVirtual', ctypes.c_ulonglong),
			]

			def __init__(self):
				# have to initialize this to the size of
				# MemoryUse
				self.dwLength = ctypes.sizeof(self)
				super(MemoryUse, self).__init__()

		stat = MemoryUse()
		ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
		return float(stat.ullTotalPhys) / 1024000000
	else:
		return 0

def findCaseInsensitiveFilename(path, mustExist=False):
	'''
	Finds a matching filename if one exists

	ex:
	c:/Some/Folder/awesome.txt
	would match the actual file:
	c:/some/folder/AWESOME.txt
	if mustExist=False would also match
	c:/some/folder/NewPath/yeah.txt
	'''

	path = unixPath(path)
	parts = path.split('/')

	pathFound = False
	for i in range(len(parts)-1):
		pathFound = False

		searchRoot = '/'.join(parts[0:i+1]) + '/'
		fileOrFolderToMatch = parts[i+1].lower()

		if not os.path.isdir(searchRoot):
			if mustExist:
				print searchRoot, 'not a directory'
			break

		files = os.listdir(searchRoot)
		for f in files:
			# print 'checking:', f, fileOrFolderToMatch
			if f.lower() == fileOrFolderToMatch:
				parts[i+1] = f
				pathFound = True

		if not pathFound:
			if mustExist:
				print 'Could not find:', fileOrFolderToMatch
			break

	if mustExist and not pathFound:
		return False

	return '/'.join(parts)


def followFile(fileObject, waitTime=2):
	# go to the end of the file
	# the '2' denotes '0 from the end'
	fileObject.seek(0, 2)
	while True:
		line = fileObject.readline()
		if not line:
			time.sleep(waitTime)
			continue

		# trim off the last character if it's a new line
		if line[-1] == '\n':
			line = line[:-1]
		yield line


def main():
	pass
	# filename = 'r:/Blackish_s03/Final_Renders/BLA_308/EXR_Linear/BLA_308_018_020_v0007/BLA_308_018_020_v0007.%04.exr 1000-1048'
	# print isFrameRangeText(filename)
	# basePath = 'C:/Program Files/Chaos Group/V-Ray/Maya 2016 for x64/vray_netinstall_client_setup.bat'
	# casePath = basePath.lower()

	# basePath = 'R:/OpticalFlaresLicense.lic'
	# casePath = 'r:/opticalFLARESLicense.lic'

	# basePath = 'Q:/Users/Grant_Miller/projects/someSweetProject/yeah.py'
	# casePath = 'Q:/Users/Grant_Miller/PROJECTS/someSweetProject/yeah.py'

	# print basePath
	# print findCaseInsensitiveFilename(casePath)
	# print findCaseInsensitiveFilename(casePath, mustExist=True)

	# print 'total ram:', getTotalRam()

if __name__ == '__main__':
	main()
