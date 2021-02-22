"""plotters module of the psy-transect psyplot plugin
"""
from typing import Dict, TYPE_CHECKING

from matplotlib.axes import Axes
from matplotlib import widgets

from psyplot.plotter import START, Formatoption
import psy_simple.plotters as psyps
import psy_maps.plotters as psypm
import psy_transect.utils as utils
import numpy as np


if TYPE_CHECKING:
    from cartopy.crs import CRS


class TransectMethod(Formatoption):
    """Specify the method how to select the transect.

    This formatoption specifies how the transect is selected.

    Parameters
    ----------
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

    dependencies = ["transect_method"]

    name = "Transect within the raw data"

    def initialize_plot(self, value):
        if value is None:
            raise ValueError("No transect specified")
        super().initialize_plot(value)

    def update(self, value):
        data = self.data

        x = data.psy.get_coord("x")
        y = data.psy.get_coord("y")

        ds = data.psy.base.isel(**data.psy.idims)

        new_ds = utils.select_transect(
            value, ds, x, y, **self.transect_method.method_kws
        )

        # update the data - this also updates the data for the plotter
        self.data = new_ds.psy[data.name]

    def diff(self, value):
        return np.any(value != self.value)


# -----------------------------------------------------------------------------
# ------------------------------ Plotters -------------------------------------
# -----------------------------------------------------------------------------


class TransectPlot2d(psyps.SimplePlot2D):
    @property
    def raw_data(self):
        return self.data


class TransectYlim(psyps.Ylim2D):
    @property
    def raw_data(self):
        return self.data


class TransectXlim(psyps.Xlim2D):

    @property
    def raw_data(self):
        return self.data


class TransectDataGrid(psyps.DataGrid):
    @property
    def raw_data(self):
        return self.data


class VerticalTransectPlotter(psyps.Simple2DPlotter):

    selectors: Dict[Axes, widgets.LassoSelector]

    transect_method = TransectMethod("transect_method")

    transect = Transect("transect")

    # necessary reimplementations
    plot = TransectPlot2d("plot")
    ylim = TransectYlim("ylim")
    xlim = TransectXlim("xlim")
    datagrid = TransectDataGrid("datagrid")

    allowed_dims = 3

    _rcparams_string = ["plotter.transect."]

    _transect_fmt = "transect"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.selectors = {}

    def get_enhanced_attrs(self, arr, *args, **kwargs):
        return getattr(arr, "attrs", {})

    def _update_transect(self, points):
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
            ax, self._update_transect, useblit=False,
            lineprops=lineprops, **kwargs
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