
// Vendor Modules
/////////////////////////
var _ = require('lodash')
var fs = require('fs')
var os = require('os')
var path = require('path')
var glob = require('glob')
var child_process = require('child_process')
var copysync = require('copysync')
var async = require('async')
var mkdirp = require('mkdirp')
var rimraf = require('rimraf')

// Our Modules
/////////////////////////
// var helpers = require('coren/shared/util/helpers')


// Helpers
//////////////////////////////////////////////////
function ensureArray(val)
{
	if (_.isArray(val))
		return val
	if (_.isUndefined(val))
		return []
	return [val]
}

/*
Method: contains

Returns whether or not to exclude a given path,
given an iterable of paths to exclude.
*/
function contains(excludes, path)
{
	var exclude = false
	_.each(excludes, function(str)
	{
		if (exclude || path.indexOf(str) != -1)
			exclude = true
	})
	return exclude
}


// cOS
/////////////////////////
var cOS = module.exports = {


// Normalization
//////////////////////////////////////////////////

/*
Method: ensureEndingSlash

Ensures that the path has a trailing '/'
*/
ensureEndingSlash: function(path)
{
	path = cOS.unixPath(path)
	if (path.slice(-1) != '/')
		path += '/'
	return path
},

/*
Method: removeStartingSlash

Removes backslashes and forward slashes from the
beginning of directory names.
*/
removeStartingSlash: function(path)
{
	if (path[0] == '\\' || path[0] == '/')
		path = path.substr(1)
	return path
},

/*
Method: normalizeDir

Dirs always use forward slashses and have a trailing slash.
*/
normalizeDir: function(path)
{
	path = cOS.unixPath(path)
	return cOS.ensureEndingSlash(path)
},

/*
Method: normalizePath

Removes starting slash, and replaces all backslashes
with forward slashses.
*/
normalizePath: function(path)
{
	if (cOS.isWindows())
		path = cOS.removeStartingSlash(path)
	return path.replace(/\\/g,'/')
},

/*
Method: unixPath

Changes backslashes to forward slashes and removes successive slashes, ex \\ or \/
*/
unixPath: function(path)
{
	// lower case drive leters
	if (path.slice(1,2) == ':')
		path = path.slice(0,2).toLowerCase() + path.slice(2)
	return path.replace(/[\\/]+/g, '/')
},


// fix: missing unicodeToString
// unicodeToString: function(data)
// {
// 	return data
// },



// Extensions
//////////////////////////////////////////////////

/*
Method: getExtension

Returns file extension of a file (without the '.').
*/
getExtension: function(path)
{
	path = path.split('.')
	if (path.length > 1)
		return path.pop().toLowerCase()
	else
		return ''
},

/*
Method: normalizeExtension

Takes in an extension, and makes is lowercase, and precedes it with a '.'
*/
normalizeExtension: function(extension)
{
	extension = extension.toLowerCase().trim()
	if (extension[0] == '.')
		return extension.slice(1)
	return extension
},

/*
Method: removeExtension

Removes the extension from a path.  If there is no extension, returns ''
*/
removeExtension: function(filename)
{
	if (!_.includes(filename, '.'))
		return filename
	return filename.split('.').slice(0, -1).join('.')
},

/*
Method: ensureExtension

Checks that a given file has the given extension.  If not, appends the extension.
*/
ensureExtension: function(filename, extension)
{
	extension = cOS.normalizeExtension(extension)
	if (cOS.getExtension(filename) != extension)
		return filename + '.' + extension
	return filename
},



// Versioning
//////////////////////////////////////////////////

/*
Method: padLeft

Pads a given string with the pad character until
it's the given length
This exists because javasript does not support string
formatting to use %04d.
*/
padLeft: function(str, padString, length)
{
	str = String(str)
	while (str.length < length)
		str = padString + str;
	return str
},

/*
Method: getVersion

Returns version number of a given filename.
*/
getVersion: function(filename)
{
	var match = filename.match(/[vV][0-9]+/g)
	if (match.length > 0) return parseInt(match[0].substring(1), 10)
	return 0

},

/*
Method: incrementVersion

Returns file with version incremented in all locations in the name.
*/
incrementVersion: function(filename)
{
	var version = cOS.getVersion(filename) + 1
	return filename.replace(/[vV][0-9]+/g, 'v' + cOS.padLeft(version, '0', 3))
},


// fix: missing getHighestVersion
// getHighestVersion: function(root, extension)
// {

// },

// Information
//////////////////////////////////////////////////

/*
Method: getDir

Returns directory name of a file with a trailing '/'.
*/
getDirName: function(filename)
{
	return cOS.normalizeDir(path.dirname(filename))
},

/*
Method: upADir

Returns the path, up a single directory.
If being called on a directory, be sure the directory is normalized before calling.
*/
upADir: function(path)
{
	path = cOS.normalizeDir(path)
	var parts = path.split('/')
	if (parts.length < 3)
		return path
	return parts.slice(0, -2).join('/') + '/'
},

/*
Method: getPathInfo

Returns object with file's basename, extension, name, dirname and path.
With options, can also return root, relative dirname, and relative path, and
make all fields lowercase.
*/
getPathInfo: function(file, options)
{
	var fileInfo = {}

	options = options || {}
	_.defaults(options, {
			lowercaseNames: false
		})

	fileInfo.path = cOS.normalizePath(file)
	fileInfo.dirname = cOS.normalizeDir(path.dirname(file))
	fileInfo.basename = path.basename(file)
	fileInfo.extension = cOS.normalizeExtension(path.extname(file))
	fileInfo.name = fileInfo.basename.replace('.' + fileInfo.extension, '')
	fileInfo.filebase = fileInfo.path.replace('.' + fileInfo.extension, '')

	// fix: relative path could be improved but it's a start
	if (options.root)
	{
		fileInfo.root = cOS.normalizeDir(options.root)
		fileInfo.relativeDirname = './' + cOS.removeStartingSlash(cOS.normalizeDir(fileInfo.dirname.replace(fileInfo.root, '')))
		fileInfo.relativePath = './' + cOS.removeStartingSlash(cOS.normalizePath(fileInfo.path.replace(fileInfo.root, '')))
	}

	if (options.lowercaseNames)
	{
		_.each(fileInfo, function(val, key) {
			fileInfo[key] = val.toLowerCase()
		})
	}

	return fileInfo
},

/*
Method: getFrameRange


Returns a dictionary with min, max, duration,
base, ext, and complete

Parameters:
		path - Generic file in sequence. Ex. text/frame.%04d.exr
*/
getFrameRange: function(path)
{
	var baseInFile = cOS.getPathInfo(path).basename
	var ext = '.' + cOS.getExtension(path)

	var percentLoc = baseInFile.indexOf('%')

	if (percentLoc == -1)
	{
		console.error('Invalid padding:', path)
		return false
	}

	var padding = parseInt(baseInFile.charAt(percentLoc + 2), 10)

	var minFrame = 9999999
	var maxFrame = -9999999

	var frame
	var count = 0
	_.each(fs.readdirSync(cOS.getDirName(path)), function(path)
	{
		count += 1
		frame = parseInt(path.substr(percentLoc, padding), 10)
		maxFrame = Math.max(maxFrame, frame)
		minFrame = Math.min(minFrame, frame)
	})

	if (minFrame == 9999999 || maxFrame == -9999999)
		return false

	var duration = maxFrame - minFrame + 1
	return {
		min : minFrame,
		max : maxFrame,
		duration: duration,
		base : baseInFile,
		ext: ext,
		complete: duration == count
	}
},



// System Operations
//////////////////////////////////////////////////


/*
Method: setEnvironmentVariable

Sets a given environment variable for the OS.

Parameters:
	key - environment variable
	val - value for the environment variable
*/
// fix: needs to work for linux / osx
setEnvironmentVariable: function(key, val)
{
	val = String(val)
	process.env[key] = val
	child_process.exec('setx ' + key + '"' + val + '"')
},



/*
Method: makeDir

Wrapper for fs.mkdir.
*/
makeDir: function(dir, callback)
{
	fs.mkdir(dir, callback)
},


/*
Method: makeDir

Wrapper for fs.mkdir.
*/
makeDirSync: function(dir)
{
	try
	{
		fs.mkdirSync(dir)
		return true
	}
	catch (err)
	{
		return err
	}
},

/*
Method: makeDirs

Makes a directory. (Synchronous)
*/
makeDirs: function(path, callback)
{
	mkdirp(cOS.normalizeDir(path), callback)
},

/*
Method: makeDirsSync

Makes a directory. (Synchronous)
*/
makeDirsSync: function(path)
{
	try {
		return mkdirp.sync(cOS.normalizeDir(path))
	} catch (err) {
		return err
	}
},

// fix: should accept a bunch of paths
/*
Method: join

Concatenates a directory with a file path using forward slashes.
*/
join: function(a, b)
{
	return cOS.normalizeDir(a) + cOS.normalizePath(b)
},


/*
Method: getFilesSync

Lists files in a given path. (Synchronous)
*/
getFilesSync: function(path)
{
	path = cOS.normalizePath(path)
	if(fs.existsSync(path))
		return fs.readdirSync(path)
	return []
},

/*
Method: removeFile

Removes a file.
*/
removeFile: function(path, callback)
{
	fs.unlink(path, callback)
},

/*
Method: removeFileSync

Removes a file. (Synchronous)
*/
removeFileSync: function(path)
{
	try
	{
		return fs.unlinkSync(path)
	}
	catch (err)
	{
		return err
	}
},

/*
Method: removeDir

Removes a directory completely
*/
removeDir: function(path, callback)
{
	rimraf(path, callback)
},
/*
Method: removeDirSync

Wrapper of fs.rmdirSync, empties the folder
then removes the it.
*/
removeDirSync: function(path)
{
	try
	{
		rimraf.sync(path)
		return true
	}
	catch (err)
	{
		return err
	}
},

// fix: doesn't keep permissions, etc on original directory
emptyDir: function(path, callback)
{
	cOS.removeDir(path, function(err)
	{
		if (err)
			return callback(err)
		cOS.makeDir(path, callback)
	})
},
/*
Method: emptyDirSync

Removes all files and subdirectories from a directory.
*/
emptyDirSync: function(path)
{
	fs.emptyDirSync(path)
},

rename: function(oldPath, newPath, callback)
{
	oldPath = cOS.normalizePath(oldPath)
	newPath = cOS.normalizePath(newPath)
	fs.rename(oldPath, newPath, callback)
},

renameSync: function(oldPath, newPath)
{
	oldPath = cOS.normalizePath(oldPath)
	newPath = cOS.normalizePath(newPath)
	fs.renameSync(oldPath, newPath)
},

copy: function(src, dst, callback)
{
	fs.copy(src, dst, callback)
},

copySync: function(src, dst)
{
	return copysync(src, dst)
},

/*
Method: copyTreeSync

Wrapper of copysync.
*/
copyTreeSync: function(src, dst)
{
	return copysync(src, dst)
},

/*
Method: cwd

Returns the current working directory.
*/
cwd: function()
{
	return cOS.normalizeDir(process.cwd())
},

getUserHome: function()
{
	var userHome = process.env.HOME || process.env.HOMEPATH || process.env.USERPROFILE
	return cOS.normalizeDir(userHome)
},

// fix: missing duplicateDir

// duplicateDir: function(src, dst)
// {
// },


/*
Method: collectFiles

Gets all files in the searchPaths with given extensions.

Parameters:

	searchPaths - list of paths to search
	extensions - list of extensions for which to look
	options - object specifying root or exclusions
	callback - a callback function
*/
collectFiles: function(searchPaths, extensions, options, callback)
{
	// optional arguments
	if (_.isFunction(options))
	{
		callback = options
		options = {}
	}
	options = options || {}
	_.defaults(options, {
		exclude: []
	})

	// allow for multiple search paths and extensions
	searchPaths = ensureArray(searchPaths)
	extensions = ensureArray(extensions)

	function globFiles(searchPath, extension, options, callback)
	{
		var filter = '**/*.' + extension
		console.log('Searching:', searchPath, 'Filter:', filter)

		function finishedMatching(err, matchingFiles)
		{
			if (err)
				throw new Error('cOS.globFiles.finishedMatching: ' + err)

			// set root for relative paths in fileInfo
			options.root = searchPath
			var fileInfo
			var files = []
			_.each(matchingFiles, function infoAndExclude(file)
			{
				// console.log(file)
				if (contains(options.exclude, file))
					return
				fileInfo = cOS.getPathInfo(file, options)
				files.push(fileInfo)
			})
			callback(null, files)
		}
		glob(searchPath + filter, finishedMatching)
	}

	var searchFuncs = []
	_.each(searchPaths, function createFuncs(searchPath)
	{
		searchPath = cOS.normalizeDir(searchPath)
		_.each(extensions, function getForExtensions(extension)
		{
			extension = cOS.normalizeExtension(extension)

			// add a new search func, called later by async
			searchFuncs.push(function(done)
			{
				globFiles(searchPath, extension, options,
					function(err, files)
					{
						if (err && !options.skipSearchPathsOK)
						{
							done(new Error('cOS.collectFiles -> Search path not found: ' +
								cOS.cwd() + searchPath + err.stack))
						}
						else
						{
							done(null, files)
						}
					})
			})
		})
	})

	async.series(
		searchFuncs,
		function allSearched(err, results)
		{
			if (err)
				throw new Error('cOS.collectFiles.allSearched: ' + err.stack)

			var allFiles = []
			_.each(results, function(files)
			{
				allFiles = allFiles.concat(files)
			})

			callback(null, allFiles)
		}
	)
},


/*
Method: collectFilesSync

Synchronous wrapper for glob.sync.
*/
collectFilesSync: function(search)
{
	return glob.sync(search)
},


/*
	Method: collectAllFiles

	Returns all files within a specified searchDir.
*/
collectAllFiles: function(searchDir, callback)
{
	searchDir = cOS.normalizeDir(searchDir)
	function walk(dir, done)
	{
		var results = []
		fs.readdir(dir, function(err, list)
		{
			if (err)
				return done(err)
			var pending = list.length
			if (!pending)
				return done(null, results)
			_.each(list, function(file)
			{
				file = cOS.join(dir, file)
				fs.stat(file, function(err, stat)
				{
					if (stat && stat.isDirectory())
					{
						walk(file, function(err, res)
						{
							results = results.concat(res)
							pending -= 1
							if (!pending)
								done(null, results)
						})
					}
					else
					{
						results.push(file)
						pending -= 1
						if (!pending)
							done(null, results)
					}
				})
			})
		})
	}
	return walk(searchDir, callback)
},



// Processes
//////////////////////////////////////////////////

// fix: missing getParentPID
// getParentPID: function()
// {

// },


/*
Method: runCommand

Executes a given command with the arguments specified.

Parameters:

	cmd - Command to be executed
	args - List of arguments to that function
	options - options forwarded to child_process.spawn
	callback - callback function
*/
runCommand: function(cmd, args, options, callback)
{
	if (_.isFunction(args))
	{
		callback = args
		args = []
		options = {}
	}
	else if (_.isFunction(options))
	{
		callback = options
		options = {}
	}
	if (_.isString(args))
		args = [args]

	options = options || {}
	_.defaults(options, {
		cwd: process.cwd(),
		env: process.env,
		log: true
	})
	var out = ''
	var err = ''
	var child = child_process.spawn(cmd, args, options)
	// child.stdin.pipe(process.stdin)
	// child.stdout.pipe(process.stdout)
	// child.stderr.pipe(process.stderr)
	child.stdout.on('data', function(data)
		{
			// if (options.log)
			// 	console.log(String(data))
			out += data
		})
	child.stderr.on('data', function(data)
		{
			// if (options.log)
			// 	console.log(String(data))
			err += data
		})
	child.on('close', function(code)
		{
			if (callback)
				callback(err, out, code)
		})
	child.on('error', function(code)
		{
			if (callback)
				callback(err, out, code)
		})
},


runPython: function(pythonFile, options, callback)
{
	cOS.runCommand('python', [pythonFile], options, callback)
},


// IO
//////////////////////////////////////////////////
/*
Method: readFile

Wrapper of fs.readFile so we don't have to
specify utf8 all the time
*/
readFile: function(path, options, callback)
{
	if (_.isFunction(options))
	{
		callback = options
		options = {}
	}
	else
		options = options || {}

	_.defaults(options, {
			encoding: 'utf8'
		})
	fs.readFile(path, options, callback)
},


// OS
//////////////////////////////////////////////////

/*
Method: isWindows
*/
isWindows: function()
{
	return os.platform() == 'win32'
},

/*
Method: isLinux
*/
isLinux: function()
{
	return os.platform() == 'linux'
},
/*
Method: isMac
*/
isMac: function()
{
	return os.platform() == 'darwin'
},


// Command Line Utilities
//////////////////////////////////////////////////

// fix: breaks on single dash arguments, improve
// fix: use optimist or whatever when we're somewhere
// with docs and internet
// getArgs: function(args)
// {
// 	i = 1
// 	if not args:
// 		args = sys.argv
// 	options = {'__file__':args[0]}
// 	while (i < sys.argv.__len__() - 1):
// 		options[args[i].replace('-','').replace(':', '')] = args[i + 1]
// 		i += 2
// 	return options
// },


/*
Method: getGlobalModulesDir

Returns the directory of the global modules.
*/
getGlobalModulesDir: function(callback)
{
	var cmd = 'npm'
	if (cOS.isWindows())
		cmd = 'npm.cmd'
	cOS.runCommand(cmd, ['get','prefix'], function(err, out, code)
	{
		if (code !== 0 || err)
			return callback(err)
		// slice removes the \n
		var globalModulesDir = out.slice(0, -1) + '/'
		if (cOS.isLinux())
			globalModulesDir = '/' + globalModulesDir + 'lib/'

		callback(false, globalModulesDir)
	})
},

// end of module
}
