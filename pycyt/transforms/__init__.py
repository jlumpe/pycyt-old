import numpy as np

from pycyt.data import TableInterface

from abstracttransform import AbstractTransform

from logtransform import LogTransform
from lintransform import LinearTransform
from asinhtransform import AsinhTransform


def by_name(name, **kwargs):
	"""
	Gets a registered transform by name and instantiates it with default
	arguments or with 
	"""
	if name in AbstractTransform.__registered_transforms__:
		return AbstractTransform.__registered_transforms__[name](**kwargs)
	else:
		raise KeyError('No registered transform {0}'.format(name))


def parse_transform_arg(arg):
	"""
	Parses a transformation argument in one of several different formats and
	returns an instance of a subclass of AbstractTransform. Can be an actual
	instance of AbstractTransform, in which case it is returned unchanged,
	a name of a registered transform, or a 2-tuple consisting of a name and
	dict of kwargs for transform constructor.
	"""
	if isinstance(arg, AbstractTransform):
		return arg
	elif isinstance(arg, basestring):
		return by_name(arg)
	elif isinstance(arg, tuple):
		name, kwargs = arg
		return by_name(name, **kwargs)
	elif arg is None:
		return None
	else:
		raise TypeError(
			'Invalid type for transformation: {0}'
			.format(type(arg))
			)


def parse_transforms_list(transforms, n):
	if isinstance(transforms, list):
		if len(transforms) != n:
			raise ValueError(
				'Got {0} transforms, expected {1}'
				.format(len(transforms), n)
				)
		return map(parse_transform_arg, transforms)
	else:
		return [parse_transform_arg(transforms)] * n


def transform(data, *args, **kwargs):

	# Sort out positional arguments and get table interface to data
	if len(args) == 1:
		targ, = args
		table = TableInterface(data)
	elif len(args) ==2:
		columns, targ = args
		table = TableInterface(data, columns)
	else:
		raise TypeError('*args must be ([columns,] transforms)')

	# Sort out keyword arguments
	drop = kwargs.pop('drop', False)
	asarray = kwargs.pop('asarray', False)
	if len(kwargs) > 1:
		raise TypeError(
			'Unknown keyword argument {0}'
			.format(repr(kwargs.keys()[0]))
			)

	# Transform may be None, in which case do nothing
	if targ is None:
		if asarray:
			return table.data
		else:
			return table

	# Get the data as a 2d array
	array = table.data

	# If list, need to transform columns individually
	if isinstance(targ, list):

		# Check length
		if len(targ) != table.ncol:
			raise ValueError(
				'Number of transformations does not match number of columns '
				'in data'
				)

		# Parse arguments to transform objects
		transforms = map(parse_transform_arg, targ)

		# Drop rows not within range of transformation
		if drop:
			in_range = np.full(table.nrow, True, dtype=np.bool)
			for c, transform in enumerate(transforms):
				if transform is not None:
					in_range &= transform.array_in_range(array[:, c])
			array = array[in_range, :]

		# Perform transformations
		transformed = array.copy()
		for c, transform in enumerate(transforms):
			if transform is not None:
				transformed[:, c] = transform.apply_array(array[:, c])

	# Else transform the whole array at once
	else:

		# Parse argument
		transform = parse_transform_arg(targ)

		# Drop rows
		if drop:
			in_range = np.all(transform.array_in_range(array), axis=1)
			array = array[in_range, :]

		# Transform array
		transformed = transform.apply_array(array)

	# Return raw array or in original format
	if asarray:
		return transformed
	else:
		if drop:
			return table.with_data(transformed, in_range)
		else:
			return table.with_data(transformed)
