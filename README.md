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

### Removed
fileExtension (use getExtension instead)
filePrep (use unixPath instead)
pathInfo (use getPathInfo instead)
isDirSync (antipattern, don't use)
isFileSync (antipattern, don't use)

### Renamed
stripExtension > removeExtension
getFileInfo > getPathInfo




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
