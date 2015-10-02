import numpy as np

from pycyt.util import AutoIDMixin, AutoIDMeta
from pycyt.data import TableInterface


class AbstractTransformMeta(AutoIDMeta):

	def __init__(cls, name, bases, dct):

		# Base class, create registry
		if not hasattr(cls, '__registered_transforms__'):
			cls.__registered_transforms__ = dict()

		# Derived class, add to registry if has name
		elif hasattr(cls, '__transform_name__'):

			registry = cls.__registered_transforms__
			tname = cls.__transform_name__

			# Raise error if already registered
			if tname in registry:
				raise AttributeError(
					'Transformation name "{0}" is already registered'
					.format(tname))
			else:
				registry[tname] = cls


class AbstractTransform(AutoIDMixin):
	"""
	Abstract base class for data transforms.
	"""

	__metaclass__ = AbstractTransformMeta

	def __call__(self, x):

		if np.isscalar(x):
			return self.apply_array(np.asarray(x))[0]

		else:

			# Get TableInterface for array
			table = TableInterface(x)
			array = table.data

			# Get rows which are in range
			in_range = np.all(self.array_in_range(array), axis=1)

			# Get tranformed data
			transformed = self.apply_array(array[in_range])
			
			# Return passed table rows in original format
			return table.with_data(transformed, in_range)

	def in_range(self, x):

		if np.isscalar(x):
			return bool(self.array_in_range(np.asarray(x))[0])

		else:

			# Get TableInterface for array
			table = TableInterface(x)

			# Get rows which are in range
			return np.all(self.array_in_range(table.data), axis=1)

	def __add__(self, other):
		if not isinstance(other, AbstractTransform):
			raise TypeError(other)
		return CompoundTransform(self, other)

	@property
	def label(self):
		return type(self).__name__
	
	def apply_array(self, array):
		raise NotImplementedError()

	def array_in_range(self, array):
		raise NotImplementedError()


class CompoundTransform(AbstractTransform):

	def __init__(self, *args):
		pass
