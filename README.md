# cOS

Short for common OS.

Provides a common set of OS operations in Javascript and Python.


## Running tests:

### Javascript

Ensure [mocha](https://mochajs.org/) is installed globally
```
	c:/ie/cOS >> mocha test
```

### Python
Ensure [tryout](https://github.com/IngenuityEngine/tryout) is installed and properly pathed

```
	c:/ie/cOS >> python test
```



## 0.1.0 Changes

### Modified
- normalizeDir - no longer removes starting slash
- getFileInfo - relative dir now prefixed w/ ./
- runCommand (python) - now just runs the command w/ os.system, used to be a duplicate of startSubprocess

### Renamed
- stripExtension > removeExtension
- getFileInfo > getPathInfo
- dirname > getDirName
- collectFilenamesSync > collectFilesSync

### Removed
- fileExtension (use getExtension)
- filePrep (use unixPath)
- pathInfo (use getPathInfo)
- isDirSync (antipattern, don't use)
- isDir (antipattern, don't use)
- isFileSync (antipattern, don't use)
- absolutePath (unused)
- remove (use removeFile or removeDir)
- removeSync (use removeFileSync or removeDirSync)
- collectFilesSync (unused)
- getDir (use getDirName)
- unlinkSync (use removeFileSync)
- createFolder (use makeDir)
- createFolderSync (use makeDir)
- osPath (use pathman)
- universalPath (use pathman)
- getConvertFile (unused)
- checkTempDir (doesn't belong here)

### Moved
- find a home for:

	def updateTools(toolsDir=None):
		'''
		Updates tools from the git repo if available.
		'''
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




## 0.0.3 Changes

### Modified
- Modifications to names of functions
- Python normalizeDir >> ensureEndingSlash
- Javascript dirName >> getDir
- Javascript unlinkSync >> removePathSync
- Python emptyFolder >> emptyDir
- Javascript copySync >> copyTreeSync
- Javascript shouldExclude >> contains
- Python startSubprocess >> runCommand

### Added
- Python - removeStartingSlash(path)
- Python - normalizeDir(path)
- Javascript - unixPath(dir)
- Javascript - universalPath(dir)
- Python - normalizeExtension(ext)
- Javascript - fileExtension(path)
- Javascript - getConvertFile(path)
- Javascript - getVersion(filename)
- Javascript - incrementVersion(filename)
- Javascript - padLeft(str, padString, length)
- Python - upADir(path)
- Javascript - getFrameRange(path)
- Javascript - mkdir(dirname)
- Python - isDir(path)
- Javascript - checkTempDir()
- Python - join(a, b)
- Python - absolutePath(path)
- Python - realPath(path)
- Python - getFiles(path)
- Python - removePath(path)
- Python - removeDir(path)
- Python - cwd()
- Python - ensureArray(val)
- Python - collectFiles(searchPaths, extensions, exclusions)
- Python - collectAllFiles(searchDir)
- Javascript - runPython(pythonFile)
- Python - isWindows()

### Removed
- Python - getParentPID() >> Shepherd
- Python - killJobProcesses >> Shepherd
