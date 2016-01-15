import sys
import re
from warnings import warn

import numpy as np

from pycyt.util import FileHandleManager
from .fcsstandard import (
	fcs_keywords,
	fcs_required_keywords,
	fcs_param_keywords,
	fcs_keyword_patterns,
	is_printable,
	is_valid_keyword,
	is_valid_delimiter
	)


# Regexes used to validate keyword values
_patterns = {
	'n': r'\d+',
	'f': r'[-+]?(\d*\.\d+|\d+(\.\d*)?)([eE][-+]?\d+)?',
	'date': r'\d{2}-[A-Za-z]{3}-\d{4}',
	'time': r'\d{2}:\d{2}:\d{2}(\.\d{2})?'
	}


# Keywords that should not be explicitly passed to write_fcs_file()
_reserved_keywords = [
	'$PnN',
	'$DATATYPE',
	'$TOT',
	'$BEGINSTEXT',
	'$BEGINDATA',
	'$BEGINANALYSIS',
	'$ENDSTEXT',
	'$ENDDATA',
	'$ENDANALYSIS',
	'$BYTEORD',
	'$PAR',
	'$MODE',
	'$NEXTDATA',
	'$PnB'
	]


def estimate_param_range(data):
	"""
	Tries to estimate parameter ranges ($PnR) given a data matrix. This is
	tricky and I'll try to use some heuristics:

		* Typically, this should be the same for all parameters.
		* It should probably also be a power of two.
		* Recorded values may actually be calibrated to adjust for background
			fluorescence levels so they could actually be higher than the
			maximum range.

	So, my method is as follows:
		1. Find maximum values of each parameter
		2. Take base2 log of each to get number of bit needed to represent it
		3. Average these values together
		4. Round to nearest integer, and use 2 ** this value.

	All instruments I've used have an ADC with 18-bit range ($PnR=262144) but
	I don't know if that is common enough to use by default. This method
	seems to generate the correct values for the files I've looked at, but
	these files all tend to have at least a few events high on the scale in
	each parameter. It could definitely fail on a file where that is not the
	case.

	Args:
		data: numpy.ndarray. 2d array of data with events along axis 0 and
			parameters along axis 1.

	Returns:
		int.
	"""
	return 2 ** int(round(np.mean(np.log2(np.max(data, axis=0)))))


def get_text_len(text):
	"""
	Get number of bytes required to store the TEXT segment of an FCS file.

	Args:
		text: dict. Keywords as dict keys (str) and values as dict values
			(unicode). Assumes delimiter has already been escaped in values.

	Returns:
		int
	"""
	# Remember there are two 1-byte delimiters for each key-value pair, plus
	# one extra delimiter at the beginning (or end)
	nbytes = 1
	for keyword, value in text.iteritems():
		nbytes += 2 + len(keyword) + len(value.encode('UTF-8'))
	return nbytes


def make_spillover(params, matrix):
	"""
	Create the value of the $SPILLOVER keyword given a list of parameter
	names and a spillover matrix.

	Args:
		params: list of str. Parameter names. Should correspond to values of
			$PnN (short names). Does not have to include all parameters in
			file but should be at least two. Order does not matter.
		matrix: numpy.ndarray. Spillover matrix, 2d array of float values with
			dimensions equal to the length of the param argument. The rows
			correspond to fluorochromes and the columns to detectors. Thus,
			the value of element M_i,j is the spillover from fluorochrome i
			into detector j.

	Returns:
		str. Value of $SPILLOVER keyword in format given by FCS3.1 standard.
	"""
	n = len(params)
	if n < 2:
		raise ValueError('Must include at least two parameters')
	if matrix.shape != (n, n):
		raise ValueError('Matrix has unexpected shape')

	entries = [str(n)]
	entries.extend(params)
	entries.extend(str(float(v)) for r in matrix for v in r)
	return ','.join(entries)


def write_fcs_file(file_, params, data, text=None, **kwargs):
	"""
	Writes data to file in FCS3.1 format.

	Args:
		file_: (stream|basestring). Writable output stream (usually file
			handle) or file path to write to.
		params: list of str. Parameter names, equivalent to values of $PnN FCS 
			keywords. Must be unique strings of ASCII characters in range
			32-126 (excluding comma), as per FCS3.1 standard. Note that these
			are the "short" names, long versions can be passed as values to
			the $PnS keywords.
		data: numpy.ndarray. 2d array of data with events along axis 0 and
			parameters along axis 1. Number and order of columns must match
			params argument. Data type must be 32- or 64-bit float ($DATATYPE
			of F or D). Big or little endian data types are supported.
		text: dict. Key/value pairs for TEXT segment. Keys must be ASCII
			strings with characters 32-128 not starting with the delimiter,
			values can be any unicode string. Default keywords which
			incorporate a parameter number (e.g. $PnR) can be specified with a
			lower-case "n" character to make them apply to all parameters.
			Values for the following keywords are determined by arguments to
			the function and should not be included:
				$PnN, $DATATYPE, $TOT, $(BEGIN|END)(STEXT|DATA|ANALYSIS),
				$BYTEORD, $PAR, $MODE, $NEXTDATA, $PnB
			The following are required keywords and values will be generated
			automatically if not present:
				$PnE, $PnR
			Unless suppress_warnings is True, warnings will be generated if:
				*  A keyword starts with '$' but is not defined in the FCS3.1
					standard.
				* A keyword's value is automatically generated by the function
					and will be overwritten.
				* A keyword's value does not match the pattern defined by the
					FCS3.1 standard.

	**kwargs:
		delim: str. Single ASCII character to use as delimiter in TEXT segment.
			Should be in range 1-126. Defaults to '/'.
		suppress_warnings: bool. If true, suppresses warnings about invalid
			FCS keywords/values. Defaults to False.
		spillover: tuple|np.ndarray|None. If not None, will be used to create
			value for $SPILLOVER keyword. If tuple, will be used as *args to
			pycyt.io.writefcsfile.make_spillover. If single numpy.ndarray
			is passed, will use (params, spillover) as arguments to same
			function.
	"""
	# Get additional keyword arguments
	delim = kwargs.pop('delim', '/')
	suppress_warnings = kwargs.pop('suppress_warnings', False)
	spillover = kwargs.pop('spillover', None)

	if len(kwargs):
		raise TypeError(
			'Unknown keyword argument "{0}"'
			.format(next(iter(kwargs)))
			)

	# Get our own copy of the text dict to work with
	if text is None:
		text_dict = dict()
	else:
		text_dict = dict(text)

	# Validate parameter names
	seen_params = set()
	for pname in params:
		if not is_printable(pname) or ',' in pname:
			raise ValueError(
				'Invalid parameter name "{0}" (see docstring)'
				.format(pname)
				)
		if pname in seen_params:
			raise ValueError(
				'Parameter name "{0}" occurs more than once'
				.format(pname)
				)
		seen_params.add(pname)

	# Validate delimiter
	if not is_valid_delimiter(delim):
		raise ValueError('Invalid delimiter (see docstring)')

	# Validate data matrix
	if data.ndim != 2 or data.shape[1] != len(params):
		raise ValueError('Data matrix has invalid shape')
	if data.dtype.kind != 'f' or data.dtype.itemsize not in [4, 8]:
		raise ValueError('Data matrix dtype must be 32- or 64-bit float')

	# Expand parameter-specific keywords
	for kw in fcs_param_keywords:
		if kw in text_dict:
			value = text_dict.pop(kw)
			for i in range(len(params)):
				text_dict[kw.replace('n', str(i+1))] = value

	# Validate passed keyword/value pairs
	for keyword, value in text_dict.iteritems():
		# Check keyword is valid. This raises a hard error if it is not.
		if not is_valid_keyword(keyword, delim):
			raise ValueError(
				'Keyword "{0}" is invalid (see docstring)'
				.format(keyword)
				)

		# Further validation of FCS-defined keywords and values
		# These all generate warnings, skip if suppress_warnings is True
		if keyword.startswith('$') and not suppress_warnings:

			# Normalized version of keyword, with digit strings replaced by "n"
			normkw = re.sub(r'\d+', 'n', keyword)

			# Check if actually an FCS-defined keyword
			if normkw in fcs_keywords:

				# Check if one of the keywords that will be overwritten
				if normkw in _reserved_keywords:
					warn(
						'Keyword {0} is determined by function arguments and'
						' will be ignored'
						.format(keyword)
						)

				# Validate keyword values
				try:
					pattern = '^' + fcs_keyword_patterns[normkw] + '$'
					if re.match(pattern, value) is None:
						warn(
							'Value of FCS-defined keyword "{0}" shoud match'
							' regex /{1}/'
							.format(keyword, pattern)
							)
				except KeyError:
					pass

			# Otherwise it may be a misspelling - warn about it
			# (it's also forbidden by the standard)
			else:
				warn(
					'Keyword {0} starts with $ but is not part of the'
					' FCS3.1 standard'
					.format(keyword)
					)

	# Keywords determined by function arguments, overwrite if present
	tot, par = data.shape
	dtype_double = data.dtype.itemsize == 8

	if data.dtype.byteorder == '=':
		data_is_le = sys.byteorder == 'little'
	else:
		data_is_le = data.dtype.byteorder == '<'
	text_dict['$BYTEORD'] = '1,2,3,4' if data_is_le else '4,3,2,1'

	text_dict['$DATATYPE'] = 'D' if dtype_double else 'F'
	text_dict['$MODE'] = 'L'
	text_dict['$NEXTDATA'] = '0'
	text_dict['$PAR'] = str(par)
	text_dict['$TOT'] = str(tot)
	text_dict['$BEGINANALYSIS'] = '0'
	text_dict['$ENDANALYSIS'] = '0'
	text_dict['$BEGINSTEXT'] = '0'
	text_dict['$ENDSTEXT'] = '0'

	for i in range(par):
		# Bits per parameter
		text_dict['$P{0}B'.format(i+1)] = '64' if dtype_double else '32'
		# Parameter short names
		text_dict['$P{0}N'.format(i+1)] = params[i]

	# Placeholders for DATA segment byte offsets - will fill this in afterwards
	data_offset_digits = 12 # Can safely assume size of file is << 1TB
	text_dict['$BEGINDATA'] = '0' * data_offset_digits
	text_dict['$ENDDATA'] = '0' * data_offset_digits

	# Create $SPILLOVER value if needed
	if spillover is not None:
		if '$SPILLOVER' in text_dict:
			warn('Overwriting value of $SPILLOVER keyword')
		if isinstance(spillover, tuple):
			spillover_args = spillover
		else:
			spillover_args = (params, spillover)
		text_dict['$SPILLOVER'] = make_spillover(*spillover_args)

	# Required keyword values that can be automatically generated if not
	# already given
	range_estimate = estimate_param_range(data)
	for i in range(par):
		# Parameter scale - default to linear ("0,0")
		text_dict.setdefault('$P{0}E'.format(i+1), '0,0')
		text_dict.setdefault('$P{0}R'.format(i+1), str(range_estimate))

	# Convert all keyword values to unicode and escape delimiters
	for kw in text_dict:
		text_dict[kw] = unicode(text_dict[kw]).replace(delim, delim + delim)

	# Calculate offests
	text_bytes = get_text_len(text_dict)
	offset_text_begin = 256
	offset_text_end = offset_text_begin + text_bytes - 1

	offset_data_begin = offset_text_end + 1
	offset_data_end = offset_data_begin + data.nbytes - 1

	# Check it all fits...
	if len(str(offset_text_end)) >= 10 ** 8:
		raise ValueError(
			'TEXT segment is {0} bytes long, unable fit into first 99,999,999'
			' bytes'
			.format(text_bytes)
			)
	assert len(str(offset_data_end)) < 10 ** data_offset_digits

	# Add correct data offsets to TEXT segment (left pad with zeros to keep
	# byte length unchanged - this is allowed by standard [not like that
	# LSRFortessa I caught right padding with spaces - read the standard
	# BD engineers!])
	offset_format_str = '0{0}d'.format(data_offset_digits)
	text_dict['$BEGINDATA'] = format(offset_data_begin, offset_format_str)
	text_dict['$ENDDATA'] = format(offset_data_end, offset_format_str)

	# Finally, it's time to start writing
	with FileHandleManager(file_, mode='wb') as fh:
		# Just in case we're appending to something maybe?
		begin_offset = fh.tell()

		# FCS standard version identifier, four spaces
		fh.write('FCS3.1')
		fh.write(' ' * 4)

		# TEXT segment offsets, left-padded with spaces to 8 bytes
		fh.write(format(offset_text_begin, ' 8d'))
		fh.write(format(offset_text_end, ' 8d'))

		# DATA segment offsets - same, but only if it fits
		if offset_data_end < 10 ** 8:
			fh.write(format(offset_data_begin, ' 8d'))
			fh.write(format(offset_data_end, ' 8d'))
		else:
			fh.write(format(0, ' 8d'))
			fh.write(format(0, ' 8d'))

		# ANALYSYS segment offsets - not supported (yet) so write zeros
		fh.write(format(0, ' 8d'))
		fh.write(format(0, ' 8d'))

		# Write the TEXT segment
		fh.seek(offset_text_begin, begin_offset)
		fh.write(delim)
		for keyword, value in text_dict.iteritems():
			fh.write(keyword) # ASCII-encoded (already validated)
			fh.write(delim)
			fh.write(value.encode('UTF-8')) # UTF-8 string
			fh.write(delim)
		assert fh.tell() == begin_offset + offset_text_end + 1

		# Finally, write DATA
		fh.seek(offset_data_begin, begin_offset)
		data.tofile(fh)
		assert fh.tell() == begin_offset + offset_data_end + 1, str(fh.tell())
