import os.path as osp
import psyplot.data as psyd
import pytest
import numpy as np
import psy_transect.utils as utils

test_dir = osp.dirname(__file__)

psyd.rcParams["plotter.maps.xgrid"] = False
psyd.rcParams["plotter.maps.ygrid"] = False


@pytest.fixture(scope="module")
def test_ds():
    with psyd.open_dataset(osp.join(test_dir, "test.nc")) as ds:
        ds["level"] = ("level", np.arange(ds.dims["level"]))
        ds = utils.mesh_to_cf_bounds(
            ds.HHL, old_dim="level1", new_dim="level", ds=ds
        )
        yield ds


@pytest.fixture
def temperature_data(test_ds):
    return test_ds.psy["temperature"].psy[0]


@pytest.fixture
def wind_data(test_ds):
    ret = test_ds.isel(time=0).psy[["u", "v"]].psy.to_array()
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
