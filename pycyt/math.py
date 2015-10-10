import numpy as np

import util


def is_poly_convex(vertices):
	"""
	Checks if a polygon is convex and if so, if it is right-handed.
	"""

	rh = None
	theta = 0

	for v1, v2, v3 in util.cycle_adjacent(vertices, 3):

		d1 = v2 - v1
		d2 = v3 - v2

		d_theta = np.arctan2(
			d1[0] * d2[1] - d1[1] * d2[0],
			d1[0] * d2[0] + d1[1] * d2[1]
			)

		if rh is None:
			rh = d_theta > 0
		elif (rh and d_theta < 0) or (not rh and d_theta > 0):
			return False, None

		theta += d_theta
		if abs(theta) > (np.pi * 2.2):
			return False, None

	return True, rh
