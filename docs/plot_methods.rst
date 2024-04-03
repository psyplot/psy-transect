.. SPDX-FileCopyrightText: 2024 Helmholtz-Zentrum hereon GmbH
..
.. SPDX-License-Identifier: CC-BY-4.0

.. _plot_methods:

psyplot plot methods
====================

This plugin defines the following new plot methods for the
:class:`psyplot.project.ProjectPlotter` class. They can, for example, be
accessed through

.. ipython::

    In [1]: import psyplot.project as psy

    In [2]: psy.plot.vertical_transect

.. autosummary::
    :toctree: generated

    ~psyplot.project.plot.vertical_transect
    ~psyplot.project.plot.vertical_maptransect
    ~psyplot.project.plot.horizontal_maptransect
    ~psyplot.project.plot.horizontal_mapvectortransect
    ~psyplot.project.plot.horizontal_mapcombinedtransect

Please refer to the section :ref:`usage` for an intro how to use them.
