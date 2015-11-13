import math

from pycyt.gates import EllipseGate
from pycyt.gatingml import (parse as parse_gatingml, nsmap as gatingml_nsmap,
	formatns)


def parse_gate(elem, ID=None):

	if ID is None:
		ID = elem.attrib.get(formatns('gating', 'id'), None)

	gate_elem = elem[0]

	# Flowjo pretends to follow Gating-ML but does ellipse gates weird
	if gate_elem.tag == formatns('gating', 'EllipsoidGate'):

		# Channels
		channels = []
		for dim_elem in gate_elem.findall('gating:dimension', gatingml_nsmap):
			fcs_dim_elem = dim_elem.find('data-type:fcs-dimension',
				gatingml_nsmap)
			channels.append(fcs_dim_elem.get(formatns('data-type', 'name')))

		# Foci
		foci = []
		foci_elem = gate_elem.find('gating:foci', gatingml_nsmap)
		for vertex_elem in foci_elem.findall('gating:vertex', gatingml_nsmap):
			focus = []
			for coord_elem in vertex_elem.findall('gating:coordinate',
					gatingml_nsmap):
				focus.append(float(coord_elem.get(
					formatns('data-type', 'value'))))
			foci.append(focus)

		# Edges
		edges = []
		edge_elem = gate_elem.find('gating:edge', gatingml_nsmap)
		for vertex_elem in edge_elem.findall('gating:vertex', gatingml_nsmap):
			edge = []
			for coord_elem in vertex_elem.findall('gating:coordinate',
					gatingml_nsmap):
				edge.append(float(coord_elem.get(
					formatns('data-type', 'value'))))
			edges.append(edge)

		# Math
		center = [sum(c) / 2. for c in zip(*edges[:2])]
		major = math.sqrt(sum([(e[1] - e[0])**2 for e in zip(*edges[:2])]))
		focus_dist = math.sqrt(sum([(f[1] - f[0])**2 for f in zip(*foci)]))
		minor = math.sqrt(major ** 2 - focus_dist ** 2)
		theta = math.atan2(edges[0][0] - edges[1][0],
			edges[0][1] - edges[1][1])

		# Create gate
		return EllipseGate(channels, center, [major, minor], theta=theta,
			ID=ID)

	# Others should be the same
	else:
		return parse_gatingml(gate_elem, ID=ID)
