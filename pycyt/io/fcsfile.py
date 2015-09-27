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
	"""

	def __init__(self, path):
		"""Creation from file path"""

		self._path = path

		self._read_metadata()

	@property
	def filepath(self):
		return self._path
	
	@property
	def version(self):
		return self._version

	@property
	def keywords(self):
		return self._keywords

	@property
	def par(self):
		return self._par

	@property
	def channels(self):
		return self._channels
	
	@property
	def tot(self):
		return self._tot	

	def _read_metadata(self):
		"""
		Reads in metadata from the file, run on initialization

		This includes offsets to various file segments as well as all keywords
		and their values. With this information the actual event data can be
		read properly.
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

			# Handle special values in keywords
			self._handle_keywords()

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
		self._keywords = dict(zip(text_keys, text_values))

	def _handle_keywords(self):
		"""Parses and validates other important keyword values"""

		# Create channels dataframe
		self._create_channels_df()

		# Total number of events
		self._tot = int(self._keywords['$TOT'])

		# Only list mode supported
		mode = self._keywords['$MODE']
		if mode != 'L':
			raise FCSReadError(
				'Error parsing "{0}": $MODE="{1}" not supported'
				.format(self._path, mode))

		# Byte order/endianness, >/< character used for numpy dtype
		if self._keywords['$BYTEORD'] == '1,2,3,4':
			self._byteord = 'little'
			ordchar = '<'
		elif self._keywords['$BYTEORD'] == '4,3,2,1':
			self._byteord = 'big'
			ordchar = '>'
		else:
			raise FCSReadError(path=self._path)

		# Check data type and determine information needed to read the data
		self._datatype = self._keywords['$DATATYPE']

		# F datatype is 32-bit float as per FCS3.1 spec
		if self._datatype == 'F':

			if not all(bits == 32 for bits in self._channels['$PnB']):
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

			if not all(bits == 64 for bits in self._channels['$PnB']):
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
			if any(b not in supported_bits for b in self._channels['$PnB']):
				raise FCSReadError(
					'Error parsing "{0}": integer sizes other than {1}-bit '
					'not supported.'
					.format(self._path, ', '.join(map(str, supported_bits)))
					)

			# Bytes per channel
			self._channel_bytes = [bits / 8
				for bits in self._channels['$PnB']]

			# Numpy dtype string per channel
			self._channel_dtypes = [ordchar + 'u' + b
				for b in self._channel_bytes]

			# Check all types are the same
			self._const_type = all(b == channel_bytes for b in channel_bytes)

			# Caluclate bit masks
			self._int_masks = []
			for ch in self._channels.iterrows():
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

	def _create_channels_df(self):
		"""
		Creates a pandas.DataFrame describing channel attributes from
		keywords
		"""

		# Number of channels/parameters
		self._par = int(self._keywords['$PAR'])

		# Create empty table
		self._channels = pd.DataFrame({
			'$PnB': pd.Series(dtype=int),    # Bits reserved for parameter
			'$PnN': pd.Series(dtype=str),    # Short name
			'$PnR': pd.Series(dtype=int),    # Range
			'$PnE': pd.Series(dtype=object), # Amplification type (float, float)
			'$PnF': pd.Series(dtype=int),    # Optional - optical filter
			'$PnL': pd.Series(dtype=object), # Optional - exitation wavelengths
			'$PnS': pd.Series(dtype=str),    # Optional - long name
			'$PnT': pd.Series(dtype=str),    # Optional - detector type
			'$PnD': pd.Series(dtype=object), # Optional - visualization scale
			'$PnG': pd.Series(dtype=float),  # Optional - gain
			'$PnO': pd.Series(dtype=float),  # Optional - excitation power
			'$PnP': pd.Series(dtype=float),  # Optional - percent light collected
			'$PnV': pd.Series(dtype=float),  # Optional - detector voltage
			})

		# Fill data frame
		for n in range(1, self._par + 1):

			prefix = '$P' + str(n)

			row = dict()

			# Required keywords
			row['$PnB'] = int(self._keywords[prefix + 'B'])
			row['$PnN'] = self._keywords[prefix + 'N']
			row['$PnR'] = int(self._keywords[prefix + 'R'])

			pne = self._keywords[prefix + 'E']
			f1, f2 = tuple(pne.split(','))
			row['$PnE'] = (float(f1), float(f2))

			# Optional keywords
			row['$PnF'] = self._keywords.get(prefix + 'F')
			row['$PnL'] = self._keywords.get(prefix + 'L', '').split(',')
			row['$PnS'] = self._keywords.get(prefix + 'S')
			row['$PnT'] = self._keywords.get(prefix + 'T')

			try:
				pnd = self._keywords[prefix + 'D']
				scale, f1, f2 = tuple(pnd.split(','))
				row['$PnD'] = (scale, float(f1), float(f2))
			except KeyError:
				row['$PnD'] = None

			try:
				row['$PnG'] = float(self._keywords[prefix + 'G'])
			except KeyError:
				row['$PnG'] = np.nan

			try:
				row['$PnO'] = float(self._keywords[prefix + 'O'])
			except KeyError:
				row['$PnO'] = np.nan

			try:
				row['$PnP'] = float(self._keywords[prefix + 'P'])
			except KeyError:
				row['$PnP'] = np.nan

			try:
				row['$PnV'] = float(self._keywords[prefix + 'V'])
			except KeyError:
				row['$PnV'] = np.nan

			# Add row
			self._channels.loc[row['$PnN']] = row
