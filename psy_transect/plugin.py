# SPDX-FileCopyrightText: 2021-2024 Helmholtz-Zentrum hereon GmbH
#
# SPDX-License-Identifier: LGPL-3.0-only

"""psy-transect psyplot plugin

This module defines the rcParams for the psy-transect plugin. This module will
be imported when psyplot is imported. What is should contain is:

- an rcParams variable as instance of :class:`psyplot.config.rcsetup.RcParams`
  that describes the configuration of your plugin
- a get_versions function that returns the version of your plugin and the ones
  from its requirements

.. warning::

    Because of recursion issues, You have to load the psyplot module before
    loading this module! In other words, you have to type

    .. code-block:: python

        import psyplot
        import psy_transect.plugin
"""
import numpy as np
from psy_maps.plugin import rcParams as maps_rcParams
from psy_simple.plugin import (
    ValidateInStrings,
    try_and_error,
    validate_bool,
    validate_float,
    validate_none,
    validate_str,
)
from psyplot.config.rcsetup import RcParams
from psyplot.data import isstring

from psy_transect import __version__ as plugin_version


def get_versions(requirements=True):
    """Get the versions of psy-transect and it's requirements

    Parameters
    ----------
    requirements: bool
        If True, the requirements are imported and it's versions are included
    """
    ret = {"version": plugin_version}
    if requirements:
        # insert versions of the requirements, e.g. via
        #   >>> import requirement
        #   >>> ret['requirement'] = requirement.__version__
        pass
    return ret


# -----------------------------------------------------------------------------
# ------------------------- validation functions ------------------------------
# -----------------------------------------------------------------------------


# define your validation functions for the values in the rcParams here. If
# a validation fails, the function should raise a ValueError or TypeError


def validate_points(points):
    if points is None or isstring(points):
        return points
    arr = np.asarray(points, float)
    if arr.ndim != 2 or arr.shape[-1] != 2:
        raise ValueError("Transect requires points as shape (N, 2)")
    return arr


# -----------------------------------------------------------------------------
# ------------------------------ rcParams -------------------------------------
# -----------------------------------------------------------------------------


# define your defaultParams. A mapping from rcParams key to a list of length 3:
#
# 1. the default value
# 2. the validation function of type conversion function
# 3. a short description of the default value
#
# Example::
#
#     defaultParams = {'my.key': [True, bool, 'What my key does']}
defaultParams = {
    # key for defining new plotters
    "project.plotters": [
        {
            "vertical_transect": {
                "module": "psy_transect.plotters",
                "plotter_name": "VerticalTransectPlotter",
                "plot_func": True,
                "prefer_list": False,
                "default_slice": 0,
                "default_dims": {
                    "z": slice(None),
                    "x": slice(None),
                    "y": slice(None),
                },
            },
            "vertical_maptransect": {
                "module": "psy_transect.plotters",
                "plotter_name": "VerticalMapTransectPlotter",
                "plot_func": True,
                "prefer_list": False,
                "default_slice": 0,
                "default_dims": {
                    "z": slice(None),
                    "x": slice(None),
                    "y": slice(None),
                },
            },
            "horizontal_maptransect": {
                "module": "psy_transect.maps",
                "plotter_name": "HorizontalTransectFieldPlotter",
                "plot_func": True,
                "prefer_list": False,
                "default_slice": 0,
                "default_dims": {
                    "z": slice(None),
                    "x": slice(None),
                    "y": slice(None),
                },
            },
            "horizontal_mapvectortransect": {
                "module": "psy_transect.maps",
                "plotter_name": "HorizontalTransectVectorPlotter",
                "plot_func": True,
                "prefer_list": False,
                "default_slice": 0,
                "default_dims": {
                    "z": slice(None),
                    "x": slice(None),
                    "y": slice(None),
                },
            },
            "horizontal_mapcombinedtransect": {
                "module": "psy_transect.maps",
                "plotter_name": "HorizontalTransectCombinedPlotter",
                "plot_func": True,
                "prefer_list": True,
                "default_slice": 0,
                "default_dims": {
                    "z": slice(None),
                    "x": slice(None),
                    "y": slice(None),
                },
            },
        },
        dict,
        "The plot methods in the psy-transect package",
    ],
    "plotter.transect.transect_method": [
        "nearest",
        validate_str,
        "The method how to extract the transect from the data",
    ],
    "plotter.transect.transect_resolution": [
        "auto",
        try_and_error(
            validate_bool,
            ValidateInStrings("transect_resolution", ["auto"], False),
            validate_float,
        ),
        "Minimal resolution of the data used to expand the transect.",
    ],
    "plotter.transect.transect": [
        None,
        validate_points,
        "The point coordinates of the transect",
    ],
    "plotter.transect.coord": [
        "index",
        ValidateInStrings(
            "coord", ["index", "distance", "haversine", "x", "y"], True
        ),
        "What to display on the x-axis",
    ],
    "plotter.vmaptransect.transform": maps_rcParams.defaultParams[
        "plotter.maps.transform"
    ],
    "plotter.maptransect.transect": [
        None,
        try_and_error(validate_none, validate_float),
        "The vertical levels to select",
    ],
    "plotter.maptransect.combined.vtransect": [
        None,
        try_and_error(validate_none, validate_float),
        "The vertical levels to select",
    ],
}

# create the rcParams and populate them with the defaultParams. For more
# information on this class, see the :class:`psyplot.config.rcsetup.RcParams`
# class
rcParams = RcParams(defaultParams=defaultParams)
rcParams.update_from_defaultParams()
