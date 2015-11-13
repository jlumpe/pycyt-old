from pycyt.gates import *


# XML namespace map for Gating-ML standard
nsmap = {
	'gating': 'http://www.isac-net.org/std/Gating-ML/v2.0/gating',
	'transforms': 'http://www.isac-net.org/std/Gating-ML/v2.0/transformations',
	'data-type': 'http://www.isac-net.org/std/Gating-ML/v2.0/datatypes'
}


def formatns(ns, name):
	return '{{{0}}}{1}'.format(nsmap[ns], name)


def parse(elem, ID=None):

	# Rectangle gate
	if elem.tag == formatns('gating', 'RectangleGate'):

		if ID is None:
			ID = elem.attrib.get(formatns('gating', 'id'), None)

		channels = []
		ranges = []

		# Channels and ranges
		for dim_elem in elem.findall('gating:dimension', nsmap):
			r = [
				float(dim_elem.get(formatns('gating', 'min'))),
				float(dim_elem.get(formatns('gating', 'max')))
				]
			ranges.append(r)
			fcs_dim_elem = dim_elem.find('data-type:fcs-dimension', nsmap)
			channels.append(fcs_dim_elem.get(formatns('data-type', 'name')))

		return RectangleGate(channels, ranges, ID=ID)

	# Polygon gate
	elif elem.tag == formatns('gating', 'PolygonGate'):

		if ID is None:
			ID = elem.attrib.get(formatns('gating', 'id'), None)

		# Channels
		channels = []
		for dim_elem in elem.findall('gating:dimension', nsmap):
			fcs_dim_elem = dim_elem.find('data-type:fcs-dimension', nsmap)
			channels.append(fcs_dim_elem.get(formatns('data-type', 'name')))

		# Vertices
		vertices = []
		for vertex_elem in elem.findall('gating:vertex', nsmap):
			coords = []
			for coord_elem in vertex_elem.findall('gating:coordinate', nsmap):
				coords.append(float(coord_elem.get(
					formatns('data-type', 'value'))))
			vertices.append(tuple(coords))

		return PolyGate(channels, vertices, ID=ID)

	# Ellipsoid gate
	elif elem.tag == formatns('gating', 'EllipsoidGate'):

		if ID is None:
			ID = elem.attrib.get(formatns('gating', 'id'), None)

		# Channels
		channels = []
		for dim_elem in elem.findall('gating:dimension', nsmap):
			fcs_dim_elem = dim_elem.find('data-type:fcs-dimension', nsmap)
			channels.append(fcs_dim_elem.get(formatns('data-type', 'name')))

		# Mean/center coordinates
		mean = []
		mean_elem = elem.find('gating:mean', nsmap)
		for coord_elem in mean_elem.findall('gating:coordinate', nsmap):
			mean.append(float(coord_elem.get(formatns('data-type', 'value'))))

		# Covariance matrix
		cov = []
		cov_elem = elem.find('gating:covarianceMatrix', nsmap)
		for row_elem in cov_elem.findall('gating:row', nsmap):
			row = []
			for entry_elem in row_elem.findall('gating:entry', nsmap):
				row.append(float(entry_elem.get(
					formatns('data-type', 'value'))))
			cov_elem.append(row)

		# TODO - radius!

		return EllipsoidGate(channels, mean, cov, ID=ID)

	# Quadrant gate
	elif elem.tag == formatns('gating', 'QuadrantGate'):
		raise NotImplementedError('QuadrantGate not yet implemented')

	# Boolean gate
	elif elem.tag == formatns('gating', 'BooleanGate'):
		raise ValueError('Cannot create BooleanGate in isolation')

	# Bad tag
	else:
		raise ValueError('Cannot parse tag "{0}"'.format(elem.tag))
