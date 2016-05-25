## cOS

Short for common OS.
Provides a common set of OS operations in Javascript and Python.

Refactor Modifications
=====================================================
Removed:
fileExtension (use getExtension instead)
filePrep (use unixPath instead)

Renamed:
stripExtension > removeExtension



Modifications made to cOS.py and cOS.js
@Mike Ravella

Modifications to existing functionality of functions:

Modifications to names of functions:
Python normalizeDir >> ensureEndingSlash
Javascript dirName >> getDir
Javascript unlinkSync >> removePathSync
Python emptyFolder >> emptyDir
Javascript copySync >> copyTreeSync
Javascript shouldExclude >> contains
Python startSubprocess >> runCommand

New Functions:
Python - removeStartingSlash(path)
Python - normalizeDir(path)
Javascript - unixPath(dir)
Javascript - universalPath(dir)
Python - normalizeExtension(ext)
Javascript - fileExtension(path)
Javascript - getConvertFile(path)
Javascript - getVersion(filename)
Javascript - incrementVersion(filename)
Javascript - padLeft(str, padString, length)
Python - upADir(path)
Javascript - getFrameRange(path)
Javascript - mkdir(dirname)
Python - isDir(path)
Javascript - checkTempDir()
Python - join(a, b)
Python - absolutePath(path)
Python - realPath(path)
Python - getFiles(path)
Python - removePath(path)
Python - removeDir(path)
Python - cwd()
Python - ensureArray(val)
Python - collectFiles(searchPaths, extensions, exclusions)
Python - collectAllFiles(searchDir)
Javascript - runPython(pythonFile)
Python - isWindows()

Functions to Remove:
Python - getParentPID() >> Shepherd
Python - killJobProcesses >> Shepherd
