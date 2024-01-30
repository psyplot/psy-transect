# SPDX-FileCopyrightText: 2021-2024 Helmholtz-Zentrum hereon GmbH
#
# SPDX-License-Identifier: LGPL-3.0-only

import cartopy.crs as ccrs

import psy_transect.maps as psytm


def test_base_plotting(temperature_data):
    plotter = psytm.HorizontalTransectFieldPlotter(
        temperature_data, transect=5
    )
    assert plotter.plot_data.dims == ("rlat", "rlon")


def test_vector_plotting(wind_data):
    plotter = psytm.HorizontalTransectVectorPlotter(
        wind_data, transect=5, datagrid="k-"
    )
    assert plotter.plot_data.dims == ("variable", "rlat", "rlon")
    lonmin, lonmax, latmin, latmax = plotter.ax.get_extent(ccrs.PlateCarree())

    assert abs(lonmin - -6) < 5
    assert abs(lonmax - -6) < 5
    assert abs(latmin - 23)
    assert abs(latmax - 23) < 5
