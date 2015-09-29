# pycyt
This is (will be) a python package for the analysis of flow cytometry data. There are several other good packages out there that accomplish this goal, but I have started this project because I found they did not fit my workflow completely. The project is in its very early stages but I believe it will come to have a competitive set of features.

### Design goals

* **Simplicity** - common operations like loading a file, applying the file-defined compensation, filtering by a predefined gate, and plotting *SSC-A* vs *FSC-A* with a log scale on the Y-axis shouldn't take more than one line each (with few parameters to enter).
* **Interactivity** - I work with flow data every day, but it is rarely a predefined workflow. More often I want to be able to explore and visualize the data interactively. Most of my time is spent in the IPython console where I can have total control to experiment, so the less lines of code I need to type the better. I want high-level functions with simple syntax to easily accomplish common tasks, with a focus on visualization.
* **Flexibility** - the package will be based around the [scipy stack](http://www.scipy.org/), which is already the standard for scientific and numerical computing in Python. The goal here is to do all the flow-specific work for you and then let you perform as complex an analysis as you want using the tools you already know. Importantly, components of the package can be as tightly or loosely coupled as you want - you should be able to apply a polygon gate to a generic `numpy.ndarray` or pandas `DataFrame` as well as the specialized flow data container object.
* **Interoperability** - Support for the [Gating-ML](http://flowcyt.sourceforge.net/gating/) standard, so you can import and export your gates, transformations, and compensation matrices to and from other tools. Like doing your gating in FlowJo? You'll be able to parse your FlowJo workspace, grab the entire population tree, load the sample data, then plot stacked histograms of CD4+ T Cells/CD8+ T Cells/B Cells/NK Cells in an 8x12 table of subplots for all wells in your 96-well plate.

Currently this package is focused on ease-of-use rather than speed, but since it is based off of numpy performance shouldn't be too shabby. It will include specific optimizations such as lazy-loading of FCS files when needed so you don't need to have your whole data set in memory at once.

### Features

#### Current

* Low-level API to read and parse single FCS files. Supports getting raw data as a numpy array, keyword/value metadata as a dictionary, and parses other important information (parameter names and other attributes, number of events, spillover matrix, etc) from strings into more accessible objects. Supports the FCS3.1 standard explicitly, seems to work fine for 3.0. Haven't tried FCS2.? files yet.
* Ability to apply compensation when loading data, either from explicit matrix or from matrix calculated from spillover matrix in file.
* Higher-level `FlowFrame` container for flow data and metadata that may be derived from a file on disk, or created from a `numpy.ndarray` or `pandas.DataFrame`. If linked to a file on disk, can enable lazy-loading so data is only read from file when needed and is not stored in memory otherwise.

#### Reasonable goals

* Explicit support for FCS3.0 (should already work but there might be some minor caveats), maybe eariler versions.
* Ability to save `FlowFrame`s to disk in proper FCS3.1 format.
* Easy plotting with matplotlib: 1d histogram, 2d density plot, matrix plots combining these.
* Support for the standard set of common Flow Cytometry transformations - log, hyperlog, asinh, etc.
* Support for standard set of gates: range/rectangle (N-dimensional), quadrant (generalized, N-dimensional), polygon (2D), ellipsoid (N-dimensional), composite/boolean gates.
* Gating-ML support to read and write transformations, gates, and compensation to and from XML for compatibility with many other tools.
* Plotting gates.
* Grouping FCS files/samples into a collection for high-throughput analysis. Give each file a unique ID, run analyses in parallel. Create by loading all files in a directory. Assign additional metadata to each sample in table-like format, such as row/column in plate.
* Gate trees formed by nesting gates in a hierarchy. Ability to select a sub-population by path from root like `gate_tree.subpopulation(my_flowframe, ['Live', 'Lymphocytes', 'CD3+ T Cells'])`.
* Serialization of all objects for saving to and loading from disk.
* Import from FlowJo file. It's a proprietary format but the workspace is actually just an XML document with fairly simple structure. Gates and transformations conform to the Gating-ML standard already.

#### Unreasonable goals

* Interactive environment to view plots and perhaps also create and modify gates. Ability to easily navigate between files and sub-populations, change plot type or channels. Implemented with desktop GUI package (Tk, PyQt, GTK...) or perhaps web interface.

### Alternatives
This project is quite immature at the moment so if you need something now you'll probably want to use one of these instead:

* [FlowCytometryTools](https://github.com/eyurtsev/FlowCytometryTools) - Python package with great set of features
* [fcm](https://pythonhosted.org/fcm/basic.html>) - Another python package that seems to support similar features
* [Bioconductor](http://master.bioconductor.org) - Package for the R language

I would recommend **FlowCytometryTools**, I have found it very useful in some other projects. It has support for gates, transformations, plotting, and includes an interactive GUI.  **Bioconductor** is also great if you are working in R.
