import os

import numpy as np
from scipy import ndimage
import matplotlib as mpl
from matplotlib import pyplot as plt
from pkg_resources import resource_filename

from pycyt.data import TableInterface
from pycyt.transforms import (transform as apply_transform,
	parse_transform_arg, parse_transforms_list)


rcfile = os.path.realpath(resource_filename('pycyt', 'matplotlibrc'))

def use_style():
	mpl.style.use(rcfile)


class ScaleMapper(object):

	def __init__(self, from_range, to_range):
		self.from_range = from_range
		self.to_range = to_range
		self.from_bottom = from_range[0]
		self.to_bottom = to_range[0]
		self.scale = (to_range[1] - to_range[0]) / \
			(from_range[1] - from_range[0])

	def __call__(self, x):
		if hasattr(x, '__iter__'):
			return [self(e) for e in x if self.in_domain(e)]
		else:
			return (x - self.from_bottom) * self.scale + self.to_bottom

	def in_domain(self, x):
		return self.from_range[0] <= x <= self.from_range[1]


def format_axis_label(lab, transform=None):
	if transform is None:
		return lab
	else:
		return r'${0}(\mathrm{{{1}}})$'.format(transform.label, lab)

def plot_comp_matrix(matrix, channels, ax=None):

	if ax is None:
		ax = plt

	im = ax.imshow(matrix, interpolation='none')

	plt.tick_params(
		axis='both',
		which='both',
		bottom='off',
		top='off',
		left='off',
		right='off',
		labelbottom='off',
		labeltop='on')

	ax.set_xticks(range(len(channels)))
	ax.set_yticks(range(len(channels)))
	ax.set_xticklabels(channels, rotation=45)
	ax.set_yticklabels(channels)

	plt.colorbar(im)


def bin2d(data, transform=None, range=None, bins=256):

	if transform is not None:
		array = apply_transform(data, transform, drop=True, asarray=True)
	else:
		array = TableInterface(data, 2).data

	x = array[:,0]
	y = array[:,1]

	return np.histogram2d(x, y, range=range, bins=bins)


def density2d(
		data,
		transform=None,
		range=None,
		bins=256,
		ax=None,
		**kwargs):

	if ax is None:
		ax = plt.gca()

	if 'labels' not in kwargs:
		table = TableInterface(data, 2)
		if table.column_names is not None:
			transforms = parse_transforms_list(transform, 2)
			labels = [format_axis_label(c, t) for c, t
				in zip(table.column_names, transforms)]
	else:
		labels = kwargs.pop('labels')

	hist, xedges, yedges = bin2d(data, transform, range=range, bins=bins)

	cutoff = kwargs.pop('cutoff', 99.5)
	if cutoff is not None:
		top = np.percentile(hist, cutoff)
		hist[hist > top] = top

	if kwargs.pop('log', False):
		img_hist = np.ma.array(np.log(hist), mask=(hist==0)).transpose()
	else:
		img_hist = np.ma.array(hist, mask=(hist==0)).transpose()

	extent = [xedges[0], xedges[-1], yedges[0], yedges[-1]]

	imgargs = dict(origin='lower', extent=extent, interpolation='none',
		aspect='auto', cmap='afmhot')
	imgargs.update(kwargs)

	img = ax.imshow(img_hist, **imgargs)

	if labels is not None:
		ax.set_xlabel(labels[0])
		ax.set_ylabel(labels[1])

	return img


def hist(data, *args, **kwargs):

	# Sort out positional arguments and get data
	if len(args) == 1:
		transform, = args
		column = None
	elif len(args) ==2:
		column, transform = args
		data = TableInterface(data, [column]).data.flatten()
	elif len(args) == 0:
		transform = None
		column = None
	else:
		raise TypeError('*args must be ([[column,] transform])')

	if 'ax' in kwargs:
		ax = kwargs.pop('ax')
	else:
		ax = plt.gca()

	if transform is not None:
		transform = parse_transform_arg(transform)
		array = transform(data, drop=True)
	else:
		array = data

	if 'xlab' in kwargs:
		xlab = kwargs.pop('xlab')
		if xlab is not None:
			ax.set_xlabel(xlab)
	elif column is not None:
		ax.set_xlabel(format_axis_label(column, transform))

	if 'ylab' in kwargs:
		ylab = kwargs.pop('ylab')
		if ylab is not None:
			ax.set_ylabel(ylab)
	else:
		if kwargs.get('normed', False):
			ylab = 'Density'
		else:
			ylab = 'Count'
		if kwargs.get('log', False):
			ylab = r'$log_{{10}}(\mathrm{{{0}}})$'.format(ylab)
		ax.set_ylabel(ylab)

	histargs = dict(bins=64, histtype='stepfilled')
	histargs.update(kwargs)

	h = ax.hist(array, **histargs)

	return h


def matrix(data, transform=None, figure=None):

	if figure is None:
		figure = plt.figure()

	# Get data in standard table format
	table = TableInterface(data)
	array = table.data

	# Apply transforms, get points in range but don't drop yet
	transforms = parse_transforms_list(transform, table.ncol)
	tarray = apply_transform(array, transform, drop=False, asarray=True)
	in_range = np.ones((table.nrow, table.ncol), dtype=np.bool)
	for col, t in enumerate(transforms):
		if t is not None:
			in_range[:,col] = t.array_in_range(array[:,col])

	# Get limits for axes
	lim = []
	for col in range(table.ncol):
		coldata = tarray[in_range[:, col], col]
		lim.append([np.min(coldata), np.max(coldata)])

	# Loop over positions in matrix
	subplots = np.ndarray((table.ncol, table.ncol), dtype=object)
	for xcol in range(table.ncol):
		for ycol in range(table.ncol):

			# Create subplot
			sp = figure.add_subplot(table.ncol, table.ncol,
				ycol * table.ncol + xcol + 1)
			subplots[xcol, ycol] = sp

			# Histogram
			if xcol == ycol:

				hist(tarray[in_range[:, xcol], xcol], ax=sp, xlab=None,
					ylab=None)
				sp.xlim = lim[xcol]

			# Density plot
			else:

				rows = np.all(in_range[:, [xcol, ycol]], axis=1)
				density2d(tarray[:, [xcol, ycol]][rows, :], ax=sp,
					labels=None)
				sp.xlim = lim[xcol]
				sp.ylim = lim[ycol]

			# X labels only on bottom
			if ycol == table.ncol - 1:
				sp.set_xlabel(format_axis_label(table.column_names[xcol],
					transforms[xcol]))
			else:
				sp.set_xticklabels([])

			# Y labels only on left
			if xcol == 0:
				sp.set_ylabel(format_axis_label(table.column_names[ycol],
					transforms[ycol]))
			else:
				sp.set_yticklabels([])

	# Y ticks for top left histogram
	if table.ncol > 1:
		mapper = ScaleMapper(lim[0], subplots[0, 0].get_ylim())
		tgt_ticks = subplots[1, 0].get_yticks()
		yticks = mapper(tgt_ticks)
		yticklab = [format(t, 'g') for t in tgt_ticks]
		subplots[0, 0].set_yticks(yticks)
		subplots[0, 0].set_yticklabels(yticklab)

	# Remove extra space between subplots
	figure.tight_layout(h_pad=0, w_pad=0)

	return figure


def transparency_cmap(color):

	color = mpl.colors.colorConverter.to_rgba(color)
	transparent = list(color)[:3] + [0]

	return mpl.colors.ListedColormap([transparent, color])


def plot_gate_img(gate, region, bins=256, ax=None, c='b'):

	if ax is None:
		ax = plt.gca()

	img = gate_img(gate, region, bins)

	cmap = transparency_cmap(c)

	ax.imshow(img, origin='lower', extent=region[0] + region[1],
		aspect='auto', cmap=cmap)


def plot_gate_edges(gate, region, bins=256, ax=None, c='b'):

	if ax is None:
		ax = plt.gca()

	edges = gate_edges(gate, region, bins)

	cmap = transparency_cmap(c)

	ax.imshow(edges, origin='lower', extent=region[0] + region[1],
		aspect='auto', cmap=cmap)


def gate_edges(gate, region, bins=256):

	img = gate_img(gate, region, bins=bins)

	edges = ndimage.sobel(img, 0) | ndimage.sobel(img, 1)

	return edges


def gate_img(gate, region, bins=256):

	x, y = np.meshgrid(np.linspace(*region[0], num=bins), np.linspace(*region[1], num=bins))

	points = np.vstack((x.flatten(), y.flatten())).transpose()

	img = gate.contains(points).reshape((bins, bins))

	return img
