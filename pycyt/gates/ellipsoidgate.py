import numpy as np

from bases import SimpleGate
from pycyt import math, util


class EllipsoidGate(SimpleGate):

	def __init__(self, channels, center, cov, **kwargs):

		super(EllipsoidGate, self).__init__(channels, **kwargs)

		# Convert center to ndarray and check
		self._center = np.squeeze(center)
		if self._center.shape != (self.ndim,):
			raise ValueError(
				'Center must be 1D array-like matching gate dimension')

		# Convert covariance matrix and check
		self._cov = np.squeeze(cov)
		if self._cov.ndim == 1:
			self._cov = np.diag(self._cov)
		if self._cov.shape != (self.ndim, self.ndim):
			raise ValueError(
				'Covariance matrix must be square matrix or array of '
				'diagonals matching gate dimension')
		try:
			assert np.all(np.isclose(self._cov, self._cov.transpose()))
			self._linv = np.linalg.cholesky(np.linalg.inv(self._cov))
		except (AssertionError, np.linalg.LinAlgError):
			raise ValueError(
				'Covariance matrix must be positive semi-definite')

	@property
	def center(self):
		return self._center

	@property
	def cov(self):
		return self._cov

	def copy(self, channels=None, center=None, cov=None, **kwargs):
		if channels is None:
			channels = self._channels
		if center is None:
			center = self._center
		if cov is None:
			cov = self._cov

		return EllipsoidGate(channels, center, cov, **kwargs)

	def _inside(self, array):
		"""So much better than the PolyGate, can do in two lines!"""

		# Multiply vectors from center by inverse of cholesky decomposition of
		# covariance matrix - this transforms the space into one where the
		# ellipsoid is the unit n-sphere
		d = (array - self._center).dot(self._linv)

		# Now just find which points are in the sphere
		return np.einsum('ij,ij->i', d, d) < 1


class EllipseGate(EllipsoidGate):

	def __init__(self, channels, center, axes, **kwargs):

		self._axes = np.asarray(axes)

		if 'theta' in kwargs:
			self._theta = kwargs.pop('theta')
		elif 'degrees' in kwargs:
			self._theta = kwargs.pop('degrees') * np.pi / 180
		else:
			self._theta = 0

		r = np.asarray([[np.cos(self._theta), 0], [np.sin(self._theta), 0]])
		r[0, 1] = -r[1, 0]
		r[1, 1] = r[0, 0]

		m = r.dot(np.diag(self._axes))
		cov = m.dot(m.transpose())

		super(EllipseGate, self).__init__(channels, center, cov, **kwargs)

	@property
	def axes(self):
		return self._axes

	@property
	def theta(self):
		return self._theta

	def copy(self, channels=None, center=None, axes=None, **kwargs):
		if channels is None:
			channels = self._channels
		if center is None:
			center = self._center
		if axes is None:
			axes = self._axes
		if 'theta' not in kwargs and 'angle' not in kwargs:
			kwargs['theta'] = self._theta

		return EllipseGate(channels, center, axes, **kwargs)
