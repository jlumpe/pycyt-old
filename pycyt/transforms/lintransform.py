import numpy as np

from abstracttransform import AbstractTransform


class LinearTransform(AbstractTransform):

	__transform_names__ = ['lin', 'flin']

	def __init__(self, b=0, t=1):
		self._bottom = b
		self._top = t
		self._invrange = 1. / (t - b)

	@property
	def bottom(self):
		return self._bottom
	
	@property
	def top(self):
		return self._top
	
	@property
	def range(self):
		return self._range

	@property
	def kwargs(self):
		return dict(b=self._bottom, t=self._top)

	@property
	def label(self):
		return 'flin_{{{0:g}, {{0:g}}}'.format(self._bottom, self._top)

	def apply_array(self, array):
		return (array - self._bottom) * self._invrange

	def array_in_range(self, array):
		return np.ones_like(array, dtype=np.bool)
