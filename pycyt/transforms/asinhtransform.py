import numpy as np

from abstracttransform import AbstractTransform


class AsinhTransform(AbstractTransform):

	__transform_names__ = ['asinh', 'fasinh']

	def __init__(self, b=10, t=1, pd=4, nd=0):
		self._base = b
		self._top = t
		self._pos_decades = pd
		self._neg_decades = nd

		self._p1 = np.sinh(pd * np.log(b)) / t
		self._p2 = nd * np.log(b)
		self._p3 = 1. / ((pd + nd) * np.log(b))

	@property
	def base(self):
		return self._base

	@property
	def top(self):
		return self._top

	@property
	def pos_decades(self):
		return self._pos_decades
	
	@property
	def neg_decades(self):
		return self._neg_decades

	@property
	def kwargs(self):
		return dict(b=self._base, t=self._top, pd=self._pos_decades,
			nd=self._neg_decades)

	@property
	def label(self):
		return 'fasinh'

	def apply_array(self, array):
		return (np.arcsinh(array * self._p1) + self._p2) * self._p3

	def array_in_range(self, array):
		return np.ones_like(array, dtype=np.bool)
