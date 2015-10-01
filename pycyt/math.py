import numpy as np

import util


def is_poly_convex(vertices):
	"""
	Checks if a polygon is convex and if so, if it is right-handed.
	"""

	pos = None

	for v1, v2, v3 in util.cycle_adjacent(vertices, 3):

		d1 = v2 - v1
		d2 = v3 - v2

		cp = d1[0] * d2[1] - d1[1] * d2[0]

		if pos is None:
			pos = cp > 0

		elif (pos and cp < 0) or (not pos and cp > 0):
			return False, None

	return True, pos
