import numpy as np

from abstracttransform import AbstractTransform


class LogTransform(AbstractTransform):

	__transform_names__ = ['log', 'flog']

	def __init__(self, b=10, d=1, t=1, s=False):
		self._base = b
		self._decades = d
		self._top = t
		self._shifted = s

		self._scale = 1. / (d * np.log(b))
		self._shift = -np.log(t) * self._scale
		if s:
			self._shift += 1

		self._simple = (d == 1 and t ==1 and not s)

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
		return self._shifted

	@property
	def kwargs(self):
		return dict(b=self._base, d=self._decades, t=self._top,
			s=self._shifted)

	@property
	def inverse(self):
		return ExponentialTransform(**self.kwargs)

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
		return np.log(array) * self._scale + self._shift

	def array_in_domain(self, array):
		return array > 0


class ExponentialTransform(AbstractTransform):

	def __init__(self, b=10, d=1, t=1, s=False):
		self._base = b
		self._decades = d
		self._top = t
		self._shifted = s

		self._invscale = d * np.log(b)
		self._shift = -np.log(t) / self._invscale
		if s:
			self._shift += 1

		self._simple = (d == 1 and t ==1 and not s)

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
		return self._shifted

	@property
	def kwargs(self):
		return dict(b=self._base, d=self._decades, t=self._top,
			s=self._shifted)

	@property
	def inverse(self):
		return LogTransform(**self.kwargs)

	def apply_array(self, array):
		return np.exp((array - self._shift) * self._invscale)

	def array_in_domain(self, array):
		return np.ones_like(array, dtype=np.bool)
