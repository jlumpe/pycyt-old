import collections

import numpy as np
import pandas as pd


def pd_index_positions(data, which):
	"""
	Gets rows of a pandas.Dataframe or elements of a pandas.Series by their
	sequential position using one of several different index types. The
	problem this is trying to correct is that Pandas objects have two methods
	of indexing, using the .iloc[] method to go by a slice or sequence of
	indices and the .loc[] which goes by rows. Boolean indexing uses .loc[]
	or the basic __getattr__ method. This project uses integer and boolean
	indexing often and it gets annoying to check which method needs to be
	used, this function is meant to do it for you.

	NOTE THAT THIS MAY RETURN A VIEW OF THE DATA, NOT A COPY

	Args:
		data: a pandas.Dataframe or pandas.Series
		which: One of several types, which different behavior for each:
			int/long: single row/element
			slice: slices row/element range with standard slice behavior
			pandas.Series: either integer dtype to select rows/elements by
				index or bool dtype to select rows/elements where index is
				True.
			numpy.ndarray: 1D, with same behavior as pandas.Series
			list: same behavior as pandas.Series

	Returns:
		same type as data argument, filtered by rows or elements.
	"""
	# Single integer index
	if np.isscalar(which) and np.dtype(type(which)).kind == 'i':
		return data.iloc[which]

	# Slice
	if isinstance(which, slice):
		return data.iloc[which]

	# Numpy array
	elif isinstance(which, (pd.Series, np.ndarray)):
		if which.dtype.kind == 'i': # Integer row indices
			return data.iloc[which]
		elif which.dtype.kind == 'b': # Boolean selection
			return data.loc[which]
		else:
			raise TypeError('Invalid dtype for "which" argument')

	# List
	elif isinstance(which, list):
		if isinstance(which[0], (int, long)): # Integer row indices
			return data.iloc[which]
		elif isinstance(which[0], bool): # Boolean selection
			return data.loc[which]
		else:
			raise TypeError('List elements must be int or bool')

	# Invalid
	else:
		raise TypeError(
			'Invalid type for "which" argument: {0}'
			.format(type(which)))

def cycle_adjacent(seq, n):
	"""
	For a given sequence (taken to be cyclical), yields all n-tuples of
	consecutive elements. For example, cycle_adjacent(range(5), 3) returns
	[(0, 1, 2), (1, 2, 3), (2, 3, 4), (3, 4, 0), (4, 0, 1)].
	Yields nothing for sequences of length less than n.
	"""
	i = iter(seq)
	start = collections.deque(maxlen=n)
	for j in range(n):
		try:
			start.append(next(i))
		except StopIteration:
			return
	q = collections.deque(start, maxlen=n)
	while True:
		yield tuple(q)
		try:
			e = next(i)
		except StopIteration:
			break
		q.popleft()
		q.append(e)
	for j in range(n-1):
		q.popleft()
		q.append(start.popleft())
		yield tuple(q)

