import numpy as np
from scipy import ndimage
import matplotlib as mpl
from matplotlib import pyplot as plt


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


def plot_density2d(x, y, bins=128, ax=None):

	if ax is None:
		ax = plt.gca()

	hist, xedges, yedges = np.histogram2d(x, y, bins=bins)

	extent = [xedges[0], xedges[-1], yedges[0], yedges[-1]]

	img = ax.imshow(hist.transpose(), origin='lower', extent=extent, interpolation='none',
		aspect='auto')

	return img


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
