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
