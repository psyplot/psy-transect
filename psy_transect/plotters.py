# SPDX-FileCopyrightText: 2021-2024 Helmholtz-Zentrum hereon GmbH
#
# SPDX-License-Identifier: LGPL-3.0-only

"""plotters module of the psy-transect psyplot plugin
"""
from __future__ import annotations

import warnings
from functools import partial
from typing import TYPE_CHECKING, Dict, List, Optional, Union

import numpy as np
import psy_maps.plotters as psypm
import psy_simple.plotters as psyps
from matplotlib import widgets
from matplotlib.axes import Axes
from psyplot.data import CFDecoder
from psyplot.plotter import START, Formatoption, docstrings

import psy_transect.utils as utils

if TYPE_CHECKING:
    from psy_transect.maps import HorizontalTransectPlotterMixin


class TransectResolution(Formatoption):
    """Expand the transect to a minimum resolution.

    This formatoption expands the segments of the transect to fullfil a
    minimum resolution. Everything but ``False`` will expand the segments of
    the transect to fullfil the minimum resolution.

    This formatoption is of particular importance if you want to use
    the vertical transect plotter in combination with a map.

    Possible types
    --------------
    ``False``
        Do not make any changes to the provided `transect` but take it as it is
    ``True`` or ``'auto'``
        The default value estimates the resolution of the underlying spatial
        data and estimates it's minimum resolution.
        **This won't not work for unstructured data!**
    float
        Specify the spatial resolution directly
    """

    name = "Minimum resolution of the transect"

    def update(self, value):
        # does nothing because the transect is updated in
        # :meth:`Transect.update`
        pass

    @property
    def estimated_resolution(self) -> Optional[float]:
        """Estimate the resolution of the input data."""
        data = self.data

        if data.psy.decoder.is_unstructured(data):
            warnings.warn(
                "Cannot estimate the resolution of unstructured data! "
                "Please set the minimum resolution for the transect using the "
                "`transect_resolution` formatoption."
            )
            return None

        x = data.psy.get_coord("x")
        y = data.psy.get_coord("y")
        return utils.estimate_resolution(x, y)

    @staticmethod
    @docstrings.get_sections(
        base="TransectResolution.expand_path_to_resolution",
        sections=["Parameters", "Returns"],
    )
    def expand_path_to_resolution(
        path: np.ndarray, resolution: float
    ) -> np.ndarray:
        """Expand a given set of points to match the given resolution.

        Parameters
        ----------
        path: np.ndarray of shape (N, 2)
            The x-y-coordinates of the path segments
        resolution: float
            The minimum resolution that shall be used to expand the path

        Returns
        -------
        np.ndarray of shape (M, 2)
            An array with ``M>=N`` where each segment in the path is smaller.
            than the minimum resolution.
        """

        def expand_segment(p0, p1):
            N = int(np.max(np.ceil(np.abs(p1 - p0) / resolution)))
            return np.concatenate(
                [np.linspace(a, b, N)[:, None] for a, b in zip(p0, p1)], -1
            )

        return np.concatenate(
            [expand_segment(p0, p1) for p0, p1 in zip(path, path[1:])], 0
        )

    docstrings.keep_params(
        "TransectResolution.expand_path_to_resolution.parameters", "path"
    )

    @docstrings.with_indent(8)
    def expand_path(self, path: np.ndarray) -> np.ndarray:
        """Expand the path segments to match the datas resolution.

        Parameters
        ----------
        %(TransectResolution.expand_path_to_resolution.parameters.path)s

        Returns
        -------
        %(TransectResolution.expand_path_to_resolution.returns)s
        """
        if not self.value:
            return path
        elif self.value is True or self.value == "auto":
            resolution = self.estimated_resolution
            if resolution is not None:
                return self.expand_path_to_resolution(path, resolution)
        return self.expand_path_to_resolution(path, self.value)


class TransectMethod(Formatoption):
    """Specify the method how to select the transect.

    This formatoption specifies how the transect is selected.

    Possible types
    --------------
    'nearest'
        Take the nearest grid point along the transect. This will not
        interpolate and return a unique list of grid points from the raw data.
    'nearest_exact'
        Take the nearest grid point, one point from the raw data per point in
        the transect
    'inverse_distance_weighting'
        Interpolation of the value at the requested position by inverse
        distance weighting method. See
        :meth:`pyinterp.RTree.inverse_distance_weighting`
    str
        Any other method suitable for the `rbf` parameter of the
        :meth:`pyinterp.RTree.radial_basis_function` method
    """

    priority = START

    name = "Method for getting the data along the transect"

    def update(self, value):
        # do nothing as the work is done within :class:`Transect`
        if value == "nearest":
            self.method_kws = dict(method="nearest", exact=False)
        elif value == "nearest_exact":
            self.method_kws = dict(method="nearest", exact=True)
        else:
            self.method_kws = dict(method=value)


class Transect(Formatoption):
    """Transect within a 2D plot

    This formatoption takes a list of x-y tuples, the so-called transect, and
    extracts the raw data along this path.

    Possible types
    --------------
    list of x-y tuples
        The point coordinates of the transect.
    None
        Uses up to the first 100 cells
    """

    priority = START  # first phase for psyplot, data manipulation

    dependencies = ["transect_method", "transect_resolution"]

    name = "Transect within the raw data"

    data_dependent = True

    def update(self, value):
        data = self.data

        x = data.psy.get_coord("x")
        y = data.psy.get_coord("y")

        ds = data.psy.base.isel(**data.psy.idims)

        if value is None:
            value = np.vstack(
                [x.values.ravel()[:100], y.values.ravel()[:100]]
            ).T

        value = self.transect_resolution.expand_path(value)

        new_ds = utils.select_transect(
            value, ds, x, y, **self.transect_method.method_kws
        )

        # update the data - this also updates the data for the plotter
        self.data = new_ds.psy[data.name]

        cell_dim = self.transect_method.method_kws.get(
            "cell_dim", "transect_cell"
        )
        decoder = CFDecoder(
            new_ds,
            x={cell_dim},
            y={self.raw_data.psy.get_coord("z").name},
        )

        self.data.psy.decoder = decoder

        self.set_decoder(decoder)

    def diff(self, value):
        try:
            return not (
                (np.shape(value) == np.shape(self.value))
                and np.all(value == self.value)
            )
        except TypeError:
            return True


# -----------------------------------------------------------------------------
# ------------------------------ Plotters -------------------------------------
# -----------------------------------------------------------------------------


class VTransform(psypm.Transform):
    __doc__ = psypm.Transform.__doc__

    connections: List[str] = []


class AlternativeTransectXCoord(Formatoption):
    """Specify what to use for the x-axis

    Possible types
    --------------
    ``'index'``
        Will use the index of the cell along the transect
    ``'distance'``
        Will use the euclidean distance of the start of the transect
    ``'haversine'``
        Will use the haversine distance in kilometers of the start of the
        transect. This can only be used if the x- and y-coordinates have
        units in ``'degrees_east'`` and ``'degrees_north'``, or ``'radian'``
        respectively.
    ``'x'``
        Will use the x-coordinate of the initial array
    ``'y'``
        Will use the y-coordinate of the initial array
    """

    dependencies = ["transect"]

    priority = START

    name = "Select the x-coordinate"

    def update(self, value):
        cell_dim = self.data.dims[-1]
        if value == "index":
            pass  # this is the default
        elif value == "distance":
            self.decoder.x = {cell_dim + "_distance"}
        elif value == "haversine":
            self.decoder.x = {cell_dim + "_haversine"}
        elif value == "x":
            x = self.raw_data.psy.get_coord("x", base=True)
            self.decoder.x = {x.name}
        elif value == "y":
            y = self.raw_data.psy.get_coord("y", base=True)
            self.decoder.x = {y.name}
        else:
            raise ValueError("Could not interprete %s" % (value,))


class VerticalTransectTranspose(psyps.Transpose):
    """Subclassed transpose to make sure we use the `coord` formatoption."""

    __doc__ = psyps.Transpose

    def get_x(self, arr):
        if self.value:
            return self.decoder.get_y(arr)
        else:
            return self.decoder.get_x(arr)

    def get_y(self, arr):
        if self.value:
            return self.decoder.get_x(arr)
        else:
            return self.decoder.get_y(arr)


class VerticalTransectPlotter(psyps.Simple2DPlotter):
    transpose = VerticalTransectTranspose("transpose")

    selectors: Dict[Axes, widgets.LassoSelector]

    transect_resolution = TransectResolution("transect_resolution")

    transect_method = TransectMethod("transect_method")

    transect = Transect("transect")

    coord = AlternativeTransectXCoord("coord")

    allowed_dims = 3

    _rcparams_string = ["plotter.transect."]

    _transect_fmt = "transect"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.selectors: Dict[Axes, widgets.LassoSelector] = {}  # type: ignore[annotation-checked]
        self._connected_horizontal_transect_plotters: Dict[  # type: ignore[annotation-checked]
            Axes, HorizontalTransectPlotterMixin
        ] = {}

    def get_enhanced_attrs(self, arr, *args, **kwargs):
        return getattr(arr, "attrs", {})

    def _update_transect(self, ax, points):
        """Update the transect for the given value."""
        self.update(**{self._transect_fmt: points, "ylim": self.ylim.value})
        selector = self.selectors.get(ax)
        if selector:
            for artist in selector.artists:
                if artist not in ax.artists:
                    ax.add_artist(artist)

    def connect_ax(
        self,
        plotter_or_ax: Union[HorizontalTransectPlotterMixin, Axes],
        **kwargs,
    ):
        """Connect to a matplotlib axes via lasso.

        This creates a lasso to be used

        Parameters
        ----------
        plotter_or_ax: VerticalTransectPlotter or matplotlib.axes.Axes
            The plotter whose axes to draw on, or an matplotlib axes. If you
            pass in the plotter, we make sure that lasso selectors of the
            plotter still work after an update.
        """
        from psy_transect.maps import HorizontalTransectPlotterMixin

        ax: Axes
        plotter: Optional[HorizontalTransectPlotterMixin]

        if isinstance(plotter_or_ax, HorizontalTransectPlotterMixin):
            ax = plotter_or_ax.ax  # type: ignore
            plotter = plotter_or_ax
        else:
            ax = plotter_or_ax
            plotter = None
        selector = widgets.LassoSelector(
            ax,
            partial(self._update_transect, ax),
            useblit=False,
            **kwargs,
        )
        self.selectors[ax] = selector
        if plotter is not None:
            self._connected_horizontal_transect_plotters[ax] = plotter
        return selector

    def disconnect_ax(self, ax: Axes):
        """Disconnect this plotter from an axes and remove the selector."""
        if ax in self.selectors:
            selector = self.selectors.pop(ax)
            selector.disconnect_events()
            try:
                selector.line.remove()
            except (AttributeError, KeyError):
                pass
        self._connected_horizontal_transect_plotters.pop(ax, None)


class VerticalMapTransectPlotter(VerticalTransectPlotter):
    transform = VTransform("transform")

    _rcparams_string = ["plotter.vmaptransect."]

    def _update_transect(self, ax, points):
        points = np.asarray(points)
        transformed = self.transform.projection.transform_points(
            ax.projection, points[:, 0], points[:, 1]
        )
        super()._update_transect(ax, transformed[:, :2])
