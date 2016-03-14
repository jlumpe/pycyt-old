import numpy as np
import pandas as pd

from pycyt import FlowFrame
from pycyt.util import AutoIDMixin
from pycyt.data import TableInterface


class AbstractGate(AutoIDMixin):
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
			self._ID = self._auto_ID()
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
	def ID(self):
		return self._ID

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

	@property
	def bbox(self):
		raise NotImplementedError()
	
	def __call__(self, events, region=None):

		# Check region
		region = self.__get_region(region)

		# Get TableInterface for events
		table = self.__get_table(events)

		# Pass/reject rows of table
		in_gate = self._contains(table.data, region)
		
		# Return passed table rows in original format
		return table.get_rows(in_gate)

	def contains(self, events, region=None):

		# Check region
		region = self.__get_region(region)

		# Get TableInterface for events
		table = self.__get_table(events)

		# Process table
		return self._contains(table.data, region)

	def count(self, events, region=None):
		return np.sum(self.contains(events, region))

	def frac(self, events, region=None):
		inside = self.contains(events, region)
		return float(np.sum(inside)) / len(inside)

	def copy(self, **kwargs):
		raise NotImplementedError()

	def __repr__(self):
		return '<{0} {1} on {2}>'.format(type(self).__name__,
			repr(self._ID), repr(self.channels))

	# Bitwise operators on gates return BooleanGate or InvertedGates
	def __and__(self, other):
		return BooleanGate([self, other], 'and')
	def __or__(self, other):
		return BooleanGate([self, other], 'or')
	def __xor__(self, other):
		return BooleanGate([self, other], 'xor')
	def __invert__(self):
		return InvertedGate(self)

	def _contains(self, array, region):
		raise NotImplementedError()

	def __get_table(self, events):
		"""
		Gets TableInterface for events, if unable raises informative error
		"""
		try:
			return TableInterface(events, self._channels)
		except KeyError:
			raise ValueError('All gate channels must be in events argument')
		except ValueError:
			raise ValueError('Invalid shape for events argument')
		except TypeError:
			raise TypeError('Cannot gate on {0}'.format(type(events)))

	def __get_region(self, region):
		"""Gets region if allowed, otherwise raises error"""
		if region is None:
			if self._default_region is not None:
				return self._default_region
			else:
				raise ValueError('No default region, must give explicitly')
		elif region not in self._regions:
			raise ValueError('Invalid region {0}'.format(repr(region)))
		else:
			return region


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


class BooleanGate(SimpleGate):
	"""
	docs...
	"""

	def __init__(self, gates, op, **kwargs):

		# Check value of op argument
		if op not in ['and', 'or', 'xor']:
			raise ValueError('op must be one of "and", "or", or "xor".')
		self._op = op

		# Check all gates have the same channels
		channels = next(iter(gates)).channels
		if not all(set(gate.channels) == set(channels) for gate in gates):
			raise ValueError(
				'All gates in BooleanGate must be defined on the same '
				'channels')

		# Parent constructor
		super(BooleanGate, self).__init__(channels, **kwargs)

		# Flatten composite gates
		self._gates = []
		for gate in gates:
			if isinstance(gate, BooleanGate):
				self._gates += gate.gates
			else:
				self._gates.append(gate)

		# Channel permutations
		self._ch_perm = []
		for gate in self._gates:
			if gate.channels == self.channels:
				self._ch_perm.append(None)
			else:
				self._ch_perm = [gate.channels.index(c) for c
					in self._channels]

	@property
	def gates(self):
		return self._gates[:]

	@property
	def op(self):
		return self._op

	def copy(self, gates=None, op=None, **kwargs):
		if gates is None:
			gates = self._gates
		if op is None:
			op = self._op

		return BooleanGate(gates, op, **kwargs)

	def _inside(self, array):

		# Initialize array with op identity
		if self._op == 'and':
			in_composite = np.full(array.shape[0], True, dtype=np.bool)
		else:
			in_composite = np.full(array.shape[0], False, dtype=np.bool)
		
		# Loop through gates
		for gate, ch_perm in zip(self._gates, self._ch_perm):

			# Get events in gate
			if ch_perm is None:
				in_gate = gate.contains(array)
			else:
				in_gate = gate.contains(array[:, ch_perm])

			# Apply op
			if self._op == 'and':
				in_composite &= in_gate
			elif self._op == 'or':
				in_composite |= in_gate
			elif self._op == 'xor':
				in_composite = in_composite != in_gate

		return in_composite


class InvertedGate(SimpleGate):

	def __init__(self, gate, region=None, **kwargs):

		self._invert_gate = gate
		self._invert_region = region

		super(InvertedGate, self).__init__(gate.channels, **kwargs)

	def _inside(self, array):
		return ~self._invert_gate.contains(array, self._invert_region)

	def __invert__(self):
		return self._invert_gate.copy(region=self._invert_region)

	def __repr__(self):
		gatestr = repr(self._invert_gate)

		if self._invert_region is not None:
			gatestr += ':' + repr(self._invert_region)

		return '<{0} of {1}>'.format(type(self).__name__, gatestr)
