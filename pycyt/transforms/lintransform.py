import numpy as np

from abstracttransform import AbstractTransform


class LinearTransform(AbstractTransform):

	__transform_names__ = ['lin', 'flin']

	def __init__(self, b=0, t=1, tb=0, tt=1):
		self._bottom = b
		self._top = t
		self._to_bottom = tb
		self._to_top = tt
		self._scale = float(tt - tb) / (t - b)

	@property
	def bottom(self):
		return self._bottom
	
	@property
	def top(self):
		return self._top

	@property
	def to_bottom(self):
		return self._to_bottom
	
	@property
	def to_top(self):
		return self._to_top
	
	@property
	def kwargs(self):
		return dict(b=self._bottom, t=self._top, tb=self._to_bottom,
			tt=self._to_top)

	@property
	def inverse(self):
		return LinearTransform(b=self._to_bottom, t=self._to_top,
			tb=self._bottom, tt=self._top)

	@property
	def label(self):
		return 'flin_{{{0:g}, {{0:g}}}'.format(self._bottom, self._top)

	def apply_array(self, array):
		return (array - self._bottom) * self._scale + self._to_bottom

	def array_in_domain(self, array):
		return np.ones_like(array, dtype=np.bool)
