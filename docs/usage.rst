.. SPDX-FileCopyrightText: 2024 Helmholtz-Zentrum hereon GmbH
..
.. SPDX-License-Identifier: CC-BY-4.0


.. _usage:

Usage
=====
Once installed, the :ref:`plotmethods <plot_methods>` are available via the
standard `psyplot.project.plot` project plotter.

.. warning::

    We are working on a better user documentation of psy-transect. But this
    should hopefully give you an initial idea about the possibilities.

    The example that is presented here is taken from

        Sommer, P. S. Using psyplot for visualizing unstructured data and 
        vertical transects [Computer software]. 
        https://github.com/Chilipp/psyplot-KS-Seminar-20240201
    

Standard COSMO-CLM grid
-----------------------

We can use the :attr:`~psyplot.project.plot.horizontal_maptransect` plotter for
visualizing a horizontal map transect. In this example, we use a model output
of the COSMO-CLM model and display horizontal and vertical map transects.

The file ``T.nc`` is :download:`here available for download <data/T.nc>`.

.. ipython::

    In [1]: import psyplot.project as psy

    In [1]: temperature_ds = psy.open_dataset("data/T.nc")
       ...: temperature_ds

    @savefig docs_horizontal_maptransect_cosmo.png width=4in
    In [2]: temperature_ds.psy.plot.horizontal_maptransect(
       ...:     name="T",
       ...:     transect=0,
       ...:     cmap="Reds",
       ...:     title="Layer at height %(transect)1.2f",
       ...: )

We can combine this with a vertical map transect along a given path:

.. ipython::

    @savefig docs_vertical_maptransect_cosmo.png width=4in
    In [3]: temperature_ds.psy.plot.vertical_maptransect(
       ...:     name="T",
       ...:     plot="poly",
       ...:     background="0.5",
       ...:     transform="cyl",
       ...:     xlim="minmax",
       ...: )


Vertical level information
--------------------------
The vertical level information in such a climate model is usually given in
bar. This information is not very helpful for most of the people, therefore
``psy-transect`` implements a methodology, to merge the vertical information
into the data and generate a CF-conform representation of the orography. For
COSMO-CLM, this information is stored in the file with the rather cryptic name
:download:`lffd1980010100c.nc <data/lffd1980010100c.nc>`.

.. ipython::

    In [5]: from psy_transect import utils

    In [5]: orography = psy.open_dataset("data/lffd1980010100c.nc").psy.HHL.psy[0]

    In [6]: new_ds = utils.mesh_to_cf_bounds(
       ...:     orography, "level1", "level", temperature_ds
       ...: )

    @savefig docs_horizontal_maptransect_cosmo_oro.png width=4in
    In [7]: new_ds.psy.plot.horizontal_maptransect(
       ...:     name="T",
       ...:     transect=0,
       ...:     cmap="Reds",
       ...:     title="Layer at height %(transect)1.2f m",
       ...: )

    @savefig docs_vertical_maptransect_cosmo_oro.png width=4in
    In [8]: new_ds.psy.plot.vertical_maptransect(
       ...:     name="T",
       ...:     plot="poly",
       ...:     background="0.5",
       ...:     datagrid="k-",
       ...:     transform="cyl",
       ...:     xlim="minmax",
       ...:     ylim=(0, 6000),
       ...:     yticks=np.linspace(0, 6000, 7),
       ...: )

As you can see in this plot, we are able to visualize the exact orography of the
model, without the need of any interpolation.


Interactive exploratory data analysis
-------------------------------------
One important aspect for transects is the interactive usage. We want to be able
to connect multiple plots and visualize the vertical transect along a line that
we draw. ``psy-transect`` has implemented some widgets (that we cannot
demonstrate in this static documentation). You can activate it via

.. code-block:: python

    p1, p2 = psy.gcp(True).plotters
    p1.connect_ax(p2)
    p2.connect_ax(p1)
