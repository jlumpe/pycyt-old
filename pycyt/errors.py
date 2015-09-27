"""Package-specific errors"""


class FCSReadError(IOError):
	"""
	Raised when reading an FCS file and something doesn't go as expected.
	"""

	def __init__(self, msg=None, path=None):
		"""Generic default message, optionall with path of file"""
		if msg is None:
			msg_template = 'Error reading {0}, file may be corrupt'
			if path is not None:
				msg = msg_template.format('"{0}"'.format(path))
			else:
				msg = msg_template.format('FCS file')

		super(FCSReadError, self).__init__(msg)
