import warnings

import pandas as pd
import numpy as np

from pycyt.errors import FCSReadError


def read_fcs_metadata(path):
	"""
	Reads metadata from an FCS file on disk given file path. This includes
	offsets to various file segments as well as all keywords and their values.
	With this information the actual event data can be read properly.

	Technically this was only written to support FCS version 3.1 files,
	but could work for others. Refer to FCS 3.1 specification in
	http://isac-net.org/PDFS/90/9090600d-19be-460d-83fc-f8a8b004e0f9.pdf

	Args:
		path: str. Path to FCS file to be read.

	Returns:
		tuple, (offets, keywords). First element is dict with keys ["TEXT",
		'DATA", "ANALYSIS"] and values (begin, end) of integer offsets to
		these segments. Second element is a dict containing all key/value
		pairs in the TEXT segment.
	"""

	# Open file
	with open(path, 'rb') as fh:

		# Read in version - first 6 bytes
		version = fh.read(6)

		# Check version
		if version != 'FCS3.1':

			# Warn if older (newer??) FCS version
			if version.startswith('FCS'):
				warnings.warn(
					'FCS version of "{0}" is {1}, may be incompatible'
					.format(path, version[3:]))

			# Otherwise fail
			else:
				raise FCSReadError(
					'"{0}" does not appear to be a valid FCS file'
					.format(path))

		# Next 4 bytes space, ignore
		fh.read(4)

		# Read in offsets - integers as 8 right-justified ASCII characters
		# If offset larger than 99,999,999, should read '       0' and true
		# offsets will be stored in the TEXT segment (should only happen with
		# DATA and ANALYSIS segments). I have also seen '      -1' in the
		# analysis end offset in and FCS3.0 file where an analysis was not
		# present, so try to support that as well). Note - Default str to int
		# conversion ignores leading/trailing whitespace.
		offsets = dict(
			TEXT=(int(fh.read(8)), int(fh.read(8))),
			DATA=(int(fh.read(8)), int(fh.read(8))),
			ANALYSIS=(int(fh.read(8)), int(fh.read(8)))
			)

		# Read entire TEXT segment into string
		fh.seek(offsets['TEXT'][0])
		text = fh.read(offsets['TEXT'][1] - offsets['TEXT'][0] + 1)

		# Delimiter character should be at beginning and end of segment
		delim = text[0]
		if text[-1] != delim:
			raise FCSReadError(path=path)

		# This shouldn't happen but just in case...
		if text[1] == delim:
			raise FCSReadError(path=path)

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
			raise FCSReadError(path=path)

		# Convert to dict
		keywords = dict(zip(text_keys, text_values))

		# TODO - update offsets from keywords as needed

	return offsets, keywords


def make_channel_frame(keywords):
	"""
	Creates a pandas.DataFrame describing channel attributes from a set of FCS
	keywords.
	"""

	# Number of channels/parameters
	npar = int(keywords['$PAR'])

	# Create empty table
	df = pd.DataFrame({
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
	for n in range(1, npar + 1):

		prefix = '$P' + str(n)

		row = dict()

		# Required keywords
		row['$PnB'] = int(keywords[prefix + 'B'])
		row['$PnN'] = keywords[prefix + 'N']
		row['$PnR'] = int(keywords[prefix + 'R'])

		pne = keywords[prefix + 'E']
		f1, f2 = tuple(pne.split(','))
		row['$PnE'] = (float(f1), float(f2))

		# Optional keywords
		row['$PnF'] = keywords.get(prefix + 'F')
		row['$PnL'] = keywords.get(prefix + 'L', '').split(',')
		row['$PnS'] = keywords.get(prefix + 'S')
		row['$PnT'] = keywords.get(prefix + 'T')

		try:
			pnd = keywords[prefix + 'D']
			scale, f1, f2 = tuple(pnd.split(','))
			row['$PnD'] = (scale, float(f1), float(f2))
		except KeyError:
			row['$PnD'] = None

		try:
			row['$PnG'] = float(keywords[prefix + 'G'])
		except KeyError:
			row['$PnG'] = np.nan

		try:
			row['$PnO'] = float(keywords[prefix + 'O'])
		except KeyError:
			row['$PnO'] = np.nan

		try:
			row['$PnP'] = float(keywords[prefix + 'P'])
		except KeyError:
			row['$PnP'] = np.nan

		try:
			row['$PnV'] = float(keywords[prefix + 'V'])
		except KeyError:
			row['$PnV'] = np.nan

		# Add row
		df.loc[row['$PnN']] = row

	return df
