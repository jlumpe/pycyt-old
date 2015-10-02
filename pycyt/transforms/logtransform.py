import numpy as np

from abstracttransform import AbstractTransform


class LogTransform(AbstractTransform):

	__transform_names__ = ['log', 'flog']

	def __init__(self, b=10, d=1, t=1, s=False):
		self._base = b
		self._decades = d
		self._top = t
		self._shift = 1 if s else 0

		self._simple = (d == 1 and t ==1 and not s)
		self._invtop = 1. / t
		self._invdec = 1. / d
		self._scale = t / np.log(b)

	@property
	def base(self):
		return self._base

	@property
	def decades(self):
		return self._decades
	
	@property
	def top(self):
		return self._top

	@property
	def shifted(self):
		return self._shift == 1

	@property
	def kwargs(self):
		return dict(b=self._base, d=self._decades, t=self._top,
			s=self.shifted)

	@property
	def label(self):
		if self._simple:
			return 'log_{{{0:g}}}'.format(self._base)
		else:
			return 'flog_{{{0:g}}}'.format(self._base)

	def __repr__(self):
		if self._simple:
			return '{0}(b={1})'.format(type(self).__name__, repr(self._base))
		else:
			return super(LogTransform, self).__repr__()

	def apply_array(self, array):
		if self._simple:
			return np.log(array) * self._scale
		else:
			t = np.log(array * self._invtop) * self._invdec + self._shift
			return 

	def array_in_range(self, array):
		return array > 0
