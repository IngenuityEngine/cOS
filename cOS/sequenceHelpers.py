import re

def getSequenceName(filename):
	regex_baseName = re.compile('(.+)[_\.][0-9]+\.[a-z]+')
	try:
		baseName = regex_baseName.search(filename).group(1)
		return baseName
	except:
		raise IndexError('The filename given does not follow the standard filename pattern for an image in a sequence.')

def getFrameNumber(fileName):
	nameParsed = re.split('[_\.]', fileName)
	try:
		frame = int(nameParsed[-2])
		return frame
	except:
		raise IndexError('The filename given does not have the format <name>_<frameNumber>.<extension> or <name>.<frameNumber>.<extension: %s' % filename)
