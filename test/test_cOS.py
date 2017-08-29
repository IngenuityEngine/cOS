
import os
import subprocess

import arkInit
arkInit.init()

import tryout
import cOS


class test(tryout.TestSuite):
	title = 'test/cOS.py'

	def setUp(self):
		os.system('rm -rf sandbox')
		os.mkdir('sandbox')
		open('sandbox/file_v001.mb', 'w')
		open('sandbox/file.mb', 'w')
		os.mkdir('sandbox/sandboxSubdir')
		open('sandbox/sandboxSubdir/file1.txt', 'w')
		os.mkdir('sandbox/testdir1')
		os.mkdir('sandbox/testdir2')
		open('sandbox/testdir1/file1', 'w')
		open('sandbox/testdir1/file2', 'w')
		open('sandbox/testdir1/file3', 'w')
		open('sandbox/testdir2/file1', 'w')
		os.mkdir('sandbox/seq')
		os.mkdir('sandbox/emptyDir')
		for i in range(10):
			open('sandbox/seq/frame.%04d.exr' % (i + 1510), 'w')

		open('sandbox/seq/newFrame.0001.exr', 'w')

	def tearDown(self):
		os.system('rm -rf sandbox')

	def makeDir(self):
		cOS.makeDir('testDir')
		self.assertTrue(os.path.isdir('testDir'))
		os.system('rmdir testDir')

	def getExtension(self):
		ext = cOS.getExtension('file_v001.mb')
		self.assertEqual(ext, 'mb')

	def getVersion(self):
		ver = cOS.getVersion('sandbox/file_v001.mb')
		self.assertEqual(ver, 1)

		ver = cOS.getVersion('654')
		self.assertEqual(ver, 654)

		ver = cOS.getVersion(27)
		self.assertEqual(ver, 27)


	def getVersionError(self):
		ver = cOS.getVersion('sandbox/file.mb')
		self.assertEqual(ver, 0)

	def incrementVersion(self):
		ver = cOS.incrementVersion('sandbox/file_v001.mb')
		self.assertEqual(cOS.getVersion(ver), 2)

	def getDirName(self):
		dirname = cOS.getDirName('sandbox/file.mb')
		self.assertEqual(dirname, 'sandbox/')

	def emptyDir(self):
		cOS.emptyDir('sandbox/')
		self.assertTrue(not subprocess.check_output(['ls', 'sandbox']).split())

	def getPathInfo(self):
		options = {'root': 'test'}
		info = cOS.getPathInfo('test/test-cOS/four.js', options)

		self.assertEqual(info['basename'], 'four.js')
		self.assertEqual(info['extension'], 'js')
		self.assertEqual(info['name'], 'four')
		self.assertEqual(info['dirname'], 'test/test-cOS/')
		self.assertEqual(info['path'], 'test/test-cOS/four.js')
		self.assertEqual(info['root'], 'test/')
		self.assertEqual(info['relativeDirname'], './test-cOS/')
		self.assertEqual(info['relativePath'], './test-cOS/four.js')
		self.assertEqual(info['filebase'], 'test/test-cOS/four')

	def removeExtension(self):
		stripped = cOS.removeExtension('sandbox/file_v001.mb')
		self.assertEqual(stripped, 'sandbox/file_v001')

	def removeExtensionNoExtension(self):
		stripped = cOS.removeExtension('path/to/file')
		self.assertEqual(stripped, 'path/to/file')

	def unixPath(self):
		prepped = cOS.unixPath('\\sandbox\\file_v001.mb')
		self.assertEqual(prepped, '/sandbox/file_v001.mb')

	def ensureEndingSlash(self):
		normalized = cOS.ensureEndingSlash('path/to/dir')
		self.assertEqual(normalized, 'path/to/dir/')
		normalized = cOS.ensureEndingSlash('http://some/url')
		self.assertEqual(normalized, 'http://some/url/')

	def duplicateDir(self):
		cOS.duplicateDir('sandbox/testdir1', 'sandbox/testdir2')
		dir2Files = subprocess.check_output(['ls', 'sandbox/testdir2']).split()
		self.assertEqual(len(dir2Files), 3)
		self.assertTrue('file1' in dir2Files)
		self.assertTrue('file2' in dir2Files)
		self.assertTrue('file3' in dir2Files)

	def genArgs(self):
		args = cOS.genArgs({'k1': 'v1', 'k2' : 'v2', 'k3' : 'v3'})
		self.assertEqual(args, '-k3 v3 -k2 v2 -k1 v1')

	def getFrameRange(self):
		info = cOS.getFrameRange('sandbox/seq/frame.%04d.exr')
		self.assertEqual(info['min'], 1510)
		self.assertEqual(info['max'], 1519)

	def validateFrameFile(self):
		frameText = cOS.getFirstFileFromFrameRangeText('sandbox/seq/frame.%04d.exr 1510-1519')
		self.assertEqual(frameText, 'sandbox/seq/frame.1510.exr')

		frameText = cOS.getFirstFileFromFrameRangeText('sandbox/seq/newFrame.%04d.exr')
		self.assertEqual(frameText, 'sandbox/seq/newFrame.0001.exr')

		frameText = cOS.getFirstFileFromFrameRangeText('sandbox/seq/frame.1510.exr')
		self.assertEqual(frameText, 'sandbox/seq/frame.1510.exr')

		frameText = cOS.getFirstFileFromFrameRangeText('sandbox/seq/frame.exr')
		self.assertEqual(frameText, False)


	def removeStartingSlash(self):
		res = cOS.removeStartingSlash('/path/to/file')
		self.assertEqual(res, 'path/to/file')

	def normalizeDir(self):
		res = cOS.normalizeDir('/path\\to/file')
		self.assertEqual(res, '/path/to/file/')

	def normalizeExtension(self):
		norm = cOS.normalizeExtension('some/path.ABC')
		self.assertEqual(norm, 'some/path.abc')
		norm = cOS.normalizeExtension('some/path.abc')
		self.assertEqual(norm, 'some/path.abc')
		norm = cOS.normalizeExtension('Some/Path with/spaces.ABC')
		self.assertEqual(norm, 'Some/Path with/spaces.abc')

	def upADir(self):
		parent = cOS.upADir('path/to/a/file/')
		self.assertEqual(parent, 'path/to/a/')
		parent = cOS.upADir('path/to/a/file.txt')
		self.assertEqual(parent, 'path/to/')

	def join(self):
		joined = cOS.join('/path/to/a/directory/', '/path/to/a/file.txt')
		self.assertEqual(joined, '/path/to/a/directory/path/to/a/file.txt')

	def getFiles(self):
		# fix: this test is pretty bad :\
		root = os.path.abspath(
			os.path.join(
				os.path.dirname(os.path.realpath(__file__)),
				'../')
			)
		print root

		print 'test one:'
		files = cOS.getFiles(root,
			fileIncludes='*.py',
			folderExcludes=['.git','node_modules'],
			filesOnly=True

		)
		print '\n'.join(files)
		self.assertTrue(len(files) > 4)
		self.assertTrue(len(files) < 10)

		print '\ntest two:'
		files = cOS.getFiles(root,
			fileIncludes=['__init__.py'],
			fileExcludes=['*'],
			filesOnly=True,
		)
		print '\n'.join(files)
		self.assertTrue(len(files) == 4)

		print '\ntest three:'
		files = cOS.getFiles(root,
			fileExcludes=['.*'],
			folderExcludes=['.*', 'node_modules'],
			filesOnly=True,
		)
		print '\n'.join(files)
		self.assertTrue(len(files) > 4)
		self.assertTrue(len(files) < 40)

		print '\ntest four:'
		files = cOS.getFiles(root,
			fileIncludes=[
				'*cOS/cOS/cOS.py',
				'*cOS/cOS/__init__.py',
			],
			fileExcludes=['*.py', '.git*'],
			folderExcludes=['.git','node_modules'],
			includeAfterExclude=True,
			filesOnly=True,
		)
		print '\n'.join(files)
		self.assertTrue(len(files) > 4)
		self.assertTrue(len(files) < 40)

	def removeFile(self):
		self.assertTrue(os.path.isfile('sandbox/file.mb'))
		cOS.removeFile('sandbox/file.mb')
		self.assertTrue(not os.path.isfile('sandbox/file.mb'))
		ret = cOS.removeFile('sandbox/file.mb')
		self.assertTrue(ret != True)

	def removeDir(self):
		self.assertTrue(os.path.isdir('sandbox/emptyDir'))
		cOS.removeDir('sandbox/emptyDir')
		self.assertTrue(not os.path.isdir('sandbox/emptyDir'))
		ret = cOS.removeDir('sandbox/emptyDir')
		self.assertTrue(ret != True)

	# fix: can't really test this as we don't know what the
	# directory should be
	# def cwd(self):
	# 	cwd = cOS.cwd()
	# 	self.assertTrue()

	def ensureArray(self):
		self.assertEqual(cOS.ensureArray([1,2,3]), [1,2,3])
		self.assertEqual(cOS.ensureArray('abc'), ['abc'])
		self.assertEqual(cOS.ensureArray(None), [])
		self.assertEqual(cOS.ensureArray((1,2,3)), [1,2,3])

	def collectFiles(self):
		os.system('rm -rf seq')
		files = cOS.collectFiles('sandbox', 'mb', '')
		self.assertEqual(sorted(files), sorted([cOS.getPathInfo(f) for f in ['sandbox/file_v001.mb', 'sandbox/file.mb']]))
		files = cOS.collectFiles('sandbox', 'mb', 'sandbox/file_v001.mb')
		self.assertEqual(sorted(files), sorted([cOS.getPathInfo(f) for f in ['sandbox/file.mb']]))

	def collectAllFiles(self):
		files = cOS.collectAllFiles('sandbox/testdir2')
		self.assertEqual(sorted(files), sorted([cOS.getPathInfo(f) for f in ['sandbox/testdir2/file1']]))

	def isWindows(self):
		self.assertTrue(cOS.isWindows())

	def getCommandOutput(self):
		out, err = cOS.getCommandOutput('jkfsdajkl')
		self.assertTrue(out == False)
		self.assertTrue(err)

		testFile = cOS.getDirName(os.path.realpath(__file__)) + \
			'testOutput/simple.py'
		out, err = cOS.getCommandOutput('python ' + testFile)
		print 'out:', out
		print 'err:', err
		self.assertTrue('hello world' in out)
		self.assertEqual(err, False)

	def normalizeFramePadding(self):
		self.assertEqual(cOS.normalizeFramePadding('C:/Trash/abc.####.png'), 'C:/Trash/abc.%04d.png')
		self.assertEqual(cOS.normalizeFramePadding('C:/Trash/abc_####.png'), 'C:/Trash/abc_%04d.png')
		self.assertEqual(cOS.normalizeFramePadding('C:/Trash/abc.$F6.png'), 'C:/Trash/abc.%06d.png')
		self.assertEqual(cOS.normalizeFramePadding('C:/Trash/abc_$F6.png'), 'C:/Trash/abc_%06d.png')
		self.assertEqual(cOS.normalizeFramePadding('C:/Trash/abc.%04d.png'), 'C:/Trash/abc.%04d.png')
		self.assertEqual(cOS.normalizeFramePadding('C:/Trash/abc.$F.png'), 'C:/Trash/abc.%d.png')
		self.assertEqual(cOS.normalizeFramePadding('C:/Trash/abc.21.png'), 'C:/Trash/abc.%d.png')
		self.assertEqual(cOS.normalizeFramePadding('C:/Trash/abc.p3q0#$93bhn.png'), 'C:/Trash/abc.p3q0#$93bhn.png')
		self.assertEqual(cOS.normalizeFramePadding('C:/Trash/abc.png'), 'C:/Trash/abc.png')

if __name__ == '__main__':
	tryout.run(test)
