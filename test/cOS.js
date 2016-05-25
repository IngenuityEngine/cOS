

// Vendor Modules
/////////////////////////
var _ = require('lodash')
var expect = require('expect.js')
var describe = global.describe
var it = global.it
// var path = require('path')
// var fs = require('fs')
// var path = require('path')

// Our Modules
/////////////////////////

describe('cOS', function() {

	var cOS
	var searchPaths, extension

	it('should load', function() {
		cOS = require('../cOS/cOS')
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
		function cb(err, files)
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
		function cb(err, files)
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
		function cb(err, files)
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
		expect(upDir).to.be('c:/')
		upDir = cOS.upADir('c:/')
		expect(upDir).to.be('c:/')
		upDir = cOS.upADir('etc/')
		expect(upDir).to.be('etc/')
	})

	it('should collectFilenamesSync', function(done) {
		var searchPath = cOS.join(__dirname, 'test/test-cOS')
		cOS.collectFilenamesSync(searchPath)
		done()
	})

	it ('should runCommand', function(done){
		cOS.runCommand('ls', function(out, err, exitCode)
		{
			console.log(out)
			expect(out).to.contain('LICENSE\nREADME.md')
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

	it ('should unixPath', function(done) {
		expect(cOS.unixPath('\\path//to\\\\file')).to.be('/path/to/file')
		expect(cOS.unixPath('//\\path//to\\\\file\\\\\\')).to.be('/path/to/file/')
		expect(cOS.unixPath('\\\\\\\\//path\\to///\\/\\\\file\\/\\/\\\\//\\\\//')).to.be('/path/to/file/')
		done()
	})

	it ('should universalPath', function(done) {
		var univ = cOS.universalPath('Q:/path/to/file/')
		expect(univ).to.be('$root/path/to/file/')
		done()
	})

	it ('should fileExtension', function(done) {
		expect(cOS.getExtension('test.txt')).to.be('txt')
		expect(cOS.getExtension('/path/to/file.html')).to.be('html')
		expect(cOS.getExtension('/path/to/file/with/no/extension')).to.be('')
		done()
	})

	it ('should removeExtension', function(done) {
		expect(cOS.removeExtension('text.txt')).to.be('text')
		expect(cOS.removeExtension('/path/to/file.html')).to.be('/path/to/file')
		expect(cOS.removeExtension('/path/to/file/with/no/extension')).to.be('/path/to/file/with/no/extension')
		done()
	})

	it ('should getConvertFile', function(done) {
		expect(cOS.getConvertFile('test.txt')).to.be('test_convert.nk')
		expect(cOS.getConvertFile('/path/to/file.html')).to.be('/path/to/file_convert.nk')
		expect(cOS.getConvertFile('/path/to/file/with/no/extension')).to.be('/path/to/file/with/no/extension_convert.nk')
		done()
	})

	it ('should getVersion', function(done) {
		expect(cOS.getVersion('test_v001.txt')).to.be(1)
		expect(cOS.getVersion('test_v100')).to.be(100)
		expect(cOS.getVersion('test_v0421894.txt')).to.be(421894)
		expect(cOS.getVersion('test_v001.txt')).to.be(1)
		expect(cOS.getVersion('test/v012/filev012')).to.be(12)
		done()
	})

	it ('should incrementVersion', function(done) {
		expect(cOS.incrementVersion('filev002')).to.be('filev003')
		expect(cOS.incrementVersion('filev009')).to.be('filev010')
		expect(cOS.incrementVersion('/path/v002/filev002')).to.be('/path/v003/filev003')
		done()
	})

	it ('should padLeft', function(done) {
		expect(cOS.padLeft('16', '0', 4)).to.be('0016')
		expect(cOS.padLeft('142', '0', 3)).to.be('142')
		expect(cOS.padLeft('1717', '0', 2)).to.be('1717')
		done()
	})

	it ('should getFrameRange', function(done) {
		cOS.mkdir('seq')
		for (var i = 0; i < 10; i+=1)
			cOS.runCommand('touch', 'seq/filev' + cOS.padLeft(String(i + 1510), '0', 4))
		var info = cOS.getFrameRange('seq/filev%04d')
		expect(info.min).to.be(1510)
		expect(info.max).to.be(1519)
		cOS.runCommand('rm', ['-rf, seq'])
		done()
	})
})