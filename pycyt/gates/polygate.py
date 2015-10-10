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

	@property
	def bbox(self):
		return [list(r) for r in self._bbox]

	@property
	def vertices(self):
		return self._vertices[:]

	def copy(self, channels=None, vertices=None, **kwargs):
		if channels is None:
			channels = self._channels
		if vertices is None:
			vertices = self._vertices

		return PolyGate(channels, vertices, **kwargs)

	def _inside(self, array):

		# Convex polygon can use faster algorithm
		if self._is_convex:

			contains = np.full(array.shape[0], True, dtype=np.bool)

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

			return contains

		# Non-convex is slower (there is probably a faster way though)
		else:

			# Test against bounding box
			in_box = np.ones(array.shape[0], dtype=np.bool)
			in_box &= array[:,0] > self._bbox[0][0]
			in_box &= array[:,0] < self._bbox[0][1]
			in_box &= array[:,1] > self._bbox[1][0]
			in_box &= array[:,1] < self._bbox[1][1]

			box_points = array[in_box, :]

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
			in_p = np.zeros(box_points.shape[0], dtype=np.bool)

			# Loop over 3-tuples of vertices (pairs of sides)
			# Will check the first side each loop but the 2nd is
			# sometimes needed if the ray intersects at a vertex.
			for v1, v2, v3 in util.cycle_adjacent(self._vertices, 3):

				# Indices of points currently looking at
				ci = np.arange(box_points.shape[0])

				# Translate to put v1 at origin
				t_points = box_points - v1
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
				which = (t_points[:, 1] >= top) |  (t_points[:, 1] < bottom)
				t_points = t_points[~which, :]
				ci = ci[~which]

				# Skip if point is to right of side's bounding box
				which = t_points[:, 0] >= right
				t_points = t_points[~which, :]
				ci = ci[~which]

				# Yes if point to left of side's bounding box
				which = t_points[:, 0] < left
				in_p[ci[which]] = ~in_p[ci[which]]
				t_points = t_points[~which, :]
				ci = ci[~which]

				# Point within bounding box - compare slopes
				which = (v[1] > 0) == (v[0] * t_points[:, 1] > v[1] * t_points[:, 0])
				in_p[ci[which]] = ~in_p[ci[which]]

			contains = np.zeros(array.shape[0], dtype=np.bool)
			contains[in_box] = in_p
			return contains
