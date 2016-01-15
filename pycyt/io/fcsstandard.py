"""
Contains definitions from the FCS3.1 standard. In particular it enumerates
the buit-in keywords.
"""


# All FCS keywords defined in 3.1 standard
# Note that all are uppercase with the exception of a lowercase "n" character
# which indices an integer value
fcs_keywords = {
	'$ABRT',
	'$BEGINANALYSIS',
	'$BEGINDATA',
	'$BEGINSTEXT',
	'$BTIM',
	'$BYTEORD',
	'$CELLS',
	'$COM',
	'$CSMODE',
	'$CSVBITS',
	'$CSVnFLAG',
	'$CYT',
	'$CYTSN',
	'$DATATYPE',
	'$DATE',
	'$ENDANALYSIS',
	'$ENDDATA',
	'$ENDSTEXT',
	'$ETIM',
	'$EXP',
	'$FIL',
	'$GATE',
	'$GATING',
	'$GnE',
	'$GnF',
	'$GnN',
	'$GnP',
	'$GnR',
	'$GnS',
	'$GnT',
	'$GnV',
	'$INST',
	'$LAST_MODIFIED',
	'$LAST_MODIFIER',
	'$LOST',
	'$MODE',
	'$NEXTDATA',
	'$OP',
	'$ORIGINALITY',
	'$PAR',
	'$PKNn',
	'$PKn',
	'$PLATEID',
	'$PLATENAME',
	'$PROJ',
	'$PnB',
	'$PnCALIBRATION',
	'$PnD',
	'$PnE',
	'$PnF',
	'$PnG',
	'$PnL',
	'$PnN',
	'$PnO',
	'$PnP',
	'$PnR',
	'$PnS',
	'$PnT',
	'$PnV',
	'$RnI',
	'$RnW',
	'$SMNO',
	'$SPILLOVER',
	'$SRC',
	'$SYS',
	'$TIMESTEP',
	'$TOT',
	'$TR',
	'$VOL',
	'$WELLID'
	}

# Required FCS keywords from 3.1 standard
fcs_required_keywords = {
	'$BEGINANALYSIS',
	'$BEGINDATA',
	'$BEGINSTEXT',
	'$BYTEORD',
	'$DATATYPE',
	'$ENDANALYSIS',
	'$ENDDATA',
	'$ENDSTEXT',
	'$MODE',
	'$NEXTDATA',
	'$PAR',
	'$PnB',
	'$PnE',
	'$PnN',
	'$PnR',
	'$TOT'
	}

# Parameter keywords from 3.1 standard - "n" stands for the parameter number
fcs_param_keywords = {
	'$PnB',
	'$PnCALIBRATION',
	'$PnD',
	'$PnE',
	'$PnF',
	'$PnG',
	'$PnL',
	'$PnN',
	'$PnO',
	'$PnP',
	'$PnR',
	'$PnS',
	'$PnT',
	'$PnV'
	}

# Regexes used to validate keyword values
_patterns = {
	'n': r'\d+',
	'f': r'[-+]?(\d*\.\d+|\d+(\.\d*)?)([eE][-+]?\d+)?',
	'date': r'\d{2}-[A-Za-z]{3}-\d{4}',
	'time': r'\d{2}:\d{2}:\d{2}(\.\d{2})?'
	}
fcs_keyword_patterns = {
	'$ABRT': _patterns['n'],
	'$BEGINANALYSIS': _patterns['n'],
	'$BEGINDATA': _patterns['n'],
	'$BEGINSTEXT': _patterns['n'],
	'$BTIM': _patterns['time'],
	'$BYTEORD': r'1,2,3,4|4,3,2,1',
	'$CSMODE': _patterns['n'],
	'$CSVBITS': _patterns['n'],
	'$CSVnFLAG': _patterns['n'],
	'$DATATYPE': r'[IFDA]',
	'$DATE': _patterns['date'],
	'$ENDANALYSIS': _patterns['n'],
	'$ENDDATA': _patterns['n'],
	'$ENDSTEXT': _patterns['n'],
	'$ETIM': _patterns['time'],
	'$GATE': _patterns['n'],
	'$GnE': '{f},{f}'.format(**_patterns),
	'$GnP': _patterns['n'],
	'$GnR': _patterns['n'],
	'$GnV': _patterns['n'],
	'$LAST_MODIFIED': '{date} {time}'.format(**_patterns),
	'$MODE': r'[LCU]',
	'$NEXTDATA': _patterns['n'],
	'$PAR': _patterns['n'],
	'$PKn': _patterns['n'],
	'$PKNn': _patterns['n'],
	'$PnB': _patterns['n'],
	'$PnCALIBRATION': r'{f},.*'.format(**_patterns),
	'$PnD': r'(Linear|Logarithmic),{f},{f}'.format(**_patterns),
	'$PnE': '{f},{f}'.format(**_patterns),
	'$PnG': _patterns['f'],
	'$PnL': '{n}(,{n})*'.format(**_patterns),
	'$PnO': _patterns['n'],
	'$PnP': _patterns['n'],
	'$PnR': _patterns['n'],
	'$PnV': _patterns['f'],
	'$RnW': '{f},{f}(;{f},{f})*'.format(**_patterns),
	'$TIMESTEP': _patterns['f'],
	'$TOT': _patterns['n'],
	'$TR': r'[^,]+,\d+',
	'$VOL': _patterns['f']
	}


def is_printable(str_):
	"""
	Tests if a string contains only printable characters according to the
	FCS3.1 standard, which are those with ASCII value 32-126.

	Args:
		str_: basestring.

	Returns:
		bool
	"""
	return all(32 <= ord(c) <= 126 for c in str_)

def is_valid_delimiter(delim):
	"""
	Checks if a character is a valid delimiter for the TEXT segment of an
	FCS3.1 file. It must be an ASCII character with code between 1 and 126.
	Additionally, although it is not explicitly stated in the standard, it
	cannot be the '$' character because keywords are not allowed to start
	with a delimiter.

	Args:
		delim: basestring, single character.

	Returns:
		bool
	"""
	return len(delim) == 1 and 1 <= ord(delim) <= 126 and delim != '$'

def is_valid_keyword(keyword, delim):
	"""
	Checks if a given keyword is valid - printable and does not begin with
	a delimiter.

	Args:
		keyword: basestring.
		delim: basestring. Delimiter character.

	Returns:
		bool
	"""
	return is_printable(keyword) and not keyword.startswith(delim)
