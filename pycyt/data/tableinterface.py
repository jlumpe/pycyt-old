import numpy as np
import pandas as pd

from flowframe import FlowFrame


class TableInterface(object):
	"""
	Takes some table-like object and wraps it in an interface that exposes it
	as a 2d array with a given number of columns. Used for convenience methods
	that operate on pycyt.FlowFrames, pandas.DataFrames, np.ndarrays, etc.
	equally.

	Either a list of column names or a column count can be given. Explicit
	column names define a mapping from the columns of the wrapped table to
	the columns of the .data array exposed by the interface. If the table
	has any additional mapped columns, they simply are not exposed (but are
	maintained when getting rows from the wrapped table or replacing data
	in it). If only a column count is given, this simply enforces that the
	wrapped table must have that many columns. If column names are given
	for a table object that does not have any kind of column labels, it just
	fixes the number of columns.

	Wrappable objects and their interpretation as tables:
		pycyt.FlowFrame - channels as columns, events as rows
		pandas.DataFrame - the obvious one
		pandas.Series - table with single column
		numpy.ndarray (2D) - table with rows in first axis and columns in 2nd
		numpy.ndarray (1D) - table with single column

	Shouldn't try modifying the wrapped table like this, the .data
	property is likely returning a copy instead of a view.
	"""

	def __init__(self, table, columns=None):

		self._table = table

		# Process column names
		if isinstance(columns, list):
			if not all(isinstance(cname, basestring) for cname in columns):
				raise TypeError('Column names must be string')
			if not len(set(columns)) == len(columns):
				raise ValueError('Column names must be unique')
			self._column_names = columns
			self._ncol = len(columns)

		elif columns is None:
			self._column_names = None
			self._ncol = None

		else:
			self._column_names = None
			self._ncol = int(columns)

		# FlowFrame
		if isinstance(table, FlowFrame):
			self._type = 'flowframe'
			self._nrow = self._table.tot
			if self._column_names is not None:
				if not all(cn in table.channels for cn in self._column_names):
					raise KeyError(
						'Column names do not match channels in {0}'
						.format(repr(table))
						)
			else:
				self._column_names = table.channels
				if self._ncol is None:
					self._ncol = table.par
				elif self._ncol != table.par:
					raise ValueError(
						'Number of columns does not match number of channels '
						'in {0}'
						.format(repr(table))
						)

		# Pandas DataFrame
		elif isinstance(table, pd.DataFrame):
			self._type = 'pd.dataframe'
			self._nrow = self._table.shape[0]
			if self._column_names is not None:
				if not all(cn in table.columns for cn in self._column_names):
					raise KeyError(
						'Column names do not match columns in DataFrame')
			else:
				self._column_names = table.columns
				if self._ncol is None:
					self._ncol = table.shape[1]
				elif self._ncol != table.shape[1]:
					raise ValueError(
						'Number of columns in DataFrame does not match')

		# Pandas Series
		elif isinstance(table, pd.Series):
			self._type = 'pd.series'
			self._nrow = len(self._table)
			if self._ncol is None:
				self._ncol = 1
			elif self._ncol != 1:
				raise ValueError(
					'pandas.Series cannot be interpreted as a table with '
					'more than one column.')

		# Numpy array
		elif isinstance(table, np.ndarray):

			# 2D array
			if table.ndim == 2:
				self._type = '2darray'
				self._nrow = self._table.shape[0]
				if self._ncol is None:
					self._ncol = table.shape[1]
				elif table.shape[1] != self._ncol:
					raise ValueError(
						'Number of columns in array does not match')

			# 1D array
			elif table.ndim == 1:
				self._type = '1darray'
				self._nrow = len(self._table)
				if self._ncol is None:
					self._ncol = 1
				elif self._ncol != 1:
					raise ValueError(
						'1D array cannot be interpreted as table with more '
						'than one column.')

			# Bad shape
			else:
				raise ValueError('Array must be 1 or 2-dimensional')

		# Bad type
		else:
			raise TypeError(
				'Value must be table or array-like, not {0}'
				.format(type(table)))

	@property
	def table(self):
		return self._table

	@property
	def type(self):
		return self._type

	@property
	def ncol(self):
		return self._ncol

	@property
	def nrow(self):
		return self._nrow

	@property
	def shape(self):
		return (self._nrow, self._ncol)

	@property
	def column_names(self):
		return self._column_names

	@property
	def data(self):
		"""
		Gets the table data as a two-dimensional numpy.ndarray
		"""
		if self._type == 'flowframe':
			if self._column_names is None:
				return self._table.data.values
			else:
				return self._table[self._column_names].values

		elif self._type == 'pd.dataframe':
			if self._column_names is None:
				return self._table.values
			else:
				return self._table[self._column_names].values
			
		elif self._type == 'pd.series':
			return self._table.values[:, np.newaxis]

		elif self._type == '2darray':
			return self._table

		elif self._type == '1darray':
			return self._table[:, np.newaxis]

		else:
			raise AssertionError() # shouldn't happen

	def __getitem__(self, index):
		return self.data[index]
	
	def get_rows(self, rows):
		"""
		Gets a subset of rows (given by integer index, slice object,
		array/series of integer indices or booleans) of the wrapped table, as
		the same type.
		"""
		if np.isscalar(rows):
			rows = [rows]

		if self._type == 'flowframe':
			return self._table.filter(rows)

		elif self._type in ['pd.dataframe', 'pd.series']:
			indexed = self._table.iloc[rows]
			if indexed.values.base is self._table.values.base and\
					indexed.values.base is not None:
				indexed = indexed.copy()
			return indexed

		elif self._type == '2darray':
			indexed = self._table[rows, :]
			if indexed.base is self._table.base and indexed.base is not None:
				indexed = indexed.copy()
			return indexed

		elif self._type == '1darray':
			indexed = self._table[rows]
			if indexed.base is self._table.base and indexed.base is not None:
				indexed = indexed.copy()
			return indexed

		else:
			raise AssertionError() # shouldn't happen
	
	def get_rows(self, rows):
		"""
		Gets a subset of rows (given by integer index, slice object,
		array/series of integer indices or booleans) of the wrapped table, as
		the same type.
		"""
		if np.isscalar(rows):
			rows = [rows]

		if self._type == 'flowframe':
			return self._table.filter(rows)

		elif self._type in ['pd.dataframe', 'pd.series']:
			indexed = self._table.iloc[rows]
			if indexed.values.base is self._table.values.base and\
					indexed.values.base is not None:
				indexed = indexed.copy()
			return indexed

		elif self._type == '2darray':
			indexed = self._table[rows, :]
			if indexed.base is self._table.base and indexed.base is not None:
				indexed = indexed.copy()
			return indexed

		elif self._type == '1darray':
			indexed = self._table[rows]
			if indexed.base is self._table.base and indexed.base is not None:
				indexed = indexed.copy()
			return indexed

		else:
			raise AssertionError() # shouldn't happen

	def with_data(self, data, rows=None):
		"""
		Returns a table of the same type as the wrapped table, with different
		data substituted in. Note that if the interface is not exposing all
		columns in the table, these columns will be present unmodified in the
		result.
		"""
		# Check data
		data = np.asarray(data)
		if data.ndim != 2 or data.shape[1] != self._ncol:
			raise ValueError('Data does not have compatible shape')
		if rows is None and data.shape[0] != self.nrow:
			raise ValueError(
				'Cannot get table with differing number of rows without '
				'specifying which ones to replace')

		# For FlowFrame or DataFrame, will have to account for different
		# column order as well as columns that are not mapped
		if self._type in ['flowframe', 'pd.dataframe']:

			# If no column mapping defined, easy - no data needs to be
			# replaced and columns are in same order
			if self._column_names is None:

				if self._type == 'flowframe':
					return FlowFrame(data, channels=self._table.channels)
				else:
					return pd.DataFrame(data, columns=self._table.columns)

			# Otherwise will have to account for mapped columns
			else:

				# Data already in the table
				if self._type == 'flowframe':
					prev_data = self._table.data.values
				else:
					prev_data = self._table.values

				# Subset of rows
				if rows is not None:
					prev_data = prev_data[rows]

				# Get copy of data to avoid modifying original
				new_data = prev_data.copy()

				# Copy column data
				for ci, cname in enumerate(self._column_names):
					if self._type == 'flowframe':
						table_ci = self._table.channels.index(cname)
					else:
						table_ci = list(self._table.columns).index(cname)
					new_data[:,table_ci] = data[:,ci]

				# Create and return new table object
				if self._type == 'flowframe':
					return FlowFrame(new_data, channels=self._table.channels)
				else:
					return pd.DataFrame(new_data, columns=self._table.columns)
			
		# For the remainder it is trivial
		elif self._type == 'pd.series':
			return pd.Series(data[:, 0])

		elif self._type == '2darray':
			return data

		elif self._type == '1darray':
			return data[:, 0]

		else:
			raise AssertionError() # shouldn't happen
