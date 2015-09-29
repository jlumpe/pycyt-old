import os
import re

import numpy as np
import pandas as pd

from pycyt.io import FCSFile
from pycyt.util import pd_index_positions


class FlowFrame(object):
	"""
	A container for flow data. Has all the basic attributes of an FCS file,
	but may or may not actually be backed by one on the disk. Suports lazy
	loading of data from file only when accessed. This class has the same
	name as the equivalent in the Bioconductor R package because I am
	uncreative.

	Public attributes:
		ID: str (read-only property). (Probably unique) string identifier
			assigned at object creation.
		data: pandas.DataFrame. The most important one. A pandas DataFrame
			with events as rows and channels as columns. Is assignable as long
			as the new dataframe has the same columns and column names.
		filepath: str|None (read-only property): If backed by a file on disk,
			absolute path to that file.
		fcsfile: pyct.io.FCSFile|None (read-only property). If backed by file
			on disk, the FCSFile instance describing that file.
		lazy: bool. Whether data is lazy-loaded from disk when accessed.
		keywords: dict (read-only property): FCS keywords and values.
		par: int (read-only property): Number of parameters/channels
		channels: pandas.DataFrame (read-only property): Data frame with
			channels in rows and all $Pn? FCS keywords in columns. Matches
			actual keyword values if FlowFrame is from file, otherwise
			populated automatically.
		channel_names: list of str (read-only property): $PnN property
			for each channel.
		tot: int|long (read-only property): Total number of events, rows of
			data matrix.

	Public methods:
		copy(): Creates a new DataFrame with copy of this one's data.
		filter(): Creates a new DataFrame with subset of this one's
			rows/events. Supports several indexing methods.

	"""

	# Keep track of next automatic numeric ID
	_next_ID = 1

	def __init__(self, from_, **kwargs):
		"""
		Flexible constructor from several different types. Additional
		arguments vary based on value of the first:

		Common args:
			ID: str, optional. String ID for FlowFrame. If not given one will
			be created automatically.

		From file path:
			from_: str. Path to FCS file to load.
			lazy: bool, optional. If true, data will be loaded from file every
				time it is accessed instead of being stored in memory.
				Defaults to False.
			comp: None|numpy.ndarray|"auto", optional. Compensation matrix to
				be applied to data when loading from file. If given explicitly
				must be square array with size matching number of columns. If
				"auto" the matrix will be calculated from the spillover matrix
				in the file if it is present. If the file has no spillover
				matrix no compensation will be performed. Defaults to None.

		From FCSFile:
			from_: FCSFile instance. Works similarly to giving file path.
			All arguments identical to loading from file path.

		From numpy.ndarray:
			from_: numpy.ndarray, two-dimensional. Data with events in
				rows and channels in columns.
			channels: list of str. Unique names of channels, same length as
				size of second dimension of array.

		From pandas.DataFrame:
			from_: pands.DataFrame with events in rows and channels as
				columns.
		"""

		# Get ID if given
		if 'ID' in kwargs:
			ID = kwargs.pop('ID')
			if not isinstance(ID, basestring):
				raise TypeError('ID must be string')
		else:
			ID = None

		# From file path
		if isinstance(from_, basestring):
			fcsfile = FCSFile(from_)
			self._init_from_file(fcsfile, **kwargs)

		# From FCSFile object
		elif isinstance(from_, FCSFile):
			self._init_from_file(from_, **kwargs)

		# From numpy.ndarray
		elif isinstance(from_, np.ndarray):
			self._init_from_array(from_, **kwargs)

		# From pandas.DataFrame
		elif isinstance(from_, pd.DataFrame):
			self._init_from_dataframe(from_, **kwargs)

		# Bad argument
		else:
			raise TypeError(
				'Invalid type for "from_" argument: {0}'
				.format(type(from_)))

		# Figure out default ID if needed
		if ID is None:
			if self.filepath is not None:
				self._ID = os.path.splitext(os.path.basename(
					self.filepath))[0]
			else:
				self._ID = self._auto_ID()
		else:
			self._ID = ID

	def _init_from_file(self, fcsfile, lazy=False, comp=None):

		# Basic attributes
		self._fcsfile = fcsfile
		self._lazy = lazy

		self._par = self._fcsfile.par
		self._channel_names = self._fcsfile.channel_names

		# Comp argument for FCSFile.read_data()
		if isinstance(comp, np.ndarray):
			if comp.shape != (fcsfile.par, fcsfile.par):
				raise ValueError('Compensation matrix has incompatible shape')
			compensation = comp
		elif comp == 'auto':
			if self._fcsfile.spillover is not None:
				compensation = True
			else:
				compensation = False
		elif comp is None:
			compensation = False
		else:
			raise ValueError(
				'Invalid value for comp argument: {0}'
				.format(comp))

		# Load data now if not lazy
		if self._lazy:
			self._data = None
			self._compensation = compensation
		else:
			self._data = self._load_data(comp=compensation)
			self._compensation = False

	def _init_from_array(self, array, channels=None):

		# Check array
		if array.ndim != 2:
			raise ValueError('Array must be two-dimensional')

		# Check channels
		if channels is None:
			raise ValueError(
				'Channels argument required when creating from numpy.ndarray')
		channels = list(map(str, channels))
		if len(channels) != array.shape[1]:
			raise ValueError('Number of channels must match array dimensions')
		if len(set(channels)) != len(channels):
			raise ValueError('Channel names must be unique')

		# Create DataFrame
		self._channel_names = channels
		self._data = pd.DataFrame(array, columns=self._channel_names)
		self._par = int(self._data.shape[1]) # from long

		# Not backed by file
		self._fcsfile = None
		self._lazy = False
		self._compensation = False

	def _init_from_dataframe(self, dataframe):

		# Everything is in the DataFrame
		self._data = dataframe
		self._channel_names = list(self._data.columns)
		self._par = int(self._data.shape[1]) # from long

		# Not backed by file
		self._fcsfile = None
		self._lazy = False
		self._compensation = False

	@property
	def ID(self):
		return self._ID

	@property
	def data(self):
		if self._lazy:
			return self._load_data()
		else:
			return self._data

	@data.setter
	def data(self, value):
		"""Allow assignment with pandas.DataFrame or numpy.ndarray"""
		if self._lazy:
			raise AttributeError('Cannot set data when lazy-loading enabled')

		if isinstance(value, np.ndarray):
			if value.ndim != 2 or value.shape[1] != self._par:
				raise ValueError('Data array must have compatible shape')
			self._data = pd.DataFrame(value.copy(),
				columns=self._channel_names)

		elif isinstance(value, pd.DataFrame):
			if tuple(value.columns) != tuple(self._channel_names):
				raise ValueError('DataFrame must have identical columns')
			self._data = value.copy()

		else:
			raise TypeError(value)

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

	def __getitem__(self, idx):
		"""
		Convenience method for indexing the data attribute. Supports several
		argument types:
			Channel indexing:
				string: Gets data for single channel as pandas.Series.
				list of strings: Filter subset of channels.
			Row/Event indexing:
				int: single row/event
				slice: slices row range with standard slice behavior
				pandas.Series: either integer dtype to select rows by index or
					bool dtype to select rows where index is True.
				numpy.ndarray: 1D, with same behavior as pandas.Series
				list of int or bool: same behavior as pandas.Series
			Mixed indexing:
				tuple: 2-tuple of row index and channel index. In this case
					row index must match above. Channel index can match above,
					or be int or list of ints to get channels by position.
					This is based off of indexing of a data.frame in R.

		Returns:
			pandas.DataFrame, or pandas.Series if single channel selected.
		"""
		# String - single channel
		if isinstance(idx, basestring):
			return self.data[idx]

		# List - ambiguous, need to check contents
		elif isinstance(idx, list):

			# Of strings - subset of channels
			if isinstance(idx[0], basestring):
				return self.data[idx]

			# Otherwise assume ints or bools to index rows
			else:
				return pd_index_positions(self.data, idx)

		# Tuple - rows and channels
		elif isinstance(idx, tuple):

			rows, channels = idx

			# Get correct channels first
			if isinstance(channels, basestring): # Channel name
				df = self.data[channels]
			elif isinstance(channels, (int, long)): # Channel index
				df = self.data[self._channel_names[channels]]
			elif isinstance(channels, list):
				if isinstance(channels[0], basestring): # List of names
					df = self.data[channels]
				elif isinstance(channels[0], (int, long)): # List of indices
					df = self.data[[self._channel_names[i] for i in channels]]
				else:
					raise TypeError(
						'Second index must contain channel names or '
						'positions')
			elif channels is None:
				df = self.data
			else:
				raise TypeError(
					'Second index must contain channel names or positions')

			# Now index rows
			if rows is None:
				return df
			else:
				return pd_index_positions(df, rows)

		# Other - assume int, pandas.Series or numpy.ndarray
		else:
			return pd_index_positions(self.data, idx)

	def copy(self, ID=None):
		"""
		Creates a new FlowFrame with copy of this one's data. The copy will
		not be linked to the same FCS file.

		Args:
			ID: ID of newly created FlowFrame.

		Returns:
			pycyt.FlowFrame
		"""
		if ID is None:
			match = re.match(r'^(.*-copy)(\d*)$', self._ID)
			if match is not None:
				ID = match.group(1) + str(int(match.group(2) or 1) + 1)
			else:
				ID = self._ID + '-copy'
		return FlowFrame.from_dataframe(self.data.copy(), ID=ID)

	def filter(self, which, **kwargs):
		"""
		Creates a new FlowFrame from a *subset* of this one's events. The
		data is copied (changing the new data wont' affect the old) and the
		new FlowFrame won't be linked to the same FCS file.

		Args:
			which: One of several types, which different behavior for each:
				int: single row/event
				slice: slices row range with standard slice behavior
				pandas.Series: either integer dtype to select rows by index or
					bool dtype to select rows where index is True.
				numpy.ndarray: 1D, with same behavior as pandas.Series
				list: same behavior as pandas.Series
			**kwargs: Additional named arguments to pass to FlowFrame
				constructor when creating from pandas.DataFrame

		Returns:
			pycyt.FlowFrame
		"""
		# Get data (if lazy loading, want to avoid accessing this attribute
		# twice)
		data = self.data

		# Get filtered data frame
		df = pd_index_positions(data, which)

		# Some indexing methods return a *view* on the original data, meaning
		# changes to one will affect the other. We don't want this.
		if df.values.base is data.values.base:
			df = df.copy()

		# Reset indices to sequential integers
		df.index = xrange(df.shape[0])

		# Create from DataFrame and any additional arguments
		return FlowFrame(df, **kwargs)

	@classmethod
	def _auto_ID(cls):
		"""Automatically creates a unique ID string for a new instance"""
		ID = cls.__name__ + str(cls._next_ID)
		cls._next_ID += 1
		return ID

	def _load_data(self, comp=None):
		"""Loads data from linked fcs file into pandas.DataFrame"""
		if comp is None:
			comp = self._compensation
		matrix = self._fcsfile.read_data(fmt='matrix',
			comp=comp)
		return pd.DataFrame(matrix, columns=self._channel_names)
