from abstracttransform import AbstractTransform

from logtransform import LogTransform


def by_name(name):
	if name in AbstractTransform.__registered_transforms__:
		return AbstractTransform.__registered_transforms__[name]()
	else:
		raise KeyError('No registered transform {0}'.format(name))
