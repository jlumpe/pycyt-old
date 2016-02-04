"""
Objects which model an abstract multidimensional space which contains data
points.
"""


__all__ = [
	'IncompatibleDataSpaceException',
	'Parameter',
	'Dimension',
	'DataSpace'
]


class IncompatibleDataSpaceException(Exception):
	"""
	Raised when a data space does not have the expected dimensions or
	parameters.
	"""
	pass


class Parameter(object):
	"""
	Corresponds to a single dimension of a raw Flow Cytometer measurement.

	This class encapsulates the concept of a parameter as it is used in the
	FCS3.1 standard - in a list mode data file there is exactly one recorded
	value per parameter per event. Typically corresponds to a single
	detector on a Flow Cytometer and is synonymous with the term "channel",
	but also includes the "Time" parameter.

	A parameter is uniquely defined by its name. Parameters form the basis
	for a data space.
	"""

	def __init__(self, name):
		"""
		Args:
			name: basestring. Name of parmeter.
		"""
		self._name = name

	def __hash__(self):
		return hash(self._name)

	def __eq__(self, other):
		return isinstance(other, Parameter) and self._name == other._name

	def __repr__(self):
		return '{0}({1})'.format(type(self).__name__, self._name)

	@property
	def name(self):
		return self._name


class Dimension(object):

	def __init__(self, parameter, transform=None):
		pass


class DataSpace(object):

	def __init__(self, dimensions, compensation=None):
		if not all(isinstance(d, Dimension) for d in dimensions):
			raise TypeError('dimensions must be sequence of Dimension')
		self._dimensions = tuple(dimensions)

	def __len__(self):
		return len(self._dimensions)

	def __iter__(self):
		return iter(self._dimensions)

	def __eq__(self, other):
		pass

	@property
	def dimensions(self):
		return self._dimensions

	@property
	def parameters(self):
		return tuple(dim.channel for d in self._dimensions)

	@property
	def ndim(self):
		return len(self)

	def subset_of(self, other):
		pass

	def compatible_with(self, other):
		pass
