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

Todo:
- [ ] rename:
	- collectFiles > getFiles
	- collectFilesSync > getFilesSync
	- copyTree > copyDir
- [ ] refactor javascript's getFiles to match python's implementation as it's far superior
- [ ] refactor the places javascript's getFiles is used to work with the new implementation
- [ ] add getSequenceBaseName to javascript
- [ ] add getFrameNumber to javascript

## 0.1.0 Changes
### Added
- getFiles (python)
- getSequenceBaseName (python)
- getFrameNumber (python)

### Modified
- normalizeDir - no longer removes starting slash
- getFileInfo - relative dir now prefixed w/ ./
- runCommand (python) - now just runs the command w/ os.system, used to be a duplicate of startSubprocess

### Renamed
- stripExtension > removeExtension
- getFileInfo > getPathInfo
- dirname > getDirName
- collectFilenamesSync > collectFilesSync
- collectRegexMatches > getRegexMatches

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
- updateTools moved to moduleTools
- killJobProcesses moved to shepherd.computer

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
