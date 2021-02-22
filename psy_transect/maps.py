"""Horizontal transects for maps."""
from typing import Dict

from matplotlib.axes import Axes
from matplotlib import widgets

import numpy as np
import psy_maps.plotters as psypm
import psy_simple.plotters as psyps
from psyplot.plotter import START, Formatoption
from itertools import chain

import psy_transect.utils as utils


class HorizontalTransect(Formatoption):
    """Transect along a vertical level

    This formatoption takes a list of x-y tuples, the so-called transect, and
    extracts the raw data along this path.

    Possible types
    --------------
    list of x-y tuples
        The point coordinates of the transect.
    """

    priority = START  # first phase for psyplot, data manipulation

    name = "Transect within the raw data"

    def initialize_plot(self, value):
        if value is None:
            raise ValueError("No transect specified")
        super().initialize_plot(value)

    def update(self, value):
        data = self.data

        z = data.psy.get_coord("z")

        ds = data.psy.base.isel(**data.psy.idims)

        new_ds = utils.select_level(value, ds, z, data.psy.get_dim("z"))

        self.update_data_from_ds(new_ds)

    def update_data_from_ds(self, ds):
        # update the data - this also updates the data for the plotter
        self.data = ds.psy[self.data.name]


class HorizontalTransectVector(HorizontalTransect):
    def update_data_from_ds(self, ds):
        variables = list(self.plotter.base_variables)[-2:]
        all_dims = set(chain.from_iterable(ds[v].dims for v in variables))
        for cname, coord in ds.coords.items():
            if set(coord.dims) <= all_dims:
                variables.append(cname)
        new = ds.psy[variables].psy.to_array()
        if "coordinates" in self.data.encoding:
            new.encoding["coordinates"] = self.data.encoding["coordinates"]
        self.data = new


class MapTransectDataGrid(psypm.MapDataGrid):
    @property
    def raw_data(self):
        return self.data


class MapTransectMapPlot2D(psypm.MapPlot2D):
    @property
    def raw_data(self):
        return self.data


class HorizontalTransectPlotterMixin:

    transect: HorizontalTransect

    sliders: Dict[Axes, widgets.Slider]

    _transect_fmt = "transect"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sliders = {}

    def _update_transect(self, val):
        """Update the transect for the given value."""
        self.update(**{self._transect_fmt: val})
        for slider in self.sliders.values():
            if slider.val != val:
                slider.set_val(val)
            slider.label.set_position((0.5, slider.val))
            slider.valtext.set_position((0.5, slider.val))

    def connect_ax(
        self, ax: Axes, orientation: str = "vertical",
        facecolor="none", edgecolor="red", dragging=False,
        label="Vertical transect", **kwargs,
    ) -> widgets.Slider:
        """Connect this plotter to an axes and draw a slider on it.

        When the slider changes, the plot here is updated.

        Parameters
        ----------
        ax: matplotlib.axes.Axes
            The matplotlib axes to draw the slider on.
        orientation: str
            The orientation of the slider (which is vertical by default).
        ``*args, **kwargs``
            Any further arguments or keyword arguments that are parsed to the
            created :class:`~matplotlib.widgets.Slider`

        Returns
        -------
        matplotlib.widgets.Slider
            The newly created slider
        """
        fig = ax.figure

        # we draw an axes above the selected axes and use it for the slider
        if orientation == "vertical":
            slider_ax = fig.add_axes(
                ax.get_position(), label="slider-ax", sharey=ax,
                facecolor="none",
            )
        else:
            slider_ax = fig.add_axes(
                ax.get_position(), label="slider-ax", sharex=ax,
                facecolor="none",
            )

        transect_val = self[self._transect_fmt]  # type: ignore
        if transect_val is not None:
            kwargs["valinit"] = transect_val
        vmin, vmax = (
            ax.get_ylim() if orientation == "vertical" else ax.get_xlim()
        )
        kwargs.setdefault("valmin", vmin)
        kwargs.setdefault("valmax", vmax)

        slider = widgets.Slider(
            slider_ax, orientation=orientation,
            facecolor=facecolor, edgecolor=edgecolor, dragging=dragging,
            label=label, **kwargs
        )

        # update text properties to show the label above the line
        # and the value below
        slider.label.set_transform(slider_ax.transData)
        slider.label.set_position((0.5, slider.val))
        slider.label.set_verticalalignment("bottom")

        slider.valtext.set_transform(slider_ax.transData)
        slider.valtext.set_position((0.5, slider.val))
        slider.valtext.set_verticalalignment("top")

        slider.on_changed(self._update_transect)
        self.sliders[ax] = slider
        return slider

    def disconnect_ax(self, ax: Axes):
        """Disconnect this plotter from an axes and remove the slider."""
        if ax in self.sliders:
            slider = self.sliders.pop(ax)
            fig = slider.ax.figure
            fig.delaxes(slider.ax)

    def get_enhanced_attrs(self, *args, **kwargs):
        ret = super().get_enhanced_attrs(*args, **kwargs)
        ret[self._transect_fmt] = self[self._transect_fmt]
        return ret


class HorizontalTransectFieldPlotter(
    HorizontalTransectPlotterMixin, psypm.FieldPlotter
):

    _rcparams_string = ["plotter.maptransect."]

    allowed_dims = 3

    transect = HorizontalTransect("transect")
    plot = MapTransectMapPlot2D("plot")
    datagrid = MapTransectDataGrid("datagrid")


class HorizontalTransectVectorPlotter(
    HorizontalTransectPlotterMixin, psypm.VectorPlotter
):

    _rcparams_string = ["plotter.maptransect.", "plotter.maptransect.vector"]

    allowed_dims = 4

    transect = HorizontalTransectVector("transect")
    datagrid = MapTransectDataGrid("datagrid")


class HorizontalTransectCombinedPlotter(
    HorizontalTransectPlotterMixin, psypm.CombinedPlotter
):

    _rcparams_string = [
        "plotter.maptransect.",
        "plotter.maptransect.vector.",
        "plotter.maptransect.combined.",
    ]

    vtransect = HorizontalTransectVector("vtransect", index_in_list=1)
    plot = MapTransectMapPlot2D("plot", index_in_list=0)
    datagrid = MapTransectDataGrid("datagrid")

    _transect_fmt = "vtransect"
