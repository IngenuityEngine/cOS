import sys, os
import subprocess

sys.path.append(
	os.path.abspath(
		os.path.join(
			os.path.dirname(os.path.realpath(__file__)),
			'../cOS/')
		)
	)

import cOS

import ieInit
ieInit.init()

import settingsManager
globalSettings = settingsManager.globalSettings()

import unittest

class cOSTest(unittest.TestCase):

	def setUp(self):
		os.system('mkdir sandbox')
		os.system('touch sandbox/file_v001.mb')
		os.system('touch sandbox/file.mb')
		os.mkdir('sandbox/sandboxSubdir')
		os.system('touch sandbox/sandboxSubdir/file1.txt')
		os.mkdir('sandbox/testdir1')
		os.mkdir('sandbox/testdir2')
		os.system('touch sandbox/testdir1/file1')
		os.system('touch sandbox/testdir1/file2')
		os.system('touch sandbox/testdir1/file3')
		os.system('touch sandbox/testdir2/file1')
		os.mkdir('sandbox/seq')
		os.mkdir('sandbox/emptyDir')
		for i in range(10):
			os.system('touch sandbox/seq/frame.%04d.exr' % (i + 1510))

	def tearDown(self):
		os.system('rm -rf sandbox')

	def test_mkdir(self):
		cOS.mkdir('testDir')
		self.assertTrue(os.path.isdir('testDir'))
		os.system('rmdir testDir')

	def test_getExtension(self):
		ext = cOS.getExtension('file_v001.mb')
		self.assertEqual(ext, 'mb')

	def test_getVersion(self):
		ver = cOS.getVersion('sandbox/file_v001.mb')
		self.assertEqual(ver, 1)

	def test_getVersionError(self):
		ver = cOS.getVersion('sandbox/file.mb')
		self.assertEqual(ver, 0)

	def test_incrementVersion(self):
		ver = cOS.incrementVersion('sandbox/file_v001.mb')
		self.assertEqual(cOS.getVersion(ver), 2)

	def test_getDir(self):
		dirname = cOS.getDir('sandbox/file.mb')
		self.assertEqual(dirname, 'sandbox/')

	def test_checkTempDir(self):
		cOS.checkTempDir()
		self.assertTrue(os.path.isdir(globalSettings.TEMP))

	def test_emptyDir(self):
		cOS.emptyDir('sandbox/')
		self.assertTrue(not subprocess.check_output(['ls', 'sandbox']).split())

	def test_getFileInfo(self):
		info = cOS.getFileInfo('sandbox/file_v001.mb')
		self.assertEqual(info['extension'], 'mb')
		self.assertEqual(info['dirname'], 'sandbox/')
		self.assertEqual(info['basename'], 'file_v001.mb')
		self.assertEqual(info['filename'], 'sandbox/file_v001.mb')
		self.assertEqual(info['filebase'], 'file_v001')

	def test_removeExtension(self):
		stripped = cOS.removeExtension('sandbox/file_v001.mb')
		self.assertEqual(stripped, 'sandbox/file_v001')

	def test_removeExtensionNoExtension(self):
		stripped = cOS.removeExtension('path/to/file')
		self.assertEqual(stripped, 'path/to/file')

	def test_unixPath(self):
		prepped = cOS.unixPath('\\sandbox\\file_v001.mb')
		self.assertEqual(prepped, '/sandbox/file_v001.mb')

	def test_universalPath(self):
		uni = cOS.universalPath('Q:/test_file')
		self.assertEqual(uni, globalSettings.UNIVERSAL_ROOT + 'test_file')

	def test_osPath(self):
		os = cOS.osPath('$root/test_file')
		self.assertEqual(os, globalSettings.ROOT + 'test_file')

	def test_ensureEndingSlash(self):
		normalized = cOS.ensureEndingSlash('path/to/dir')
		self.assertEqual(normalized, 'path/to/dir/')

	def test_duplicateDir(self):
		cOS.duplicateDir('sandbox/testdir1', 'sandbox/testdir2')
		dir2Files = subprocess.check_output(['ls', 'sandbox/testdir2']).split()
		self.assertEqual(len(dir2Files), 3)
		self.assertTrue('file1' in dir2Files)
		self.assertTrue('file2' in dir2Files)
		self.assertTrue('file3' in dir2Files)

	def test_getConvertFile(self):
		converted = cOS.getConvertFile('sandbox/file_v001.mb')
		self.assertEqual(converted, 'sandbox/file_v001_convert.nk')

	def test_genArgs(self):
		args = cOS.genArgs({'k1': 'v1', 'k2' : 'v2', 'k3' : 'v3'})
		self.assertEqual(args, '-k3 v3 -k2 v2 -k1 v1')

	def test_getFrameRange(self):
		info = cOS.getFrameRange('sandbox/seq/frame.%04d.exr')
		self.assertEqual(info['min'], 1510)
		self.assertEqual(info['max'], 1519)

	def test_removeStartingSlash(self):
		res = cOS.removeStartingSlash('/path/to/file')
		self.assertEqual(res, 'path/to/file')

	def test_normalizeDir(self):
		res = cOS.normalizeDir('/path\\to/file')
		self.assertEqual(res, 'path/to/file/')

	def test_normalizeExtension(self):
		norm = cOS.normalizeExtension('Mb')
		self.assertEqual(norm, 'mb')
		norm = cOS.normalizeExtension('.mb')
		self.assertEqual(norm, 'mb')

	def test_upADir(self):
		parent = cOS.upADir('path/to/a/file/')
		self.assertEqual(parent, 'path/to/a/')
		parent = cOS.upADir('path/to/a/file.txt')
		self.assertEqual(parent, 'path/to/')

	def test_isDir(self):
		isDir = cOS.isDir('sandbox')
		self.assertTrue(isDir)
		isDir = cOS.isDir('DOESNTEXIST')
		self.assertTrue(not isDir)

	def test_join(self):
		joined = cOS.join('/path/to/a/directory', '/path/to/a/file.txt')
		self.assertEqual(joined, 'path/to/a/directory/path/to/a/file.txt')

	def test_absolutePath(self):
		absPath = cOS.absolutePath('sandbox')
		self.assertEqual(absPath, 'c:/ie/cOS/test/sandbox/')

	def test_getFiles(self):
		files = cOS.getFiles('sandbox')
		self.assertEqual(set(files), set(['emptyDir', 'seq', 'file_v001.mb', 'file.mb', 'testdir1', 'testdir2', 'sandboxSubdir']))

	def test_removePath(self):
		self.assertTrue(os.path.isfile('sandbox/file.mb'))
		cOS.removePath('sandbox/file.mb')
		self.assertTrue(not os.path.isfile('sandbox/file.mb'))
		ret = cOS.removePath('sandbox/file.mb')
		self.assertTrue(not ret)

	def test_removeDir(self):
		self.assertTrue(os.path.isdir('sandbox/emptyDir'))
		cOS.removeDir('sandbox/emptyDir')
		self.assertTrue(not os.path.isdir('sandbox/emptyDir'))
		ret = cOS.removeDir('sandbox/emptyDir')
		self.assertTrue(not ret)

	def test_cwd(self):
		cwd = cOS.cwd()
		self.assertEqual(cwd, 'c:/ie/cOS/test/')

	def test_ensureArray(self):
		self.assertEqual(cOS.ensureArray([1,2,3]), [1,2,3])
		self.assertEqual(cOS.ensureArray('abc'), ['abc'])
		self.assertEqual(cOS.ensureArray(None), [])
		self.assertEqual(cOS.ensureArray((1,2,3)), [1,2,3])

	def test_collectFiles(self):
		os.system('rm -rf seq')
		files = cOS.collectFiles('sandbox', 'mb', '')
		self.assertEqual(sorted(files), sorted([cOS.getFileInfo(f) for f in ['sandbox/file_v001.mb', 'sandbox/file.mb']]))
		#self.assertEqual(set(files), set([cOS.getFileInfo(f) for f in ['sandbox/file_v001.mb', 'sandbox/file.mb', 'sandbox/testdir1/file1', 'sandbox/testdir1/file2', 'sandbox/testdir1/file3', 'sandbox/testdir2/file1']]))
		files = cOS.collectFiles('sandbox', 'mb', 'sandbox/file_v001.mb')
		self.assertEqual(sorted(files), sorted([cOS.getFileInfo(f) for f in ['sandbox/file.mb']]))

	def test_collectAllFiles(self):
		files = cOS.collectAllFiles('sandbox/testdir2')
		self.assertEqual(sorted(files), sorted([cOS.getFileInfo(f) for f in ['sandbox/testdir2/file1']]))

	def test_isWindows(self):
		self.assertTrue(cOS.isWindows())

if __name__ == '__main__':
	unittest.main()