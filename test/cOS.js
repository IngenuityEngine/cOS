

// Vendor Modules
/////////////////////////
var _ = require('lodash')
var expect = require('expect.js')
// var path = require('path')
// var fs = require('fs')
// var path = require('path')

// Our Modules
/////////////////////////
var helpers = require('../shared/util/helpers')

var describe = helpers.getGlobal('describe')
var it = helpers.getGlobal('it')

describe('cOS', function() {

	var cOS
	var searchPaths, extension


	it('should load', function() {
		cOS = require('../server/cOS')
	})


	it ('should getFileInfo', function() {
		var options = {
			root: 'test'
		}
		var fileInfo = cOS.getFileInfo('test/test-cOS/four.js', options)

		var expectedInfo = {
			basename: 'four.js',
			extension: '.js',
			name: 'four',
			dirname: 'test/test-cOS/',
			path: 'test/test-cOS/four.js',
			root: 'test',
			relativeDirname: 'test-cOS/',
			relativePath: 'test-cOS/four.js'
		}
		expect(fileInfo).to.eql(expectedInfo)
	})

	it('should ensureEndingSlash', function() {
		expect(cOS.ensureEndingSlash('path/')).to.be('path/')
		expect(cOS.ensureEndingSlash('path')).to.be('path/')
		expect(cOS.ensureEndingSlash('path\\')).to.be('path/')
	})

	it('should normalizeDir', function() {
		expect(cOS.normalizeDir('some/path/')).to.be('some/path/')
		expect(cOS.normalizeDir('some/path')).to.be('some/path/')
		expect(cOS.normalizeDir('some\\path\\')).to.be('some/path/')
		expect(cOS.normalizeDir('some\\path')).to.be('some/path/')
		expect(cOS.normalizeDir('/some/path/')).to.be('some/path/')
		expect(cOS.normalizeDir('/some/path')).to.be('some/path/')
		expect(cOS.normalizeDir('\\some\\path\\')).to.be('some/path/')
		expect(cOS.normalizeDir('\\some\\path')).to.be('some/path/')
	})

	it('should normalizePath', function() {
		expect(cOS.normalizePath('some/path/file.js')).to.be('some/path/file.js')
		expect(cOS.normalizePath('some\\path\\file.js')).to.be('some/path/file.js')
		expect(cOS.normalizePath('/some/path/file.js')).to.be('some/path/file.js')
		expect(cOS.normalizePath('/some\\path\\file.js')).to.be('some/path/file.js')
	})

	it('should join', function() {
		expect(cOS.join('some/path/','file.js')).to.be('some/path/file.js')
		expect(cOS.join('some/path\\','file.js')).to.be('some/path/file.js')
		expect(cOS.join('/some/','/path/file.js')).to.be('some/path/file.js')
		expect(cOS.join('some\\','\\path\\file.js')).to.be('some/path/file.js')
	})

	it('should collectFiles', function(done) {
		searchPaths = ['test/test-cOS']
		extension = '.mustache'
		var cb = function (err, files)
		{
			if (err) throw err
			expect(files).to.be.a('object')
			expect(files.length).to.be(3)
			var names = _.pluck(files, 'basename')
			expect(names).to.eql(['one.mustache','two.mustache','three.mustache'])
			done()
		}
		cOS.collectFiles(searchPaths, extension, cb)
	})

	it('should collectFiles with exclusions', function(done) {
		searchPaths = ['test/test-cOS']
		extension = '.mustache'
		var cb = function (err, files)
		{
			if (err) throw err

			expect(files).to.be.a('object')
			expect(files.length).to.be(2)
			var names = _.pluck(files, 'basename')
			expect(names).to.eql(['one.mustache', 'three.mustache'])
			done()
		}
		cOS.collectFiles(searchPaths, extension, {exclude: ['two']}, cb)
	})

	it('should collectFiles searchPaths and extensions', function(done) {
		searchPaths = ['test/test-cOS/one/two/','test/test-cOS/three']
		extension = ['.mustache','.styl']
		var cb = function (err, files)
		{
			if (err) throw err
			expect(files).to.be.a('object')
			expect(files.length).to.be(3)
			var names = _.pluck(files, 'basename')
			expect(names).to.contain('two.mustache','three.mustache','three.styl')
			done()
		}
		cOS.collectFiles(searchPaths, extension, cb)
	})

	it('should get the cwd', function() {
		console.log(cOS.cwd())
	})

	it ('should upADir', function(){
		var upDir = cOS.upADir('c:/test/sub')
		expect(upDir).to.be('c:/test/')
		upDir = cOS.upADir('c:/')
		expect(upDir).to.be('c:/')
		upDir = cOS.upADir('etc/')
		expect(upDir).to.be('etc/')
	})

	it('should collectFilenames', function(done) {
		var searchPath = cOS.join(__dirname, 'test-cOS')
		cOS.collectFilenames(searchPath, function(err, result)
		{
			if (err)
				throw err
			console.log(result)
			done()
		})
	})

	it ('should runCommand', function(done){
		cOS.runCommand('ls', function(out, err, exitCode)
		{
			console.log(out)
			expect(out).to.contain('shared\ntest')
			expect(err).to.be('')
			expect(exitCode).to.be(0)
			done()
		})
	})

	it ('should getGlobalModulesDir', function(done){
		cOS.getGlobalModulesDir(function(err, path)
		{
			console.log('"' + path + '"')
			expect(path.length).to.be.ok()
			expect(err).to.be(false)
			done()
		})
	})
})
