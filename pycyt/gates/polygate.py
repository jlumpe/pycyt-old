import numpy as np

from bases import SimpleGate
from pycyt import math, util


class PolyGate(SimpleGate):

	def __init__(self, channels, vertices, **kwargs):

		if len(channels) != 2:
			raise ValueError('PolyGate must have exactly two channels')

		super(PolyGate, self).__init__(channels, **kwargs)

		if len(vertices) < 2:
			raise ValueError('Must have at least 3 vertices')

		# Process vertices
		self._vertices = []
		for vertex in vertices:

			# Convert to ndarray, remove extra axes
			vertex = np.squeeze(vertex)

			if vertex.shape != (2,):
				raise ValueError('Vertices must be 2-dimensional')

			self._vertices.append(vertex)

		# Check if polygon is convex
		self._is_convex, self._is_rh = math.is_poly_convex(self._vertices)

		# Compute bounding box
		self._bbox = [
			[f(v[i] for v in self._vertices) for f in (min, max)]
			for i in range(2)]

	@property
	def is_convex(self):
		return self._is_convex

	def _inside(self, array):

		contains = np.full(array.shape[0], True, dtype=np.bool)

		# Convex polygon can use faster algorithm
		if self._is_convex:

			# Loop over pairs of vertices (sides)
			for v1, v2 in util.cycle_adjacent(self._vertices, 2):

				# Vectors from vertex 1 to all test points
				dp = array - v1

				# Vector from vertex 1 to vertex 2
				dv = v2 - v1

				# Cross product between them
				cp = dp[:,0] * dv[1] - dp[:,1] * dv[0]

				# Reject where cp isn't positive (or negative if left-handed)
				contains &= (cp > 0) ^ self._is_rh

		# Non-convex is slower (there is probably a faster way though)
		else:
			
			# Loop over all points to test
			for i, point in enumerate(array):

				# Test against bounding box
				if not (self._bbox[0][0] < point[0] < self._bbox[0][1]):
					contains[i] = False
					continue
				if not (self._bbox[1][0] < point[1] < self._bbox[1][1]):
					contains[i] = False
					continue

				# Will cast a ray from the point in the positive x direction,
				# if it crosses an odd number of times the point is inside.
				# Note - special cases arise when the ray intersects a side
				# just at a vertex. If we count this as a regular side
				# intersection it will be counted twice, which is the same as
				# not counting it at all. Technically this will never ever
				# happen enough to make a difference in an analysis but I'm
				# being pedantic here. The solution is to count all rays
				# passing through a vertex as actually going just above the
				# vertex, forcing it to be consistently counted one way or
				# the other.
				in_p = False

				# Loop over 3-tuples of vertices (pairs of sides)
				# Will check the first side each loop but the 2nd is
				# sometimes needed if the ray intersects at a vertex.
				for v1, v2, v3 in util.cycle_adjacent(self._vertices, 3):

					# Translate to put v1 at origin
					p = point - v1
					v = v2 - v1

					# Bounding box of side in these coordinates
					left = min(v[0], 0)
					right = max(v[0], 0)
					bottom = min(v[1], 0)
					top = max(v[1], 0)

					# Skip if point entirely above or below side
					# Note we use >= on the top and < on the bottom, according
					# to the rule of counting exact intersection with a vertex
					# to being slightly above it. This also avoids counting
					# the case where the side is horizontal (v[1] == 0 and
					# top == bottom).
					if p[1] >= top or p[1] < bottom:
						continue

					# Skip if point is to right of side's bounding box
					if p[0] >= right:
						continue

					# Yes if point to left of side's bounding box
					if p[0] < left:
						in_p = not in_p
						continue

					# Point within bounding box - compare slopes
					if (v[1] > 0) == (v[0] * p[1] > v[1] * p[0]):
						in_p = not in_p
						continue

				# Put result in array
				contains[i] = in_p

		return contains
