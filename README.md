# pycyt
This is (will be) a very basic python package for the analysis of flow cytometry data. There are several other good packages out there that accomplish this goal, I have decided to write my own becuase they were all missing a few features I needed and I thought it would be a good learning exercise. I don't know if this will ever be full-featured enough that anyone will actually want to use it over the others, but I'm making it available.

# Alternatives
If you somehow got here looking for flow cytometry software to actually use in your own project, you almost certainly want to use one of these instead:

* [FlowCytometryTools](https://github.com/eyurtsev/FlowCytometryTools) - Python package with great set of features
* [fcm](https://pythonhosted.org/fcm/basic.html>) - Another python package that seems to support similar features
* [Bioconductor](http://master.bioconductor.org) - Package for the R language

I would recommend **FlowCytometryTools**, I have found it very useful in some other projects. It has support for gates, transformations, plotting, and includes an interactive GUI. Unfortunately I found I needed better support for additional gate types in higher dimensions, which is what led to this project. **Bioconductor** is also great if you are working in R.

# Features

### Current

* Read and parse single FCS files. Supports getting raw data as a numpy array, keyword/value metadata as a dictionary, and parses other important information (channel names and other parameters, number of events, etc) into a nicer and more accessible format. Pretty basic but not bad for my first day of work.

### Reasonable goals

* Edit existing files or create from scratch, and save to disk in proper FCS3.1 format.
* Better container for data more removed from actual source file, with higher-level functions. Support lazy loading of data so many files don't have to be in memory at once.
* Compensation matrices.
* Easy plotting with matplotlib: 1d histogram, 2d density plot, matrix plots combining these.
* Support for the standard set of common Flow Cytometry transformations.
* Support for standard set of gates: range/rectangle (N-dimensional), quadrant (generalized, N-dimensional), polygon (2D), ellipsoid (N-dimensional), composite gates.
* Gating-ML support to read and write transformations, gates, and compensation to and from XML for compatibility with many other tools.
* Plotting gates.
* Grouping FCS files/samples into a collection for high-throughput analysis. Give each file a unique ID, run analyses in parallel. Create by loading all files in a directory.
* Gate trees formed by nesting gates in a hierarchy. Ability to select a sub-population by path from root like `gate_tree.subpopulation(my_fcs, ['Live', 'Lymphocytes', 'CD3+ T Cells'])`.
* Serialization of all objects for saving to and loading from disk.

### Unreasonable goals

* Interactive environment to view plots and perhaps also create and modify gates. Ability to easily navigate between files and sub-populations, change plot type or channels. Implemented with desktop GUI package (Tk, PyQt, GTK...) or perhaps web interface.
