
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

// Our Modules
/////////////////////////
// var helpers = require('coren/shared/util/helpers')

// cOS
/////////////////////////
var cOS = module.exports = {


/*
	Method: ensureEndingSlash

	Ensures that the path has a trailing '/'
*/
ensureEndingSlash: function(path)
{
	// no need for an ending slash if there's no directory
	if (path.length < 1)
		return path

	var lastChar = path[path.length - 1]
	path = path.substr(0, path.length - 1)

	if (lastChar == '/' || lastChar == '\\')
		return path + '/'
	else
		return path + lastChar + '/'
},


/*
	Method: removeStartingSlash

	Removes backslashes and forward slashes from the beginning of directory names.
*/
removeStartingSlash: function(dir)
{
	if (dir[0] == '\\' || dir[0] == '/')
		dir = dir.substr(1)
	return dir
},

/*
	Method: normalizeDir

	Dirs always use forward slashses, don't have a leading slash, and have a trailing slash.
*/
normalizeDir: function(dir)
{
	dir = dir.replace(/\\/g,'/')
	if (cOS.isWindows())
		dir = cOS.removeStartingSlash(dir)
	return cOS.ensureEndingSlash(dir)
},


/*
	Method: isDirSync

	Checks if a path is a directory. (Synchronous)
*/
isDirSync: function(path)
{
	try {
		var stats = fs.statSync(path)
		return stats.isDirectory()
	} catch (err) {
		return false
	}
},

isFileSync: function(path)
{
	try {
		var stats = fs.statSync(path)
		return stats.isFile()
	} catch (err) {
		return false
	}
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
	Method: validEmptyDirSync

	Returns an object describing whether a directory is an existing directory (valid), and if it contains files (hasFiles).
*/
validEmptyDirSync: function(dir)
{
	var exists = fs.existsSync(dir)
	if (exists)
	{
		if (cOS.isDirSync(dir))
		{
			var files = fs.readdirSync(dir)
			if (files.length)
			{
				return {valid: true, hasFiles: true}
			}
			return {valid: true}
		}
		else
		{
			return {
					valid: false,
					error: 'Dir: ' + dir + ' exists but is not a directory'
				}
		}
	}
	else
	{
		var rootDir = cOS.upADir(dir)
		if (!cOS.isDirSync(rootDir))
			return {
					valid: false,
					error:'Root dir: ' + rootDir + ' does not exists'
				}
		fs.mkdirSync(dir)
		return {valid: true}
	}
},
/*
	Method: normalizePath

	Removes starting slash, and replaces all backslashes with forward slashses.
*/
normalizePath: function(path)
{
	if (cOS.isWindows())
		path = cOS.removeStartingSlash(path)
	return path.replace(/\\/g,'/')
},

// cOS.join that always joins with forward slash
// fix: should accept a bunch of paths
/*
	Method: join

	Concatenates a directory with a file path using forward slashes.
*/
join: function(a, b)
{
	return cOS.normalizeDir(a) + cOS.normalizePath(b)
},

// wrap cOS.dirname w/ normalize
dirname: function(file)
{
	return cOS.normalizeDir(path.dirname(file))
},

/*
	Method: getFileInfo

	Returns object with file's basename, extension, name, dirname and path.
	With options, can also return root, relative dirname, and relative path, and
	make all fields lowercase.
*/
getFileInfo: function(file, options)
{
	var fileInfo = {}

	options = options || {}
	_.defaults(options, {
			lowercaseNames: false
		})

	fileInfo.basename = path.basename(file)
	fileInfo.extension = path.extname(file)
	fileInfo.name = path.basename(file, fileInfo.extension)
	fileInfo.dirname = cOS.normalizeDir(path.dirname(file))
	fileInfo.path = cOS.normalizePath(path.normalize(file))

	// fix: relative path could be improved but it's a start
	if (options.root)
	{
		fileInfo.root = cOS.normalizePath(path.normalize(options.root))
		fileInfo.relativeDirname = cOS.normalizeDir(fileInfo.dirname.replace(fileInfo.root, ''))
		fileInfo.relativePath = cOS.normalizePath(fileInfo.path.replace(fileInfo.root, ''))
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
	Method: absolutePath

	Returns absolute path of a given path.
*/
absolutePath: function(path)
{
	return cOS.join(cOS.cwd(), path)
},

/*
	Method: realPathSync

	Returns the normalized real path. (Synchronous)
*/
realPathSync: function(path)
{
	return cOS.normalizePath(fs.realpathSync(path))
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

// wrap cOS.readFile so we don't have to specify utf8 all the time
/*
	Method: readFile

	Wrapper of fs.readFile so that utf8 doesn't need to be specified always.
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


unlinkSync: function(path)
{
	if (fs.existsSync(path))
		return fs.unlinkSync(path)
	return false
},

/*
	Method: removeDirSync

	Wrapper of fs.rmdir.
*/
// removeDirSync: function(path)
// {
// 	path = cOS.normalizePath(path)
// 	fs.removeSync(path)
// },
removeDirSync: function(path)
{
	path = cOS.normalizePath(path)
	var files = cOS.getFilesSync(path)
	_.each(files, function(file)
	{
		var curPath = path + '/' + file
		// recurse or
		if(fs.statSync(curPath).isDirectory())
			cOS.removeDirSync(curPath)
		// delete file
		else
			cOS.removePath(curPath)
	})
	fs.rmdirSync(path)
},

removeDir: function(path, callback)
{
	path = cOS.normalizePath(path)
	fs.remove(path, callback)
},

remove: function(path, callback)
{
	path = cOS.normalizePath(path)
	fs.remove(path, callback)
},

removeSync: function(path)
{
	path = cOS.normalizePath(path)
	fs.removeSync(path)
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

/*
	Method: emptyDirSync

	Removes all files and subdirectories from a directory.
*/
emptyDirSync: function(path)
{
	path = cOS.normalizePath(path)
	fs.emptyDirSync(path)
},

emptyDir: function(path, callback)
{
	path = cOS.normalizePath(path)
	fs.emptyDir(path, callback)
},

/*
	Method: cwd

	Returns the current working directory.
*/
cwd: function()
{
	return cOS.normalizeDir(process.cwd())
},


// fix: should fail gracefully
// build: function(options, callback)
// {
// 	if (_.isFunction(options))
// 	{
// 		callback = options
// 		options = {}
// 	}

// 	console.log('Searching:')
// 	_.each(options.searchPaths, function(path)
// 	{
// 		console.log(path)
// 	})
// 	console.log('\nFor:', options.extensions)

// 	_.defaults(options, {
// 										asString: true,
// 										lowercaseNames: false
// 									})


// 	async.waterfall(
// 		[
// 			function(cb) {
// 				cOS.collectFiles(options.searchPaths, options.extensions, options, cb)
// 			},
// 			function(allFiles, cb) {
// 				cOS.build(allFiles, templateManager.compile, options, cb)
// 			}
// 		], callback)
// },

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

// fix: should fail gracefully
// fix: should be async
/*
	Method: collectFilesSync

	Synchronous version of collectFiles.
*/
collectFilesSync: function(searchPath, extension, files, options)
{
	if (!_.isArray(files))
		files = []

	if (!_.isObject(options))
		options = {}

	// set default options
	_.defaults(options, {
		getContents: true,
		encoding: 'utf8',
		exclude: []
	})
	// allow for multiple search paths
	if (_.isArray(searchPath))
	{
		_.each(searchPath, function(searchPath) {
			_.extend(files, cOS.collectFilesSync(searchPath, extension, files, options))
		})
	}
	// allow for multiple extensions
	else if (_.isArray(extension))
	{
		_.each(extension, function(extension) {
			_.extend(files, cOS.collectFilesSync(searchPath, extension, files, options))
		})
	}
	// otherwise get files and return
	else if (typeof searchPath == 'string')
	{
		if (!fs.existsSync(searchPath))
			return false
		searchPath = fs.realpathSync(searchPath)
		searchPath = cOS.ensureEndingSlash(searchPath)
		var filter = '*' + extension
		var excludes = '/**/'

		// only exclude if we have a valid exclude array
		if (options.exclude &&
			_.isArray(options.exclude) &&
			options.exclude.length)
			excludes = '!(' + options.exclude.join('|') + ')/**/'

		var rootMatches = glob.sync(searchPath + filter)
		var extendedMatches = glob.sync(searchPath + excludes + filter)
		var matchingFiles = rootMatches.concat(extendedMatches)


		// debug('Searching:', searchPath, 'Filter:', filter)
		var fileInfo
		options.root = searchPath
		_.each(matchingFiles, function infoAndExclude(file)
		{
			// bail if any of the excludes is found in the list
			if (cOS.shouldExclude(options.exclude, file))
				return

			fileInfo = cOS.getFileInfo(file, options)
			// fix: should have async option
			if (options.getContents)
			{
				fileInfo.contents = fs.readFileSync(file, options.encoding)
			}
			files.push(fileInfo)
		})
	}
	return files
},

shouldExclude: function(excludes, path)
{
	var exclude = false
	_.each(excludes, function(str)
	{
		if (exclude || path.indexOf(str) != -1)
			exclude = true
	})
	return exclude
},

/*
	Method: compileFiles

	Compiles files given a compileFunction and options

	Parameters:

		files - List of files to be compiled
		compileFunction - function used to compile files
		options - options to be forwarded to the compileFunction
		callback - a callback function
*/
compileFiles: function(files, compileFunction, options, callback)
{
	if (_.isFunction(options))
	{
		callback = options
		options = {}
	}

	var compiledFiles = []
	var compileFuncs = _.map(files, function(fileInfo)
	{
		return function(done)
		{
			// debug('Compiling:', fileInfo.path)
			try
			{
				fileInfo.contents = compileFunction(fileInfo.contents, fileInfo, options)
				compiledFiles.push(fileInfo)
			}
			catch (err)
			{
				// done(Error('Compile failed for file:\n\n' + fileInfo.path + '\n\n' + err))
				throw Error('Compile failed for file:\n\n' + fileInfo.path + '\n\n' + err.stack)
			}
			done()
		}
	})
	async.parallel(
		compileFuncs,
		function(err)
		{
			callback(err, compiledFiles)
		}
	)
},

/*
	Method: collectFilenamesSync

	Synchronous wrapper for glob.sync.
*/
collectFilenamesSync: function(search)
{
	return glob.sync(search)
},



getUserHome: function()
{
	var userHome = process.env.HOME || process.env.HOMEPATH || process.env.USERPROFILE
	return cOS.normalizeDir(userHome)
},

copySync: function(src, dst)
{
	return copysync(src, dst)
},

copy: function(src, dst, callback)
{
	fs.copy(src, dst, callback)
},

createFolder: function(pathName, callback)
{
	fs.ensureDir(pathName, callback)
},

createFolderSync: function(pathName)
{
	fs.ensureDirSync(pathName)
},


// Methods
/////////////////////////

///////////////////// Normalization Operations \\\\\\\\\\\\\\\\\\\\\\\\

/*
	Method: unixPath

	Changes backslashes to forward slashes and removes successive slashes, ex \\ or \/
*/
unixPath: function(dir)
{
	return dir.replace(/[\\/]+/g, '/')
},

/*
	Method: universalPath

	Swaps Universal Root (Q:/) with unix root ($root).
	fix: CURRENTLY HARD CODED UNIVERSAL_ROOT TO BE $root.
*/
universalPath: function(dir)
{
	dir = dir.toLowerCase()
	return cOS.unixPath(dir).replace('q:', '$root')
},

/*
	Method: osPath

	Swaps unix root ($root) with Universal Root (Q:/)
*/
osPath: function(dir)
{
	return dir.replace('$root', 'Q:/')
},


///////////////////////////// Extension Operations ////////////////////////////////

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
removeExtension: function(path) {
	return path.replace(/\.[^/.]+$/, '')
},

/*
	Method: fileExtention

	Returns file extension of a file (without the '.').
*/
fileExtension: function(path)
{
	path = path.split('.')
	if (path.length > 1) return path.pop()
	else return ''
},

/*
	Method: getConvertFile

	Creates convert file by removing file extension, and appending '_convert.nk'.
*/
getConvertFile: function(path)
{
	return cOS.removeExtension(path) + '_convert.nk'
},

//////////////////////// Versioning Operations ///////////////////////////

/*
	Method: padLeft

	Pads a given string <str> to the left with <padString> to create a string of length <length>.
	This exists because javasript does not support string formatting to use %03d.
*/
padLeft: function(str, padString, length)
{
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
	return filename.replace(/[vV][0-9]+/g, 'v' + cOS.padLeft(String(version), '0', 3))
},

////////////////////////// Information Retrieval /////////////////////////////

/*
	Method: getDir

	Returns directory name of a file with a trailing '/'.
*/
getDir: function(filename)
{
	return cOS.normalizeDir(path.dirname(filename))
},

/*
	Method: getFrameRange

	Returns an object with 'min' (minFrame), 'max' (maxFrame), 'base' (fileName), and 'ext' (ext).

	Parameters:
		path - Generic file in sequence. Ex. text/frame.%04d.exr
*/
getFrameRange: function(path)
{
	var baseInFile = cOS.getFileInfo(path).basename
	var ext = '.' + cOS.getExtension(path)

	var percentLoc = baseInFile.indexOf('%')

	if (percentLoc == -1) throw "Frame padding not found in " + path

	var padding = parseInt(baseInFile.charAt(percentLoc + 2), 10)

	var minFrame = 9999999
	var maxFrame = -9999999

	var frame
	_.each(fs.readdirSync(cOS.getDir(path)), function(x)
	{
		frame = +(x.substr(percentLoc, padding))
		console.log(frame)
		if (!isNaN(frame))
		{
			maxFrame = Math.max(maxFrame, frame)
			minFrame = Math.min(minFrame, frame)
		}
	})

	return {
		'min' : minFrame,
		'max' : maxFrame,
		'base' : baseInFile,
		'ext': ext}
},

///////////////////////////// System Operations //////////////////////////////

/*
	Method: setEnvironmentVariable

	Sets a given environment variable for the OS.

	Parameters:
		key - environment variable
		val - value for the environment variable

*/
setEnvironmentVariable: function(key, val)
{
	val = String(val)
	process.env[key] = val
	child_process.exec('setx ' + key + '"' + val + '"')
},


/*
	Method: mkdir

	Wrapper for fs.mkdir.
*/
mkdir: function(dirname) {
	if (! cOS.isDirSync(dirname)) {
		fs.mkdir(dirname)
	}
},



/*
	Method: removePathSync

	Removes a file. (Synchronous)
*/
removePathSync: function(path)
{
	if (fs.existsSync(path))
		return fs.unlinkSync(path)
	return false
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
	Method: getFileContents

	Uses readFile to get the contents of a file.
*/
getFileContents: function(fileInfos, options, callback)
{
	if (_.isFunction(options))
	{
		callback = options
		options = {}
	}

	fileInfos = cOS.ensureArray(fileInfos)
	var contentsFuncs = _.map(fileInfos, function(fileInfo)
	{
		return function(cb)
		{
			cOS.readFile(fileInfo.path, options, function(err, data)
			{
				if (err)
					return cb(err)
				fileInfo.contents = data
				cb()
			})
		}
	})
	async.parallel(contentsFuncs,
		function(err)
		{
			callback(err, fileInfos)
		})
},

// fix: remove eventually
/*
	Method: ensureArray

	If input is an array, return input.  If not, makes it an array.  If undefied, returns [].
*/
ensureArray: function(val)
{
	if (_.isArray(val))
		return val
	if (_.isUndefined(val))
		return []
	return [val]
},
/*
	Method: ensureExtension

	Checks that a given file has the given extension.  If not, appends the extension.
*/
ensureExtension: function(filename, extension)
{
	extension = cOS.normalizeExtension(extension)
	if (cOS.getExtension(filename) != extension)
		return filename + extension
	return filename
},
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
	// if they didnt' pass options
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
	searchPaths = cOS.ensureArray(searchPaths)
	extensions = cOS.ensureArray(extensions)

	function globFiles(searchPath, extension, options, callback)
	{
		var filter = '**/' + extension
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
				if (cOS.contains(options.exclude, file))
					return
				fileInfo = cOS.getFileInfo(file, options)
				files.push(fileInfo)
			})
			callback(null, files)
		}
		glob(searchPath + filter, finishedMatching)
	}

	var searchFuncs = []
	_.each(searchPaths,
		function createFuncs(searchPath)
		{
			searchPath = cOS.normalizeDir(searchPath)
			_.each(extensions, function getForExtensions(extension)
			{
				extension = '*' + cOS.normalizeExtension(extension)

				// add a new search func, called later by async
				searchFuncs.push(function(done)
				{
					globFiles(searchPath, extension, options,
						function(err, files)
						{
							if (err && !options.skipSearchPathsOK)
								done(new Error('cOS.collectFiles -> Search path not found: ' +
									cOS.cwd() + searchPath + err.stack))
							else
								done(null, files)
						})
				})
			})
		})

	async.parallel(
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
	Method: contains

	Returns whether or not to exclude a given path, given an iterable of paths to exclude.
*/
contains: function(excludes, path)
{
	var exclude = false
	_.each(excludes, function(str)
	{
		if (exclude || path.indexOf(str) != -1)
			exclude = true
	})
	return exclude
},

/*
	Method: runPython

	Executes a given python file.
	fix: globalSettings.PYTHON currently hardcoded.
*/
// runPython: function(pythonFile)
// {
// 	var PYTHON = 'C:/Python27/python.exe'
// 	return child_process.exec(PYTHON, [pythonFile])
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
