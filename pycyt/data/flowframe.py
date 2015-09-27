import re

import numpy as np

from pycyt.io import FCSFile


class FlowFrame(object):
	"""
	A container for flow data. Has all the basic attributes of an FCS file,
	but may or may not actually be backed by one on the disk. Suports lazy
	loading of data from file only when accessed. This class has the same
	name as the equivalent in the Biocondutor R package because I am
	uncreative.

	This class generally shouldn't be instantiated directly, instead the class
	methods from_file() or from_array() should be used.

	Public attributes:
		ID: str (read-only property). (Probably unique) string identifier
			assigned at object creation.
		data: numpy.ndarray. The most important one. An array of shape
			(tot, par). Is assignable as long as the new array has a shape
			compatible with the number of channels.
		filepath: str|None (read-only property): If backed by a file on disk,
			absolute path to that file.
		fcsfile: pyct.io.FCSFile|None (read-only property). If backed by file
			on disk, the FCSFile instance describing that file.
		lazy: bool. Whether data is lazy-loaded from disk when accessed.
		keywords: dict (read-only property): FCS keywords and values.
		par: int (read-only property): Number of paramters/channels
		channels: pandas.DataFrame (read-only property): Data frame with
			channels in rows and all $Pn? FCS keywords in columns. Filled in
			automatically if 
		channel_names: list of str (read-only property): $PnN property
			for each channel.
		tot: int|long (read-only property): Total number of events, rows of
			data matrix.

	Public methods:
		from_file (class method): Create from a file on disk
		from_array (class method): Create from numpy.ndarray
	"""

	# Keep track of next automatic numeric ID
	_next_ID = 1

	def __init__(self, from_, **kwargs):
		"""Don't use this directly"""
		# From FCS file
		if from_ == 'fcsfile':

			self._fcsfile = kwargs['fcsfile']
			self._lazy = kwargs['lazy']

			self._par = self._fcsfile.par
			self._channel_names = self._fcsfile.channel_names

			if self._lazy:
				self._data = None
			else:
				self._data = self._fcsfile.read_data(fmt='matrix')

		# From array
		elif from_ == 'array':

			self._fcsfile = None
			self._lazy = False

			self._data = kwargs['array']
			self._channel_names = kwargs['channels']

			self._par = int(self._data.shape[1]) # from long

		else:
			raise ValueError(from_)

		if kwargs.get('ID') is not None:
			self._ID = kwargs['ID']
		else:
			self._ID = self._auto_ID()

	@classmethod
	def from_file(cls, path, lazy=False, ID=None):
		"""
		Create from FCS file on disk.

		Args:
			path: str. Path to FCS file.
			lazy: bool. If true, data will be loaded from file every time it
				is accessed instead of being stored in memory.
			ID: str|None. String ID for FlowFrame. If none one will be created
				automatically.

		Returns:
			pycyt.FlowFrame
		"""
		fcsfile = FCSFile(path)
		return cls('fcsfile', fcsfile=fcsfile, lazy=lazy, ID=ID)

	@classmethod
	def from_array(cls, array, channels, ID=None):
		"""
		Create from numpy.ndarray and channel names

		Args:
			array: numpy.ndarray, two-dimensional.
			channels: list of str. Unique names of channels, same length as
				size of second dimension of array.
			ID: str|None. String ID for FlowFrame. If none one will be created
				automatically.

		Returns:
			pycyt.FlowFrame
		"""
		if not isinstance(array, np.ndarray):
			raise TypeError('Array must be numpy.ndarray')
		if array.ndim != 2:
			raise ValueError('Array must be two-dimensional')

		channels = list(map(str, channels))
		if len(channels) != array.shape[1]:
			raise ValueError('Number of channels must match array dimensions')
		if len(set(channels)) != len(channels):
			raise ValueError('Chanel names must be unique')

		return cls('array', array=array, channels=channels, ID=ID)

	@property
	def ID(self):
		return self._ID

	@property
	def data(self):
		if self._lazy:
			return self._fcsfile.read_data(fmt='matrix')
		else:
			return self._data

	@data.setter
	def data(self, value):
		if self._lazy:
			raise AttributeError('Cannot set data when lazy-loading enabled')
		if not isinstance(value, np.ndarray):
			raise TypeError('Data must be numpy.ndarray')
		if value.ndim != 2 or value.shape[1] != self._par:
			raise ValueError('Data array must have compatible shape')
		self._data = value

	@property
	def filepath(self):
		if self._fcsfile is not None:
			return self._fcsfile.filepath
		else:
			return None

	@property
	def fcsfile(self):
		return self._fcsfile
	
	@property
	def lazy(self):
		return self._lazy

	@lazy.setter
	def lazy(self, value):
		if not self._fcsfile:
			raise AttributeError(
				'Lazy attribute only assignable if FlowFrame backed by FCS '
				'file')
		if type(value) is not bool:
			raise TypeError(value)
		if self._lazy is False and value is True:
			self._lazy = True
			self._data = None # Should be garbage collected and free memory
		if self._lazy is True and value is False:
			self._lazy = False
			self._data = self._fcsfile.read_data(fmt='matrix')

	@property
	def keywords(self):
		if self._fcsfile is not None:
			return self._fcsfile.keywords
		else:
			return None # TODO

	@property
	def par(self):
		return self._par

	@property
	def channels(self):
		if self._fcsfile is not None:
			return self._fcsfile.channels
		else:
			return None # TODO

	@property
	def channel_names(self):
		return self._channel_names
	
	@property
	def tot(self):
		if self._lazy:
			return self._fcsfile.tot
		else:
			return self._data.shape[0]

	def __repr__(self):
		return '<{0} {1}>'.format(type(self).__name__, repr(self._ID))

	def copy(self, ID=None):
		"""
		Creates a new FlowFrame with copy of this one's data. The copy will
		not be linked to the same FCS file.
		"""
		if ID is None:
			match = re.match(r'^(.*-copy)(\d*)$', self._ID)
			if match is not None:
				ID = match.group(1) + str(int(match.group(2) or 1) + 1)
			else:
				ID = self._ID + '-copy'
		return FlowFrame.from_array(self.data.copy(), self.channel_names,
			ID=ID)

	@classmethod
	def _auto_ID(cls):
		"""Automatically creates a unique ID string for a new instance"""
		ID = cls.__name__ + str(cls._next_ID)
		cls._next_ID += 1
		return ID
