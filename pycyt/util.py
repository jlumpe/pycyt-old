import collections

import numpy as np
import pandas as pd


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


class AutoIDMeta(type):
	"""
	Meta-class for AutoIDMixin, gives all subclasses an attribute to store
	next ID
	"""
	def __new__(cls, name, bases, dct):

		if '_next_ID' not in dct:
			dct['_next_ID'] = 1

		return super(AutoIDMeta, cls).__new__(cls, name, bases, dct)


class AutoIDMixin(object):
	"""Mix-in class that allocates unique IDs based on class name and
	sequential integer
	"""
	__metaclass__ = AutoIDMeta

	@classmethod
	def _auto_ID(cls):
		"""Automatically creates a unique ID string for a new instance"""
		ID = cls.__name__ + str(cls._next_ID)
		cls._next_ID += 1
		return ID


class FileHandleManager(object):
	"""
	Context manager which takes either an already-open file handle or a file
	path in its constructor, and returns an open file handle from the
	__enter__ method. If a file path was passed, the handle is opened on
	__enter__ and closed on __exit__. Meant to be used in functions which take
	either an open file handle or file path as an argument.
	"""

	def __init__(self, file_, mode='r', **kwargs):
		"""
		Args:
			file_: (stream object|basestring). Open file handle (or other
				stream), or path to file to be opened.
			mode: basestring. Mode to open file with, if file_ is a string.
				Default 'r' for reading in text mode (same as open() default).
			**kwargs: Passed to open() if needed.
		"""
		self.file_ = file_
		self.mode = mode
		self.kwargs = kwargs

	def __enter__(self):
		if isinstance(self.file_, basestring):
			self.fh = open(self.file_, mode=self.mode, **self.kwargs)
			self.needs_close = True
		else:
			self.fh = self.file_
			self.needs_close = False
		return self.fh

	def __exit__(self, type, value, traceback):
		if self.needs_close:
			self.fh.close()
