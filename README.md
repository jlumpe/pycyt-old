# pycyt

**pycyt** is a Python API for the analysis of high-throughput flow cytometry data.

It is currently in the early stages of development. See below for a list of current and planned features.

If you just want to see it in action, jump over to the [quick start](pycyt/examples/quickstart.ipynb) page or check out the other [examples](pycyt/examples).


### What does it do?

The purpose of the package is to allow for the integration of standard flow data analysis methods (file IO, compensation, gating, etc.) with the many powerful numerical and scientific computing tools available in Python, or to allow users to easily write their own.

To this end, **pycyt** provides a simple and flexible API to manipulate flow data and expose it as common Python data types. It is based around the [scipy stack](http://www.scipy.org/) and so should work nicely with many other tools right out the box.

**pycyt** is intended for users with at least basic Python knowledge, but to use it to its full potential familiarity with **scipy** is also recommended.


### What doesn't it do?

Currently, there is no built-in GUI. This is an API, not an application. A level of interactivity is available if used in an environment like [IPython](http://ipython.org/), which enables interactive plots, and it is built with this in mind.

Instead of being a replacement for, say, FlowJo, **pycyt** could instead be used to load a FlowJo workspace and then perform a more complicated custom analysis on populations you have already defined.

Eventually, a GUI app with file IO, plotting, and gating will be a feature. This will not come until most of the basic features are in place, though.


### Design goals

##### Simplicity

Common operations like loading a file, compensating, gating, or showing a plot require a single concise function call with few parameters needed.

An emphasis is placed on interactivity with the [IPython console](https://ipython.org/ipython-doc/3/interactive/qtconsole.html) in mind, making exploratory data analysis easy.

##### Flexibility

The package is based around the [scipy stack](http://www.scipy.org/), which is already the standard for scientific and numerical computing in Python. The goal here is to do all the flow-specific work for you and then let you perform as complex an analysis as you want using the tools you already know.

Importantly, components of the package can be as tightly or loosely coupled as you want - you should be able to gate on a generic `numpy.ndarray` or pandas `DataFrame` just as easily as the specialized flow data container object.


##### Interoperability

Support for the [Gating-ML](http://flowcyt.sourceforge.net/gating/) standard, so you can import and export your gates, transformations, and compensation matrices to and from other tools. Importing from FlowJo workspace files is also planned.

&nbsp;

Currently **pycyt**'s main focus is on ease of use and portability rather than speed, and it is written in pure Python. Since it is based off of numpy performance shouldn't be too shabby, though. Performance optimizations are made whenever possible to keep things snappy, and it currently seems to be fast enough for real-time analysis.


### Features

#### Current

* **Read FCS files** - gets raw data as a numpy array and parses other metadata into accessible native Python objects. Supports the FCS3.1 standard explicitly, seems to work fine for 3.0. Haven't tried FCS2.x files yet.
* **Flexible data container** - high-level `FlowFrame` container for flow data that may have been loaded from disk or created by other means. If linked to a file on disk, can enable lazy-loading so data is only read from file when needed and is not stored in memory otherwise.
* **Compensation** - either from explicit matrix or from spillover matrix in file.
* **Transformations** - log, asinh, hyperlog, logicle, etc. Customizable parameters and easy API for creating your own.
* **Gates** - range/rectangle (N-dimensional), quadrant (generalized, N-dimensional [WIP]), polygon (2D), ellipsoid (N-dimensional), composite/boolean gates.
* **Plotting** - easy plotting with matplotlib: 1d histogram, 2d density plot, matrix plots combining these. Can also overlay gates on plots. Note - the plotting functions are currently experimental and usage will likely change.


#### Goals

* Explicit support for FCS3.0, maybe earlier versions. Ability to save `FlowFrame`s to disk in proper FCS3.1 format.
* Gating-ML support to read and write transformations, gates, and compensation to and from XML for compatibility with many other tools.
* Grouping FCS files/samples into a collection for easy parallel analysis. 
* Gate trees formed by nesting gates in a hierarchy.
* Serialization of all objects for saving to and loading from disk.
* Import from FlowJo file.
* Eventually, an interactive environment to view plots and create and modify gates. Implemented with desktop GUI package (Tk, PyQt, GTK...) or perhaps web interface.


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
