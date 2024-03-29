import sys
import os
import warnings

import pandas as pd
import numpy as np

from pycyt.errors import FCSReadError


class FCSFile(object):
	"""
	Represents an FCS file on disk

	Metadata is read, parsed, and validated immediately upon initialization.
	Actual data is read by the read_data method.

	Technically this was only written to support FCS version 3.1 files,
	but could work for others. Refer to FCS 3.1 specification in
	http://isac-net.org/PDFS/90/9090600d-19be-460d-83fc-f8a8b004e0f9.pdf

	Public attributes:
		filepath: str (read-only property): Absolute path to FCS file on disk.
		version: str (read-only property): FCS version of parsed file.
		text: dict (read-only property): Keywords and their values parsed from
			the TEXT segment.
		par: int (read-only property): Number of paramters, equal to value of
			$PAR keyword.
		channels: list of str (read-only property): $PnN property
			for each channel.
		channel_info: pandas.DataFrame (read-only property): Data frame with
			channels in rows and all $Pn? keywords in columns. Values are
			parsed versions of keyword values.
		tot: int (read-only property): Total number of events, equal to value
			of $TOT keyword.
		spillover: numpy.ndarray (read-only property): Parsed value of
			$SPILLOVER keyword, expanded and rearranged to cover all channels
			and in the correct order.

	Public methods:
		read_data: Reads the actual data from the file into a numpy.ndarray.
	"""

	def __init__(self, path):
		"""Creation from file path"""

		self._path = os.path.realpath(path)

		self._read_metadata()

	@property
	def filepath(self):
		return self._path
	
	@property
	def version(self):
		return self._version

	@property
	def text(self):
		return self._text

	@property
	def par(self):
		return self._par

	@property
	def channels(self):
		return list(self._channel_info['$PnN'])

	@property
	def channel_info(self):
		return self._channel_info
	
	@property
	def tot(self):
		return self._tot

	@property
	def spillover(self):
		return self._spillover

	def read_data(
			self,
			slice1=None,
			slice2=None,
			fmt='matrix',
			systype=True,
			comp=False):
		"""
		Reads data from the file. A slice of events may be selected.

		Args:
			slice1: int|None. If slice2 is none, number of events to read.
				If slice2 is given, first event to read. If none, read all
				events.
			slice2: int|none. If given, upper end of slice of events to read
				(exclusive). Like using [slice1:slice2] on a list.
			fmt: "matrix"|"events". Determines format of data returned.
				"matrix" is the default and is recommended for when $DATATYPE
				is "F", "D", or "I" with constant bytes per column. Use
				"events" for when you're operating outside the realm of logic
				and using differently-sized integer columns.
			systype: bool. If true, converts data types in memory to native
				ones for current system. Basically this means swapping the
				byte order if needed. This results in a dtype equivalent to
				one of np.float32, np.float64, np.uint8, np.uint16, np.uint32,
				or np.uint64. Only applies when fmt=="matrix".
			comp: bool|numpy.ndarray. Compensation matrix to apply to data.
				Matrix may be given explicitly as numpy ndarray (typically
				square, but technically just the number of rows needs to
				match the number of channels). If passed True, the matrix will
				be calculated as the pseudoinverse of the spillover matrix.
				If argument is false no compensation will be performed.

		Returns:
			numpy.ndarray. For fmt=="matrix", a two-dimensional array with
			events in rows and channels in columns. Data type is determined by
			the maximum-size data type of the columns (they can only be
			different when $DATATYPE is "I"). For fmt=="events", a 1-d array
			with one element per event. dtype is a numpy.void containing
			correct scalar dtype for each channel in order.
		"""

		# Begin and end events (inclusive/exclusive)
		if slice1 is None:
			event_range = (0, self._tot)
		else:
			if slice2 is None:
				event_range = (0,) + slice1
			else:
				event_range = (slice1, slice2)

		if event_range[0] < 0 or event_range[1] > self._tot:
			raise ValueError('Invalid slice: {0}'.format(event_range))

		# Number of events to read
		nevents = event_range[1] - event_range[0]

		# Bytes per event
		bytes_per_event = sum(self._channel_bytes)

		# Offset to start reading data at
		offset = self._offsets['DATA'][0] + bytes_per_event * event_range[0]
		if offset > self._offsets['DATA'][1] + 1:
			raise FCSReadError(
				'Error reading data from "{0}": data offset range '
				'inconsistent with $PnB and $TOT'
				.format(self._path))

		# Read in matrix format
		if fmt == 'matrix':
			data = self._read_matrix(offset, nevents)

			# Convert to correct byte order
			if systype:
				if sys.byteorder == 'little' and data.dtype.byteorder != '<':
					# This swaps bytes in-place in memory
					data.byteswap(True)
					# Replace variable with new view interpeting the order
					# correctly
					data = data.newbyteorder()

			# Compensation
			if isinstance(comp, np.ndarray):
				if comp.ndim != 2 or comp.shape[0] != self._par:
					raise ValueError(
						'Compensation matrix must be two-dimensional with '
						'{0} columns'
						.format(self._par))
				data = data.dot(comp)
			elif comp is True:
				if self._spillover is None:
					raise RuntimeError(
						'Compensation matrix not present in file')
				data = data.dot(np.linalg.pinv(self._spillover))
			elif comp is not None and comp is not False:
				raise TypeError(
					'Comp argument must be bool, numpy.ndarray, or None, not '
					' {0}'
					.format(type(comp)))

			return data

		# Read in events format
		if fmt == 'events':
			return self._read_events(offset, nevents)

		# Improper format
		else:
			raise ValueError('Invalid fmt argument: {0}'.format(repr(fmt)))

	def _read_matrix(self, offset, nevents):
		"""Reads data in matrix format (homogeneous data type)"""

		# If all column data types are identical, can do this directly
		if self._const_type:

			# Data type and number of elements
			dtype = np.dtype(self._channel_dtypes[0])
			nelem = nevents * self._par

			# Read in data as linear array
			with open(self._path, 'rb') as fh:
				fh.seek(offset)
				data = np.fromfile(fh, dtype=dtype, count=nelem)

			# Reshape
			# Note that C-order has last axis (channels) chaning fastest
			data = data.reshape((nevents, self._par), order='C')

			# If integer type, apply masks
			if self._datatype == 'I':
				for c in range(self._par):
					mask = self._int_masks[c]
					if mask is not None:
						data[:,c] &= np.asarray([mask],
							dtype=self._channel_dtypes[c])

			return data

		# Otherwise need to do it the other way and convert
		else:

			events = self._read_events(offset, nevents)

			# Widest column type
			widest = np.argmax(self._channel_bytes)
			dtype = np.dtype(self._channel_dtypes[widest])

			# Allocate array
			data = np.ndarray((nevents, self._par), dtype=dtype)

			# Copy data column-by-column
			for c, name in enumerate(self.channels):
				data[:,c] = events[name]

			return data

	def _read_events(self, offset, nevents):
		"""Reads data in events format (heterogeneous data types)"""

		# Numpy composite data type for each event
		event_dtype = np.dtype(zip(self.channels, self._channel_dtypes))

		# Read data from file
		with open(self._path, 'rb') as fh:
			fh.seek(offset)
			data = np.fromfile(fh, dtype=event_dtype, count=nevents)

		# Apply integer masks as needed
		if self._datatype == 'I':
			for ch_name, mask, dtype in zip(self.channels,
					self._int_masks, self._channel_dtypes):
				if mask is not None:
					data[ch_name] &= np.asarray([mask], dtype=dtype)

		return data

	def _read_metadata(self):
		"""
		Reads in metadata from the file, run on initialization

		This includes offsets to various file segments as well as all TEXT
		segment keywords and their values. With this information the actual
		event data can be read properly.
		"""

		# Open file
		with open(self._path, 'rb') as fh:

			# Read in version - first 6 bytes
			self._version = fh.read(6)

			# Check version
			if self._version != 'FCS3.1':

				# Warn if older (newer??) FCS version
				if self._version.startswith('FCS'):
					warnings.warn(
						'FCS version of "{0}" is {1}, may be incompatible'
						.format(self._path, self._version[3:]))

				# Otherwise fail
				else:
					raise FCSReadError(
						'"{0}" does not appear to be a valid FCS file'
						.format(self._path))

			# Next 4 bytes space, ignore
			fh.read(4)

			# Read in offsets - integers as 8 right-justified ASCII characters
			# If offset larger than 99,999,999, should read '       0' and
			# true offsets will be stored in the TEXT segment (should only
			# happen with DATA and ANALYSIS segments). I have also seen
			# '      -1' in the analysis end offset in an FCS3.0 file where
			# an analysis was not present, so try to support that as well).
			# Note - Default str to int conversion ignores leading/trailing
			# whitespace.
			self._offsets = dict(
				TEXT=(int(fh.read(8)), int(fh.read(8))),
				DATA=(int(fh.read(8)), int(fh.read(8))),
				ANALYSIS=(int(fh.read(8)), int(fh.read(8)))
				)

			# Read in TEXT segment
			self._read_text(fh)

			# If the DATA segment extends outside the first 99,999,999 bytes
			# of the file the offsets cannot be stored in the base allocated
			# in the header. In this case the standard dictates that the
			# header contain the strings '       0' instead and that the
			# actual offsets be given with the $BEGINDATA and $ENDDATA
			# keywords.
			if any(o <= 0 for o in self._offsets['DATA']):
				self._offsets['DATA'] = (
					int(self._text['$BEGINDATA']),
					int(self._text['$ENDDATA'])
					)

			# Handle special values in text
			self._handle_text()

	def _read_text(self, fh):
		"""Read in and parse text segment of file given file handle"""

		# Read entire TEXT segment into string
		text_offset = self._offsets['TEXT']
		fh.seek(text_offset[0])
		text = fh.read(text_offset[1] - text_offset[0] + 1)

		# Delimiter character should be at beginning and end of segment
		delim = text[0]
		if text[-1] != delim:
			raise FCSReadError(path=self._path)

		# This shouldn't happen but just in case...
		if text[1] == delim:
			raise FCSReadError(path=self._path)

		# Segment formatted as alternating keys and values, separated by
		# delimiter. But, delimiter can be escaped by writing twice so
		# can't just use text.split(delim)
		idx = 1
		text_segments = []
		while idx < len(text):

			# Find next index of delimiter which is not immediately
			# followed by another delimiter
			next_idx = idx
			next_idx = text.find(delim, idx)
			while next_idx < len(text) - 1 and text[next_idx + 1] == delim:
				next_idx = text.find(delim, next_idx + 2)

			# Save segment, after replacing double delimiters
			segment = text[idx:next_idx].replace(delim * 2, delim)
			text_segments.append(segment)

			# Skip after next delimiter
			idx = next_idx + 1

		# Split into keys and values
		text_keys = text_segments[0::2]
		text_values = text_segments[1::2]

		if len(text_keys) != len(text_values):
			raise FCSReadError(path=self._path)

		# Convert to dict
		self._text = dict(zip(text_keys, text_values))

	def _handle_text(self):
		"""Parses and validates other important keyword values"""

		# Number of channels/parameters
		self._par = int(self._text['$PAR'])

		# Create channels dataframe
		self._create_channels_df()

		# Total number of events
		self._tot = int(self._text['$TOT'])

		# Only list mode supported
		mode = self._text['$MODE']
		if mode != 'L':
			raise FCSReadError(
				'Error parsing "{0}": $MODE="{1}" not supported'
				.format(self._path, mode))

		# Byte order/endianness, >/< character used for numpy dtype
		if self._text['$BYTEORD'] == '1,2,3,4':
			self._byteord = 'little'
			ordchar = '<'
		elif self._text['$BYTEORD'] == '4,3,2,1':
			self._byteord = 'big'
			ordchar = '>'
		else:
			# Mixed byte orders present in FCS3.0, unsupported
			raise FCSReadError(
				'Error parsing "{0}": unsupported $BYTEORD "{1}"'
				.format(self._path, self._text['$BYTEORD']))

		# Check data type and determine information needed to read the data
		self._datatype = self._text['$DATATYPE']

		# F datatype is 32-bit float as per FCS3.1 spec
		if self._datatype == 'F':

			if not all(bits == 32 for bits in self._channel_info['$PnB']):
				raise FCSReadError(
					'Error parsing "{0}": $PnB must be 32 for all '
					'parameters if $DATATYPE is F'
					.format(self._path))

			self._channel_bytes = [4] * self._par
			self._channel_dtypes = [ordchar + 'f4'] * self._par
			self._const_type = True
			self._int_masks = None

		# D datatype is 64-bit float as per FCS3.1 spec
		elif self._datatype == 'D':

			if not all(bits == 64 for bits in self._channel_info['$PnB']):
				raise FCSReadError(
					'Error parsing "{0}": $PnB must be 64 for all '
					'parameters if $DATATYPE is D'
					.format(self._path))

			self._channel_bytes = [8] * self._par
			self._channel_dtypes = [ordchar + 'f8'] * self._par
			self._const_type = True
			self._int_masks = None

		# I datatype is unsigned integer, variable size
		elif self._datatype == 'I':

			# Support only 8, 16, 32, and 64-bit integers
			supported_bits = [8, 16, 32, 64]
			if any(b not in supported_bits for b in self._channel_info['$PnB']):
				raise FCSReadError(
					'Error parsing "{0}": integer sizes other than {1}-bit '
					'not supported.'
					.format(self._path, ', '.join(map(str, supported_bits)))
					)

			# Bytes per channel
			self._channel_bytes = [bits / 8
				for bits in self._channel_info['$PnB']]

			# Numpy dtype string per channel
			self._channel_dtypes = [ordchar + 'u' + b
				for b in self._channel_bytes]

			# Check all types are the same
			self._const_type = all(b == channel_bytes for b in channel_bytes)

			# Caluclate bit masks
			self._int_masks = []
			for ch in self._channel_info.iterrows():
				range_ = ch['$PnR']
				bits = ch['$PnB']
				if range_ == (1 << bits):
					self._int_masks.append(None)
				else:
					mask = (1 << (range_ - 1).bit_length()) - 1
					if mask >= (1 << bits):
						raise FCSReadError(
							'Error parsing "{0}": $PnR incompatible with '
							'$PnB for parameter {1}'
							.format(self._path, ch['$PnN']))
					self._int_masks.append(mask)

		# Other data types not supported
		else:
			raise FCSReadError(
				'Error parsing "{0}": $DATATYPE="{1}" not supported'
				.format(self._path, mode))

		# Read in spillover matrix
		# $SPILLOVER was introduced in FCS3.1 as an official keyword,
		# is sometimes just "SPILL" in FCS3.0 (BD cytometers)
		if '$SPILLOVER' in self._text:
			spill_str = self._text['$SPILLOVER']
		elif 'SPILL' in self._text:
			spill_str = self._text['SPILL']
		else:
			spill_str = None

		if spill_str is not None:

			# If any errors encountered while parsing, simply warn
			try:
				# Values separated by commas
				spill_values = spill_str.split(',')

				# First value is integer number of channels in matrix
				n = int(spill_values[0])
				assert 0 < n <= self._par
				assert len(spill_values) == 1 + n + n**2

				# Channel names in next n values (matching $PnN)
				spill_channels = spill_values[1:n+1]
				spill_ch_idx = [list(self._channel_info['$PnN']).index(ch)
					for ch in spill_channels]

				# Create identity matrix for ALL parameters, in case
				# $SPILLOVER only specifies a subset
				spill_matrix = np.identity(self._par)

				# Final n^2 values are the matrix in row-major order
				for r in range(n):
					for c in range(n):
						value = float(spill_values[1 + (r + 1) * n + c])
						# Diagonals should all be 1.0
						if r == c: assert value == 1.0
						spill_matrix[spill_ch_idx[r], spill_ch_idx[c]] = value

				self._spillover = spill_matrix

			# AssertionError on false assertions (duh), ValueError when
			# parsing invalid float literal or param name not in $PnN's
			except (AssertionError, ValueError) as e:
				# Just warn
				warnings.warn(
					'Error parsing spillover matrix in "{0}": {1}: {2}'
					.format(self._path, type(e).__name__, e))

		else:
			self._spillover = None

	def _create_channels_df(self):
		"""
		Creates a pandas.DataFrame describing channel attributes from
		keywords
		"""

		# Create empty table
		self._channel_info = pd.DataFrame.from_items([
			('$PnN', pd.Series(dtype=str)),    # Short name
			('$PnB', pd.Series(dtype=int)),    # Bits reserved for parameter
			('$PnE', pd.Series(dtype=object)), # Amplification type (float, float)
			('$PnR', pd.Series(dtype=int)),    # Range
			('$PnD', pd.Series(dtype=object)), # Optional - visualization scale
			('$PnF', pd.Series(dtype=int)),    # Optional - optical filter
			('$PnG', pd.Series(dtype=float)),  # Optional - gain
			('$PnL', pd.Series(dtype=object)), # Optional - exitation wavelengths
			('$PnO', pd.Series(dtype=float)),  # Optional - excitation power
			('$PnP', pd.Series(dtype=float)),  # Optional - percent light collected
			('$PnS', pd.Series(dtype=str)),    # Optional - long name
			('$PnT', pd.Series(dtype=str)),    # Optional - detector type
			('$PnV', pd.Series(dtype=float))   # Optional - detector voltage
			])

		# Fill data frame
		for i in range(1, self._par + 1):

			prefix = '$P' + str(i)

			row = dict()

			# Required keywords
			row['$PnB'] = int(self._text[prefix + 'B'])
			row['$PnN'] = self._text[prefix + 'N']
			row['$PnR'] = int(self._text[prefix + 'R'])

			pne = self._text[prefix + 'E']
			f1, f2 = tuple(pne.split(','))
			row['$PnE'] = (float(f1), float(f2))

			# Optional keywords
			row['$PnF'] = self._text.get(prefix + 'F')
			row['$PnL'] = self._text.get(prefix + 'L', '').split(',')
			row['$PnS'] = self._text.get(prefix + 'S')
			row['$PnT'] = self._text.get(prefix + 'T')

			try:
				pnd = self._text[prefix + 'D']
				scale, f1, f2 = tuple(pnd.split(','))
				row['$PnD'] = (scale, float(f1), float(f2))
			except KeyError:
				row['$PnD'] = None

			for c in ['G', 'O', 'P', 'V']:
				row['$Pn' + c] = float(self._text.get(prefix + c, 'nan'))

			# Add row
			self._channel_info.loc[i] = row
