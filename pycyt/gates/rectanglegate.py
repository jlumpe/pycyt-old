import numpy as np

from bases import SimpleGate


class RectangleGate(SimpleGate):

	def __init__(self, channels, ranges, **kwargs):

		super(RectangleGate, self).__init__(channels, **kwargs)

		if len(ranges) != self.ndim:
			raise ValueError('Number of ranges must match number of channels')

		self._ranges = []
		for range_ in ranges:

			bottom, top = tuple(range_)

			if bottom is not None:
				bottom = float(bottom)
			if top is not None:
				top = float(top)

			self._ranges.append((bottom, top))

	def _inside(self, array):

		contains = np.full(array.shape[0], True, dtype=np.bool)

		for col, (bottom, top) in enumerate(self._ranges):

			if bottom is not None:
				contains &= array[:,col] > bottom

			if top is not None:
				contains &= array[:,col] < top

		return contains
