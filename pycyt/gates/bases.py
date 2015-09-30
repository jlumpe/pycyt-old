import numpy as np
import pandas as pd

from pycyt import FlowFrame


class AbstractGate(object):
	"""
	Abstract base class for a flow cytometry gate object.

	Conceptually, a gate divides a data space into two or more regions.
	These regions
	"""

	def __init__(self, channels, regions, default_region=None, ID=None):

		# Check channels
		if not all(isinstance(ch, basestring) for ch in channels):
			raise TypeError('Channels must be strings')
		if len(set(channels)) != len(channels):
			raise ValueError('Channels must be unique')
		self._channels = list(channels)

		# Check ID, auto generate if needed
		if isinstance(ID, basestring):
			self._ID = ID
		elif ID is None:
			self._ID = self._auto_id()
		else:
			raise TypeError('ID must be string, not {0}'.format(type(ID)))

		# Regions should be set
		self._regions = set(regions)

		# Check default region
		if default_region not in self._regions and default_region is not None:
			raise ValueError(
				'Invalid default region {0}'
				.format(default_region))
		self._default_region = default_region

	@property
	def channels(self):
		return self._channels[:]

	@property
	def ndim(self):
		return len(self._channels)
	
	@property
	def regions(self):
		return self._regions

	@property
	def default_region(self):
		return self._default_region
	
	def __call__(self, events, region=None):

		# Check region
		if region is None:
			if self._default_region is not None:
				region = self._default_region
			else:
				raise ValueError('No default region, must give explicitly')
		elif region not in self._regions:
			raise ValueError('Invalid region {0}'.format(repr(region)))

		# Apply based on type of argument

		# FlowFrame
		if isinstance(events, FlowFrame):
			array = events.data[self._channels].values
			passed = self._contains(array, region)
			return events.filter(passed)

		# Pandas DataFrame
		elif isinstance(events, pd.DataFrame):
			array = events[self._channels].values
			passed = self._contains(array, region)
			return events.iloc[passed]

		# Pandas Series - for 1D gates
		elif isinstance(events, pd.Series):
			if len(self._channels) != 1:
				raise ValueError('Can only apply 1D gate to pandas.Series')
			else:
				array = events.values[:,np.newaxis]
				passed = self._contains(array, region)
				return events.iloc[passed]

		# Numpy array - assume column in same order as channels
		elif isinstance(events, numpy.ndarray):

			# 2D array
			if events.ndim == 2:
				if events.shape[1] != len(self._channels):
					raise ValueError(
						'Number of columns in array must match number of '
						'channels in gate')
				else:
					passed = self._contains(events, region)
					return events[passed,:]

			# 1D array - for 1D gates
			elif events.ndim == 1:
				if len(self._channels) != 1:
					raise ValueError('Can only apply 1D gate to 1D array')
				else:
					array = events.values[:,np.newaxis]
					passed = self._contains(array, region)
					return events[passed]

			# Bad shape
			else:
				raise ValueError('Array must be 1 or 2-dimensional')

		# Bad type
		else:
			raise TypeError('Cannot gate on {0}'.format(type(events)))
		

	def contains(self, events, region=None):

		# Check region
		if region is None:
			if self._default_region is not None:
				region = self._default_region
			else:
				raise ValueError('No default region, must give explicitly')
		elif region not in self._regions:
			raise ValueError('Invalid region {0}'.format(repr(region)))

		# Get data array based on type of events argument

		# FlowFrame
		if isinstance(events, FlowFrame):
			array = events.data[self._channels].values

		# Pandas DataFrame
		elif isinstance(events, pd.DataFrame):
			array = events[self._channels].values

		# Pandas Series - for 1D gates
		elif isinstance(events, pd.Series):
			if len(self._channels) != 1:
				raise ValueError('Can only apply 1D gate to pandas.Series')
			else:
				array = events.values[:,np.newaxis]

		# Numpy array - assume column in same order as channels
		elif isinstance(events, numpy.ndarray):

			# 2D array
			if events.ndim == 2:
				if events.shape[1] != len(self._channels):
					raise ValueError(
						'Number of columns in array must match number of '
						'channels in gate')
				else:
					array = events

			# 1D array - for 1D gates
			elif events.ndim == 1:
				if len(self._channels) != 1:
					raise ValueError('Can only apply 1D gate to 1D array')
				else:
					array = events.values[:,np.newaxis]

			# Bad shape
			else:
				raise ValueError('Array must be 1 or 2-dimensional')

		# Bad type
		else:
			raise TypeError('Cannot gate on {0}'.format(type(events)))

		# Process array
		return self._contains(array, region)

	def count(self, events, region=None):
		return np.sum(self.contains(events, region))

	def with_default(self, default_region):
		raise NotImplementedError()

	def __repr__(self):
		return '<{0} on {1}>'.format(type(self).__name__, repr(self.channels))

	# Bitwise operators on gates return CompositeGate or InvertedGates
	def __and__(self, other):
		return CompositeGate([self, other], 'and')
	def __or__(self, other):
		return CompositeGate([self, other], 'or')
	def __xor__(self, other):
		return CompositeGate([self, other], 'xor')
	def __invert__(self):
		return InvertedGate(self)

	def _contains(self, array, region):
		raise NotImplementedError()

	def _auto_id(self):
		return 'some id'


class SimpleGate(AbstractGate):

	def __init__(self, channels, default_region=None, ID=None):

		if default_region is None:
			default_region = 'in'

		super(SimpleGate, self).__init__(channels, regions={'in', 'out'},
			default_region=default_region, ID=ID)

	def _contains(self, array, region):
		if region == 'in':
			return self._inside(array)
		else:
			return ~self._inside(array)

	def _inside(self, array):
		raise NotImplementedError()
	
	def __invert__(self):
		other_region = 'out' if self._default_region == 'in' else 'out'
		return self.with_default(default_region=other_region)


class CompositeGate(SimpleGate):
	"""
	docs...
	"""

	def __init__(self, gates, op, ID=None):

		# Check value of op argument
		if op not in ['and', 'or', 'xor']:
			raise ValueError('op must be one of "and", "or", or "xor".')
		self._op = op

		# Check all gates have the same channels
		channels = next(iter(gates)).channels
		if not all(set(gate) == set(channels) for gate in gates):
			raise ValueError()

		# Parent constructor
		super(CompositeGate, self).__init__(channels, ID)


class InvertedGate(SimpleGate):

	def __init__(self, gate, region=None, ID=None):

		self._invert_gate = gate
		self._invert_region = region

		super(InvertedGate, self).__init__(gate.channels, default_region='in',
			ID=ID)

	def _inside(self, array):
		return self._invert_gate.contains(array, self._invert_region)

	def __invert__(self):
		return self._invert_gate.with_region(self._invert_region)

	def __repr__(self):
		gatestr = repr(self._invert_gate)

		if self._invert_region is not None:
			gatestr += ':' + repr(self._invert_region)

		return '<{0} of {1}>'.format(type(self).__name__, gatestr)
