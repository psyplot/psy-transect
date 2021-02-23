"""plotters module of the psy-transect psyplot plugin
"""
from typing import Dict, TYPE_CHECKING, Optional
from functools import partial
import warnings

from matplotlib.axes import Axes
from matplotlib import widgets

import xarray as xr

from psyplot.plotter import START, Formatoption, docstrings
from psyplot.data import CFDecoder
import psy_simple.plotters as psyps
import psy_maps.plotters as psypm
import psy_transect.utils as utils
import numpy as np


if TYPE_CHECKING:
    from cartopy.crs import CRS


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
        else:
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
    """

    priority = START  # first phase for psyplot, data manipulation

    dependencies = ["transect_method", "transect_resolution"]

    name = "Transect within the raw data"

    data_dependent = True

    def initialize_plot(self, value):
        if value is None:
            raise ValueError("No transect specified")
        super().initialize_plot(value)

    def update(self, value):
        data = self.data

        x = data.psy.get_coord("x")
        y = data.psy.get_coord("y")

        ds = data.psy.base.isel(**data.psy.idims)

        value = self.transect_resolution.expand_path(value)

        new_ds = utils.select_transect(
            value, ds, x, y, **self.transect_method.method_kws
        )

        # update the data - this also updates the data for the plotter
        self.data = new_ds.psy[data.name]

        decoder = CFDecoder(
            new_ds,
            x={self.data.dims[-1]},
            y={self.raw_data.psy.get_coord("z").name},
        )

        self.data.psy.decoder = decoder

        self.set_decoder(decoder)

    def diff(self, value):
        return np.any(value != self.value)


# -----------------------------------------------------------------------------
# ------------------------------ Plotters -------------------------------------
# -----------------------------------------------------------------------------


class VTransform(psypm.Transform):

    connections = []


class AlternativeTransectXCoord(Formatoption):
    """Specify what to use for the x-axis

    Possible types
    --------------
    ``'index'``
        Will use the index of the cell along the transect
    ``'distance'``
        Will use the euclidean distance of the start of the transect
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
        elif value == "x":
            x = self.raw_data.psy.get_coord("x", base=True)
            self.decoder.x = {x.name}
        elif value == "y":
            y = self.raw_data.psy.get_coord("y", base=True)
            self.decoder.x = {y.name}
        else:
            raise ValueError("Could not interprete %s" % (value,))


class VerticalTransectPlotter(psyps.Simple2DPlotter):

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
        self.selectors = {}

    def get_enhanced_attrs(self, arr, *args, **kwargs):
        return getattr(arr, "attrs", {})

    def _update_transect(self, ax, points):
        """Update the transect for the given value."""
        self.update(**{self._transect_fmt: points})

    def connect_ax(self, ax: Axes, lineprops={"color": "red"}, **kwargs):
        """Connect to a matplotlib axes via lasso.

        This creates a lasso to be used

        Parameters
        ----------
        ax : Axes
            The matplotlib axes to connect to
        """
        selector = widgets.LassoSelector(
            ax,
            partial(self._update_transect, ax),
            useblit=False,
            lineprops=lineprops,
            **kwargs
        )
        self.selectors[ax] = selector
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


class VerticalMapTransectPlotter(VerticalTransectPlotter):

    transform = VTransform("transform")

    _rcparams_string = ["plotter.vmaptransect."]

    def _update_transect(self, ax, points):
        points = np.asarray(points)
        transformed = self.transform.projection.transform_points(
            ax.projection, points[:, 0], points[:, 1]
        )
        super()._update_transect(ax, transformed[:, :2])
