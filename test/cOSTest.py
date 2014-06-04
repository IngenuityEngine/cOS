import sys, os
import subprocess

sys.path.append(os.path.abspath('../cOS/'))
import cOS

import ieInit
ieInit.init()

import ieGlobals

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
		for i in range(10):
			os.system('touch sandbox/seq/frame.%04d.exr' % (i + 1510))


	def tearDown(self):
		os.system('rm -rf sandbox')


	def test_mkdir(self):
		cOS.mkdir('testDir')
		self.assertTrue(os.path.isdir('testDir'))
		os.system('rmdir testDir')

	def test_fileExtension(self):
		ext = cOS.fileExtension('file_v001.mb')
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
		self.assertTrue(os.path.isdir(ieGlobals.IETEMP))

	def test_emptyFolder(self):
		cOS.emptyFolder('sandbox/')
		self.assertTrue(not subprocess.check_output(['ls', 'sandbox']).split())

	def test_pathInfo(self):
		info = cOS.pathInfo('sandbox/file_v001.mb')
		self.assertEqual(info['extension'], 'mb')
		self.assertEqual(info['dirname'], 'sandbox/')
		self.assertEqual(info['basename'], 'file_v001.mb')
		self.assertEqual(info['filename'], 'sandbox/file_v001.mb')
		self.assertEqual(info['filebase'], 'file_v001')

	def test_stripExtension(self):
		stripped = cOS.stripExtension('sandbox/file_v001.mb')
		self.assertEqual(stripped, 'sandbox/file_v001')

	def test_stripExtensionNoExtension(self):
		stripped = cOS.stripExtension('path/to/file')
		self.assertEqual(stripped, 'path/to/file')

	def test_filePrep(self):
		prepped = cOS.filePrep('\\sandbox\\file_v001.mb')
		self.assertEqual(prepped, '/sandbox/file_v001.mb')

	def test_unixPath(self):
		prepped = cOS.unixPath('\\sandbox\\file_v001.mb')
		self.assertEqual(prepped, '/sandbox/file_v001.mb')

	def test_universalPath(self):
		uni = cOS.universalPath('Q:/test_file')
		self.assertEqual(uni, ieGlobals.UNIVERSAL_ROOT + 'test_file')

	def test_osPath(self):
		os = cOS.osPath('$root/test_file')
		self.assertEqual(os, ieGlobals.ROOT + 'test_file')

	def test_normalizeDir(self):
		normalized = cOS.normalizeDir('path/to/dir')
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

if __name__ == '__main__':
	unittest.main()