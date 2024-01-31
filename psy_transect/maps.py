# SPDX-FileCopyrightText: 2021-2024 Helmholtz-Zentrum hereon GmbH
#
# SPDX-License-Identifier: LGPL-3.0-only

"""Horizontal transects for maps."""

from __future__ import annotations

from functools import partial
from itertools import chain
from typing import Dict, Union

import psy_maps.plotters as psypm
from matplotlib import widgets
from matplotlib.axes import Axes
from psyplot.plotter import START, Formatoption

import psy_transect.utils as utils
from psy_transect.plotters import VerticalTransectPlotter


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

    def update(self, value):
        data = self.data

        z = data.psy.get_coord("z")

        if value is None:
            value = z.min().values

        ds = data.psy.base.isel(**data.psy.idims)

        new_ds = utils.select_level(value, ds, z, data.psy.get_dim("z"))

        self.update_data_from_ds(new_ds)

    def update_data_from_ds(self, ds):
        # update the data - this also updates the data for the plotter
        self.data = ds.psy[self.data.name]


class HorizontalTransectLonLatBox(psypm.LonLatBox):
    dependencies = psypm.LonLatBox.dependencies + ["transect"]


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
        self.sliders: Dict[Axes, widgets.Slider] = {}  # type: ignore[annotation-checked]
        self._connected_vertical_transect_plotters: Dict[  # type: ignore[annotation-checked]
            Axes, VerticalTransectPlotter
        ] = {}

    def _update_transect(self, ax, val):
        """Update the transect for the given value."""
        self.update(**{self._transect_fmt: val})
        for slider in self.sliders.values():
            if slider.val != val:
                slider.set_val(val)
            slider.label.set_position((0.5, slider.val))
            slider.valtext.set_position((0.5, slider.val))
        for plotter in self._connected_vertical_transect_plotters.values():
            selector = plotter.selectors.get(self.ax)
            if selector:
                for artist in selector.artists:
                    if artist not in self.ax.artists:
                        self.ax.add_artist(artist)

    def connect_ax(
        self,
        plotter_or_ax: Union[VerticalTransectPlotter, Axes],
        orientation: str = "vertical",
        facecolor="none",
        edgecolor="red",
        track_color="none",
        initcolor="red",
        dragging=False,
        label="Vertical transect",
        **kwargs,
    ) -> widgets.Slider:
        """Connect this plotter to an axes and draw a slider on it.

        When the slider changes, the plot here is updated.

        Parameters
        ----------
        plotter_or_ax: VerticalTransectPlotter or matplotlib.axes.Axes
            The plotter whose axes to draw on, or an matplotlib axes. If you
            pass in the plotter, we make sure that lasso selectors of the
            plotter still work after an update.
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
        if isinstance(plotter_or_ax, VerticalTransectPlotter):
            ax = plotter_or_ax.ax
            plotter = plotter_or_ax
        else:
            ax = plotter_or_ax
            plotter = None
        fig = ax.figure

        # we draw an axes above the selected axes and use it for the slider
        if orientation == "vertical":
            slider_ax = fig.add_axes(
                ax.get_position(),
                label="slider-ax",
                sharey=ax,
                facecolor="none",
            )
        else:
            slider_ax = fig.add_axes(
                ax.get_position(),
                label="slider-ax",
                sharex=ax,
                facecolor="none",
            )

        transect_val = self[self._transect_fmt]  # type: ignore
        if transect_val is not None:
            kwargs["valinit"] = transect_val
        z = self.data.psy.get_coord("z")  # type: ignore
        vmin = z.min().values
        vmax = z.max().values

        kwargs.setdefault("valmin", vmin)
        kwargs.setdefault("valmax", vmax)

        slider = widgets.Slider(
            slider_ax,
            orientation=orientation,
            facecolor=facecolor,
            edgecolor=edgecolor,
            track_color=track_color,
            initcolor=initcolor,
            dragging=dragging,
            label=label,
            **kwargs,
        )

        # update text properties to show the label above the line
        # and the value below
        slider.label.set_transform(slider_ax.transData)
        slider.label.set_position((0.5, slider.val))
        slider.label.set_verticalalignment("bottom")

        slider.valtext.set_transform(slider_ax.transData)
        slider.valtext.set_position((0.5, slider.val))
        slider.valtext.set_verticalalignment("top")

        slider.on_changed(
            partial(self._update_transect, ax),
        )
        self.sliders[ax] = slider
        if plotter is not None:
            self._connected_vertical_transect_plotters[ax] = plotter
        return slider

    def disconnect_ax(self, ax: Axes):
        """Disconnect this plotter from an axes and remove the slider."""
        if ax in self.sliders:
            slider = self.sliders.pop(ax)
            fig = slider.ax.figure
            fig.delaxes(slider.ax)
        self._connected_vertical_transect_plotters.pop(ax, None)

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

    lonlatbox = HorizontalTransectLonLatBox("lonlatbox")


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
