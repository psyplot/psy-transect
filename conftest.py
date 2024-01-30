# SPDX-FileCopyrightText: 2021-2024 Helmholtz-Zentrum hereon GmbH
#
# SPDX-License-Identifier: LGPL-3.0-only

import os.path as osp
from pathlib import Path
from typing import Callable

import numpy as np
import psyplot.data as psyd
import pytest

import psy_transect.utils as utils

test_dir = osp.dirname(__file__)

psyd.rcParams["plotter.maps.xgrid"] = False
psyd.rcParams["plotter.maps.ygrid"] = False


@pytest.fixture(scope="module")
def get_test_file() -> Callable[[str], Path]:
    """Fixture to get the path to a test file."""

    def get_file(basename: str) -> Path:
        """Get a file in the test folder

        Parameters
        ----------
        basename : str
            The basename of the file, relative to the tests folder

        Returns
        -------
        Path
            The path to the file relative to the working directory
        """
        test_folder = Path(__file__).parent / "tests"
        return test_folder / basename

    return get_file


@pytest.fixture
def test_ds(get_test_file: Callable[[str], Path]):
    with psyd.open_dataset(get_test_file("test.nc")) as ds:
        ds["level"] = ("level", np.arange(ds.dims["level"]))
        ds = utils.mesh_to_cf_bounds(
            ds.psy.HHL, old_dim="level1", new_dim="level", ds=ds
        )
        yield ds


@pytest.fixture
def temperature_data(test_ds):
    return test_ds.psy["temperature"].psy[0]


@pytest.fixture
def wind_data(test_ds):
    new_ds = test_ds.isel(time=0).psy[["u", "v"]]
    new_ds["HHL_bnds"] = test_ds["HHL_bnds"]
    new_ds = new_ds.set_coords("HHL_bnds")
    ret = new_ds.psy.to_array()
    ret.encoding["coordinates"] = test_ds["u"].encoding["coordinates"]
    return ret


@pytest.fixture
def transect_points(test_ds):
    lonmin, lonmax = test_ds.lon.min(), test_ds.lon.max()
    latmin, latmax = test_ds.lat.min(), test_ds.lat.max()
    points = np.c_[
        np.linspace(lonmin, lonmax)[:, None],
        np.linspace(latmin, latmax)[:, None],
    ]
    return points
