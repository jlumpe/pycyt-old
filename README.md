# pycyt

**pycyt** is a Python API for the analysis of flow cytometry data. It is intended for users with basic Python knowledge and is based around the [scipy stack](http://www.scipy.org/). The goal of the package is to allow the integration of standard flow data analysis methods (file IO, compensation, gating, etc.) with the powerful numerical and scientific computing tools available in Python, or to allow users to easily write their own.

If you just want to see it in action, jump over to the [examples](pycyt/examples/) page. Otherwise continue below for features, requirements, and installation instructions.

Note that **pycyt** is currently in the early stages of development. See below for a list of current and planned features.


### Design goals

* **Simplicity** - common operations like loading a file, compensating, gating, or showing a plot require a single concise function call with few parameters needed. An emphasis is placed on interactivity with the [IPython console](https://ipython.org/ipython-doc/3/interactive/qtconsole.html) in mind, making exploratory data analysis easy.
* **Flexibility** - the package is based around the [scipy stack](http://www.scipy.org/), which is already the standard for scientific and numerical computing in Python. The goal here is to do all the flow-specific work for you and then let you perform as complex an analysis as you want using the tools you already know. Importantly, components of the package can be as tightly or loosely coupled as you want - you should be able to gate on a generic `numpy.ndarray` or pandas `DataFrame` just as easily as the specialized flow data container object.
* **Interoperability** - Support for the [Gating-ML](http://flowcyt.sourceforge.net/gating/) standard, so you can import and export your gates, transformations, and compensation matrices to and from other tools. Importing from FlowJo workspace files is also planned.

Currently **pycyt**'s main focus is on ease of use and portability rather than speed, and it is written in pure Python. Since it is based off of numpy performance shouldn't be too shabby, though. Performance optimizations are made whenever possible to keep things snappy, and it currently seems to be fast enough for real-time analysis.


### Features

#### Current

* Low-level API to read single FCS files. Supports getting raw data as a numpy array and parses other metadata into accessible native Python objects. Supports the FCS3.1 standard explicitly, seems to work fine for 3.0. Haven't tried FCS2.x files yet.
* Ability to apply compensation when loading data, either from explicit matrix or from matrix calculated from spillover matrix in file.
* Higher-level `FlowFrame` container for flow data and metadata that may be derived from a file on disk, or created from a `numpy.ndarray` or `pandas.DataFrame`. If linked to a file on disk, can enable lazy-loading so data is only read from file when needed and is not stored in memory otherwise.
* Support for the standard set of common Flow Cytometry transformations - log, hyperlog [WIP], asinh, etc.
* Support for standard set of gates: range/rectangle (N-dimensional), quadrant (generalized, N-dimensional [WIP]), polygon (2D), ellipsoid (N-dimensional), composite/boolean gates.
* Easy plotting with matplotlib: 1d histogram, 2d density plot, matrix plots combining these. Can also overlay gates on plots. Note - the plotting functions are currently experimental and usage will likely change.


#### Goals

* Explicit support for FCS3.0 (should already work but there might be some minor caveats), maybe earlier versions.
* Ability to save `FlowFrame`s to disk in proper FCS3.1 format.
* Gating-ML support to read and write transformations, gates, and compensation to and from XML for compatibility with many other tools.
* Grouping FCS files/samples into a collection for high-throughput analysis. Give each file a unique ID, run analyses in parallel. Create by loading all files in a directory. Assign additional metadata to each sample in table-like format, such as row/column in plate.
* Gate trees formed by nesting gates in a hierarchy. Ability to select a sub-population by path from root like `gate_tree.subpopulation(my_flowframe, ['Live', 'Lymphocytes', 'CD3+ T Cells'])`.
* Serialization of all objects for saving to and loading from disk.
* Import from FlowJo file. It's a proprietary format but the workspace is actually just an XML document with fairly simple structure. Gates and transformations conform to the Gating-ML standard already.
* Eventually, an interactive environment to view plots and perhaps also create and modify gates. Ability to easily navigate between files and sub-populations, change plot type or channels. Implemented with desktop GUI package (Tk, PyQt, GTK...) or perhaps web interface.


### Alternatives

I suggest taking a look at these other great packages as well to see if they might meet your needs better:

* [FlowCytometryTools](https://github.com/eyurtsev/FlowCytometryTools) - Python package with great set of features
* [fcm](https://pythonhosted.org/fcm/basic.html>) - Another python package that seems to support similar features
* [FlowCore (Bioconductor)](https://www.bioconductor.org/packages/release/bioc/html/flowCore.html) - Package for the R language

I would recommend **FlowCytometryTools**, I have found it very useful in some other projects. It has support for gates, transformations, plotting, and includes an interactive GUI.  **Bioconductor** is also great if you are working in R.


### Requirements

**pycyt** is written for Python 2.7. Its only external requirement for use is (and should remain) the [scipy stack](http://www.scipy.org/). See the [installation page](http://www.scipy.org/install.html) for instructions. If you are on Windows, I highly recommend installing the free [Anaconda](http://continuum.io/downloads) Python distribution which takes care of all of this for you. [setuptools](https://pypi.python.org/pypi/setuptools) is also required for installation.


### Installation

Installation is accomplished through [setuptools](https://pypi.python.org/pypi/setuptools) and should be very straightforward if scipy is already present. **pycyt** is written in pure Python so no compilation is required. Simply clone the repository and run the `setup.py` script with the `install` argument. Example:

    cd <github directory>
    git clone https://github.com/jlumpe/pycyt
    cd pycyt
    python setup.py install

After this you can simply `import pycyt` in your scripts.


### License

The MIT License (MIT)

Copyright (c) 2015 Jared Lumpe

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
