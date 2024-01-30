# SPDX-FileCopyrightText: 2021-2024 Helmholtz-Zentrum hereon GmbH
#
# SPDX-License-Identifier: LGPL-3.0-only

"""Test module for psy_transect.plotters"""
import psy_transect.plotters as psyt


def test_base_plotting(temperature_data, transect_points):
    plotter = psyt.VerticalTransectPlotter(
        temperature_data,
        transect=transect_points,
        plot="poly",
        datagrid="k-",
        xlim="minmax",
        ylim="minmax",
    )

    ymin = temperature_data.psy.base.HHL_bnds.values.min()
    ymax = temperature_data.psy.base.HHL_bnds.values.max()
    xmin = -0.5
    xmax = 4.5
    assert (ymin, ymax) == plotter.ax.get_ylim()
    assert (xmin, xmax) == plotter.ax.get_xlim()
