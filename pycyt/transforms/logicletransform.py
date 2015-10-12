import numpy as np
from scipy.special import lambertw

from abstracttransform import AbstractTransform


class BiexponentialTransform(AbstractTransform):

	def __init__(self, b=10, t=1, pd=4, ld=1, nd=0):
		self._base = b
		self._top = t
		self._pos_decades = pd
		self._lin_decades = ld
		self._neg_decades = nd

		if b <= 1:
			raise ValueError('b must be > 1')
		if pd <= 0:
			raise ValueError('pd must be positive')
		if not 0 <= ld <= pd / 2:
			raise ValueError('ld must be >= 0 and <= pd/2')
		if not  -ld <= nd <= pd - 2 * ld:
			raise ValueError('nd must be >= -ld and <= pd - 2*ld')

		# This is all from the Gating-ML 2.0 standard:
		w = float(ld) / (pd + nd)
		x2 = float(nd) / (pd + nd)
		x1 = x2 + w
		x0 = x2 + 2 * w

		self._b = (pd + nd) * np.log(b)

		# Math time! Gating-ML says the d parameter for the biexponential
		# function is defined by:
		#     2 * ( ln(d) - ln(b) ) + w * (d + b) = 0
		# with b and w as above. Rearrange to
		#     2*ln(b) - w*b = w*d + 2*ln(d)
		# and define
		#     x = d
		#     y = 2*ln(b) - w*b
		#     c_1 = w
		#     c_2 = 2
		# to get an equation of the form
		#     y = c_1*x + c_2*ln(x)
		# (just so we can solve the general case, because math is fun! Right?)
		# Now solve for x:
		#     y/c_2 = c_1/c_2 * x + ln(x)
		#     exp(y/c_2) = x * exp(c_1/c_2 * x)
		# which we can solve using the Lambert W function as
		#     x = c_2/c_1 * W( c_1/c_2 * exp(y/c_2) )
		# I thought it was fun...
		y = 2. * np.log(self._b) - w * self._b
		self._d = 2. / w * lambertw(.5 * w * np.exp(.5 * y))

		assert not np.iscomplex(self._d)
		self._d = self._d.real

		# And the rest is directly from the Gating-ML spec:
		c_a = np.exp(x0 * (self._b + self._d))
		f_a = np.exp(self._b * x1) - c_a / np.exp(self._d * x1)
		self._a = t / (np.exp(self._b) - f_a - c_a / np.exp(self._d))
		self._c = c_a * self._a
		self._f = f_a * self._a

		# Make sure we ended up with real-values parameters
		param_ok = lambda v: not np.isnan(v) and np.isfinite(v)
		assert all(param_ok(getattr(self, '_' + n)) for n in 'abcdf')

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
	def lin_decades(self):
		return self._lin_decades
	
	@property
	def neg_decades(self):
		return self._neg_decades

	@property
	def kwargs(self):
		return dict(b=self._base, t=self._top, pd=self._pos_decades,
			ld=self._lin_decades, nd=self._neg_decades)

	@property
	def inverse(self):
		return LogicleTransform(**self.kwargs)

	def apply_array(self, array):
		return self._a * np.exp(self._b * array) \
			- self._c * np.exp(-self._d * array) \
			- self._f

	def array_in_domain(self, array):
		return np.ones_like(array, dtype=np.bool)


class LogicleTransform(AbstractTransform):

	__transform_names__ = ['logicle']

	def __init__(self, b=10, t=1, pd=4, ld=1, nd=0, niter=10):
		self._base = b
		self._top = t
		self._pos_decades = pd
		self._lin_decades = ld
		self._neg_decades = nd

		self._niter = niter

		self._inverse = BiexponentialTransform(b=b, t=t, pd=pd, ld=ld, nd=nd)

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
	def lin_decades(self):
		return self._lin_decades
	
	@property
	def neg_decades(self):
		return self._neg_decades

	@property
	def kwargs(self):
		return dict(b=self._base, t=self._top, pd=self._pos_decades,
			ld=self._lin_decades, nd=self._neg_decades)

	@property
	def inverse(self):
		return self._inverse

	@property
	def label(self):
		return 'logicle'

	def apply_array(self, array):
		# Grab the hidden parameters from the biexponential transform
		a, b, c, d, f = tuple(getattr(self._inverse, '_' + n) for n in 'abcdf')

		# Get an inital guess
		x = np.zeros_like(array, dtype=np.float64)

		# Divide data into 3 regions, those where the value of the function
		# will be greater than, less than, or close to zero.
		w = .2
		r_p = np.logical_and(array > self._inverse(w), array > -f)
		r_n = np.logical_and(array < self._inverse(-w), array < -f)

		# Generate guesses by assuming one or both of the exponential
		# terms in the inverse to be close to 0 and inverting the
		# remaining one
		x[r_p] = np.log((array[r_p] + f) / a) / b
		x[r_n] = np.log((array[r_n] + f) / -c) / -d

		# Now, apply Newton's method to iteratively improve the guess
		tol = 1e-9
		for i in range(self._niter):
			y = self._inverse(x) - array
			dy = a * b * np.exp(b * x) + c * d * np.exp(-d * x)

			t = np.abs(dy) > tol
			x[t] -= (y / dy)[t]

		return x

	def array_in_domain(self, array):
		return np.ones_like(array, dtype=np.bool)
