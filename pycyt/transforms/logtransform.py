import numpy as np

from abstracttransform import AbstractTransform


class LogTransform(AbstractTransform):

	__transform_name__ = 'log'

	def __init__(self, base=10):
		self._base = base
		self._scale = 1. / np.log(base)

	@property
	def base(self):
		return self._base

	@property
	def label(self):
		return 'log_{{{0:g}}}'.format(self._base)

	def apply_array(self, array):
		return np.log(array) * self._scale

	def array_in_range(self, array):
		return array > 0
