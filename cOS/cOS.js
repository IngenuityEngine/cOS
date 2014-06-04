
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

// Methods
/////////////////////////



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

// dirs are always forward slashes and always have a trailing slash
/*
	Method: normalizeDir

	Dirs always use forward slashses, don't have a leading slash, and have a trailing slash.
*/
normalizeDir: function(dir)
{
	dir = dir.replace(/\\/g,'/')
	dir = cOS.removeStartingSlash(dir)
	return cOS.ensureEndingSlash(dir)
},

/*
	Method: isDirSync

	Checks if a method is a directory.
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

/*
	Method: makeDirsSync

	Makes a directory.
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

	Returns an object describing whether a directory is valid, and if it contains files.
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
// paths are always forward slashes
// fix: consider not removing starting slash for linux paths
/*
	Method: normalizePath

	Paths are always forward slashes.
*/
normalizePath: function(path)
{
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
/*
	Method: dirName

	Returns normalized directory name of a file.
*/
dirName: function(file)
{
	return cOS.normalizeDir(path.dirname(file))
},

/*
	Method: getFileInfo

	Returns object with file's basename, extension, dirname and path.
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
		_.each(fileInfo, function(val, key) { fileInfo[key] = val.toLowerCase() })
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

	Returns the normalized real path.
*/
realPathSync: function(path)
{
	return cOS.normalizePath(fs.realpathSync(path))
},

/*
	Method: getFilesSync

	Lists files in a given path.
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

/*
	Method: unlinkSync

	Removes a file.
*/
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
			fs.unlinkSync(curPath)
	})
	fs.rmdirSync(path)
},

/*
	Method: emptyDirSync

	Removes all files and subdirectories from a directory.
*/
emptyDirSync: function(path)
{
	path = cOS.normalizePath(path)
	var files = cOS.getFilesSync(path)
	_.each(files, function(file)
	{
		var curPath = path + '/' + file
		if(fs.statSync(curPath).isDirectory())
			cOS.removeDirSync(curPath)
		else
			fs.unlinkSync(curPath)
	})
},

/*
	Method: cwd

	Returns the current working directory.
*/
cwd: function()
{
	return cOS.normalizeDir(process.cwd())
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
	var contentsFuncs = _.collect(fileInfos, function(fileInfo)
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
	Method: normalizeExtension

	Makes extensions lowercase, and begin with a '.'
*/
normalizeExtension: function(extension)
{
	extension = extension.toLowerCase().trim()
	if (extension[0] != '.')
		return '.' + extension
	return extension
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
				if (cOS.shouldExclude(options.exclude, file))
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


		console.log('Searching:', searchPath, 'Filter:', filter)
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

/*
	Method: shouldExclude

	Returns whether or not to exclude a given path, given an iterable of paths to exclude.
*/
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
	var compileFuncs = _.collect(files, function(fileInfo)
	{
		return function(done)
		{
			// console.log('Compiling:', fileInfo.path)
			try
			{
				fileInfo.contents = compileFunction(fileInfo.contents, fileInfo, options)
				compiledFiles.push(fileInfo)
				done()
			}
			catch (err)
			{
				// done(Error('Compile failed for file:\n\n' + fileInfo.path + '\n\n' + err))
				throw Error('Compile failed for file:\n\n' + fileInfo.path + '\n\n' + err.stack)
			}
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
				callback(out, err, code)
		})
	child.on('error', function(code)
		{
			if (callback)
				callback(out, err, code)
		})
},

/*
	Method: isWindows

	Returns whether or not the machine running the command is Windows.
*/
isWindows: function()
{
	return _.contains(os.platform().toLowerCase(), 'win')
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
	cOS.runCommand(cmd, ['get','prefix'], function(out, err, code)
	{
		if (code !== 0 || err)
			return callback(err)
		// slice removes the \n
		callback(false, out.slice(0, -1))
	})
},

/*
	Method: copySync

	Wrapper of copysync.
*/
copySync: function(src, dst)
{
	return copysync(src, dst)
},

// end of module
}
