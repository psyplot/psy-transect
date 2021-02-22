"""Utility functions for psy-transect"""
from typing import Union, Dict, Optional, List, Any
from itertools import chain, filterfalse

import xarray as xr
import numpy as np
from sklearn.neighbors import BallTree


def unique_everseen(iterable, key=None):
    """List unique elements, preserving order. Remember all elements ever seen.

    Function taken from https://docs.python.org/2/library/itertools.html"""
    # unique_everseen('AAAABBBCCDAABBB') --> A B C D
    # unique_everseen('ABBCcAD', str.lower) --> A B C D
    seen = set()
    seen_add = seen.add
    if key is None:
        for element in filterfalse(seen.__contains__, iterable):
            seen_add(element)
            yield element
    else:
        for element in iterable:
            k = key(element)
            if k not in seen:
                seen_add(k)
                yield element


def mesh_to_cf_bounds(
    coord: Union[xr.DataArray, xr.IndexVariable],
    old_dim: str,
    new_dim: str,
    ds: Optional[xr.Dataset] = None,
    coordinate: bool = True,
    bounds_dim: str = "bnds",
    coord_name: Optional[str] = None,
    add_coordinate: bool = True,
) -> xr.Dataset:
    """Transform a mesh boundary variable to CF-conform bounds

    This function takes a coordinate with shape ``(l, m, n+1)`` and transforms
    it into a variable of shape ``(l, m, n, 2)``. ``n`` can be at any position
    of the variable. The exact position is defined by the `dim_map` parameter.

    Parameters
    ----------
    coord: xarray.DataArray or xarray.IndexVariable
        The original coordinate to transform
    old_dim: str
        The name of the dimension within the ``dims`` attribute of `coord` with
        size ``n+1``
    new_dim: str
        The new name of the dimension that will have size ``n``.
    ds: xarray.Dataset, optional
        The dataset where to store the new data into. By default, a new empty
        dataset will be created
    coordinate: bool, optional
        If True, generate the coordinate variable. If False, only the
        CF-conform bounds variable is created. By default True.
    bounds_dim: str, optional
        The name of the newly created dimension with shape 2, by default "bnds"
    coord_name: str, optional
        The name of the coordinate. This parameter will be ignored if
        `coordinate` is ``False``. If None, the coordinate will get the same
        name as `coord`. By default None.
    add_coordinate: bool, optional
        If True and `coordinate` is True, the generated `coordinate` will be
        added to the ``'coordinates'`` attribute of all variables in the
        provided dataset `ds` that have the all the dimensions of `coord`.
        By default True

    Returns
    -------
    xarray.Dataset
        The updated `ds` or a fresh dataset
    """
    if coord_name is None:
        coord_name = coord.name
    if ds is None:
        ds = xr.Dataset()
    bounds_data = np.concatenate(
        [
            coord.isel(**{old_dim: slice(0, -1)}).values[..., None],
            coord.isel(**{old_dim: slice(1, None)}).values[..., None],
        ],
        -1,
    )
    new_dims = list(coord.dims)
    i = new_dims.index(old_dim)
    new_dims.pop(i)
    new_dims.insert(i, new_dim)
    bounds_name = coord_name + "_bnds"
    ds.coords[bounds_name] = (
        new_dims + [bounds_dim],
        bounds_data,
        coord.attrs,
    )

    if coordinate:
        coord_vals = bounds_data.mean(axis=-1)
        coord_attrs = coord.attrs.copy()
        coord_attrs["bounds"] = bounds_name
        ds.coords[coord_name] = (new_dims, coord_vals, coord_attrs)
        if add_coordinate:
            for var in ds.variables.values():
                if set(new_dims) <= set(var.dims):
                    enc = (
                        var.attrs
                        if "coordinates" in var.attrs
                        else var.encoding
                    )
                    da_coordinates = enc.get("coordinates", "")
                    da_coordinates = coord_name + " " + da_coordinates
                    enc["coordinates"] = da_coordinates.strip()
    return ds


def get_distance_from_start(points: np.ndarray) -> np.ndarray:
    """Get the cumulative distance for a list of points.

    This function calculates the distance between consecutive points and
    generates the cumulative sum.

    Parameters
    ----------
    points : np.ndarray of shape [N, M]
        An array of point coordinates

    Returns
    -------
    np.ndarray of shape N
        The distance from the start of the path for each point in `points`.
    """
    dist = np.r_[0, np.linalg.norm(points[1:] - points[:-1], axis=-1).cumsum()]
    return dist


def nearest_points(
    points: np.ndarray,
    arrays: List[xr.DataArray],
    coords: List[xr.IndexVariable],
    coord_dims: List[str],
    cell_dim: str,
    exact: bool = False,
) -> List[xr.DataArray]:
    """Select the closest grid cells along a path.

    This method takes the closest grid cells along a transect using
    scikit-learns BallTree.

    Parameters
    ----------
    points : np.ndarray of shape [N, M]
        The path consisting of ``N`` points with ``M`` dimensions
    arrays : List[xr.DataArray]
        The data arrays to extract
    coords : List[xr.IndexVariable]
        The list of the ``M`` coordinates that belong to the given `arrays`
    coord_dims : List[str]
        The names of each of the ``M`` dimensions. This list must have the same
        number of dimensions as the size of the second dimension in `points`.
    cell_dim : str
        The name of the dimension to generate for the new arrays.
    exact : bool, optional
        If True, the resulting dimension indicated by `cell_dim` will have the
        size ``N``, otherwise we will only keep the unique cells within the
        given `coords`.

    Returns
    -------
    List of xr.DataArray
        The given `arrays` at the location indicated by the given `points`
    """
    def expand_segment(p0, p1):
        N = int(np.max(np.ceil(np.abs(p1 - p0) / min_dist)))
        return np.concatenate(
            [np.linspace(a, b, N)[:, None] for a, b in zip(p0, p1)], -1
        )

    grid_points = np.concatenate(
        [coord.values.reshape((-1, 1)) for coord in coords], -1
    )
    tree = BallTree(grid_points)

    dist = np.abs(grid_points[1:] - grid_points[:-1])
    min_dist = np.where(dist > 0, dist, np.inf).min(0)
    if not exact:
        points = np.concatenate(
            [expand_segment(p0, p1) for p0, p1 in zip(points, points[1:])], 0
        )
        indices = np.array(
            list(
                unique_everseen(
                    tree.query(
                        points, return_distance=False, sort_results=False
                    )[:, 0]
                )
            )
        )
    else:
        indices = np.array(
            list(
                tree.query(points, return_distance=False, sort_results=False)[
                    :, 0
                ]
            )
        )

    ret = []

    coord_names = [coord.name for coord in coords]

    new_coord = np.arange(indices.size)

    for da in arrays:
        dims_to_keep = tuple(dim for dim in da.dims if dim not in coord_dims)
        nkeep = len(dims_to_keep)
        transposed = da.transpose(
            *(dims_to_keep + coords[0].dims), transpose_coords=True
        )
        reshaped = transposed.values.reshape(transposed.shape[:nkeep] + (-1,))
        cell_data = reshaped[..., indices]

        da_coords = {
            key: val
            for key, val in da.coords.items()
            if set(val.dims) <= set(dims_to_keep)
        }
        da_coords[cell_dim] = new_coord

        nkeep = len(dims_to_keep)

        new = xr.DataArray(
            cell_data,
            dims=dims_to_keep + (cell_dim,),
            coords=da_coords,
            attrs=da.attrs,
            name=da.name,
        )

        encoding = {
            key: val
            for key, val in da.encoding.items()
            if key != "original_shape"
        }

        remove_coordinates(new.attrs, coord_names, [cell_dim])
        remove_coordinates(encoding, coord_names, [cell_dim])

        new.encoding.update(encoding)
        if dims_to_keep:
            first_coord = min(map(da.dims.index, coord_dims))
            if first_coord <= nkeep:
                new_dims = list(dims_to_keep)
                new_dims.insert(first_coord, cell_dim)
                new = new.transpose(*new_dims, transpose_coords=True)
        ret.append(new)

    return ret


def interpolate_points(
    points: np.ndarray,
    arrays: List[xr.DataArray],
    coords: List[xr.IndexVariable],
    coord_dims: List[str],
    cell_dim: str,
    method: str = "inverse_distance_weighting",
    **kws: Any,
) -> List[xr.DataArray]:
    """Interpolate data arrays along a path.

    This method interpolates data arrays to a path indicated by an array
    of points.

    Parameters
    ----------
    points : np.ndarray of shape [N, M]
        The path consisting of ``N`` points with ``M`` dimensions
    arrays : List[xr.DataArray]
        The data arrays to extract
    coords : List[xr.IndexVariable]
        The list of the ``M`` coordinates that belong to the given `arrays`
    coord_dims : List[str]
        The names of each of the ``M`` dimensions. This list must have the same
        number of dimensions as the size of the second dimension in `points`.
    cell_dim : str
        The name of the dimension to generate for the new arrays.
    exact : bool, optional
        If True, the resulting dimension indicated by `cell_dim` will have the
        size ``N``, otherwise we will only keep the unique cells within the
        given `coords`.

    Returns
    -------
    List of xr.DataArray
        The given `arrays` at the location indicated by the given `points`
    """
    # TODO: You can specify the coord system here, too!
    import pyinterp

    mesh = pyinterp.RTree()

    grid_points = np.vstack([np.ravel(coord) for coord in coords]).T

    ret = []

    if method != "inverse_distance_weighting":
        kws["rbf"] = method
        method = "radial_basis_function"

    interp = getattr(mesh, method)

    for da in arrays:
        dims_to_keep = tuple(dim for dim in da.dims if dim not in coord_dims)
        nkeep = len(dims_to_keep)
        if nkeep:
            stacked = da.stack(__newdim=dims_to_keep)
        else:
            stacked = da.expand_dims("__newdim", axis=-1)
        cell_data = np.zeros(
            (len(points), stacked.shape[-1]), dtype=stacked.dtype
        )
        for i in range(stacked.shape[-1]):
            mesh.packing(grid_points, stacked.values[..., i].ravel())
            interpolated = interp(points, **kws)[0]
            cell_data[:, i] = interpolated

        da_coords = {
            name: var
            for name, var in stacked.coords.items()
            if var.dims == ("__newdim",)
        }

        da_coords[cell_dim + "_distance"] = (
            cell_dim,
            get_distance_from_start(points),
            {"long_name": "Euclidean distance from the start of the transect"},
        )

        new = xr.DataArray(
            cell_data,
            dims=(cell_dim, "__newdim"),
            coords=da_coords,
            attrs=stacked.attrs,
            name=stacked.name,
        )

        encoding = {
            key: val
            for key, val in da.encoding.items()
            if key != "original_shape"
        }

        new.encoding.update(encoding)

        if nkeep:
            new = new.unstack("__newdim")
        else:
            new = new[..., 0]

        ret.append(new)
    return ret


def select_transect(
    points, ds, *coords, exact=False, cell_dim=None, method="nearest", **kws
):

    npoints, ncoords = np.asarray(points).shape
    if len(coords) != ncoords:
        raise ValueError(
            f"Number of coordinates ({len(coords)}) does not match"
            f"size of second dimension in points ({ncoords})!"
        )
    coord_dims = set(chain.from_iterable(coord.dims for coord in coords))
    if cell_dim is None:
        cell_dim = "transect_cell"
        while cell_dim in ds.dims:
            cell_dim += "_cell"
    arrays = [
        ds[key] for key in ds.variables if coord_dims <= set(ds[key].dims)
    ]
    ds = ds.copy()

    if arrays:
        da = arrays[0].isel(
            **{dim: 0 for dim in set(arrays[0].dims) - coord_dims}
        )
        coords = xr.broadcast(*(list(coords) + [da]))[:-1]
    else:
        coords = xr.broadcast(list(coords))
        coord_dims = set(coords[0].dims)

    if method == "nearest":
        interpolated = nearest_points(
            points, arrays, coords, coord_dims, cell_dim, exact=exact, **kws
        )
    else:
        interpolated = interpolate_points(
            points, arrays, coords, coord_dims, cell_dim, method=method, **kws
        )
    for da in interpolated:
        if da.name in ds.coords:
            ds.coords[da.name] = da
        else:
            ds[da.name] = da

    # add the distance within the transect
    # coord_names = [c.name for c in coords]
    # new_points = np.dstack(
    #     [c.values for name, c in ds.variables.items() if name in coord_names]
    # )[0]
    # ds[cell_dim + "_distance"] = (
    #     "cell_dim",
    #     get_distance_from_start(new_points),
    #     {"long_name": "Euclidean distance from the start of the transect"},
    # )

    return ds


def remove_coordinates(encoding, coord_names, new_coords=[]):
    if "coordinates" in encoding:
        coord_attr = encoding["coordinates"]
        for coord_name in coord_names:
            coord_attr = coord_attr.replace(coord_name, "")
        if new_coords:
            encoding["coordinates"] = (
                coord_attr.strip() + " " + " ".join(new_coords)
            )


def select_level(level, ds, coord, dim):
    coord_dims = set(coord.dims)
    arrays = [
        ds[key] for key in ds.variables if coord_dims <= set(ds[key].dims)
    ]
    ds = ds.copy()

    if arrays:
        da = arrays[0].isel(
            **{dim: 0 for dim in set(arrays[0].dims) - coord_dims}
        )
        coord = xr.broadcast(coord, da)[0]

    selection = xr.ufuncs.fabs(coord - level).argmin(dim)

    for da in arrays:
        if da.name in ds.coords:
            ds.coords[da.name] = da[selection]
        else:
            ds[da.name] = da[selection]
        remove_coordinates(da.attrs, [coord.name])
        remove_coordinates(da.encoding, [coord.name])
    ds.coords[coord.name] = ((), level, coord.attrs)

    return ds
