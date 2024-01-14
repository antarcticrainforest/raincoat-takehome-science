"""Reading and manipulating datasets."""
from io import StringIO
from typing import Mapping, Optional, Any, List, Tuple, Union

import dask
import dask.array
import numpy as np
from numpy.typing import NDArray
import pandas as pd
import xarray as xr
from .utils import logger
from .path import calculate_wind_at_given_distance

# From https://www.nrlmry.navy.mil/atcf_web/docs/database/new/abdeck.txt
b_deck_columns = [
    "BASIN",
    "CY",
    "YYYYMMDDHH",
    "TECHNUM/MIN",
    "TECH",
    "TAU",
    "Lat",
    "Lon",
    "VMAX",
    "MSLP",
    "TY",
    "RAD",
    "WINDCODE",
    "RAD1",
    "RAD2",
    "RAD3",
    "RAD4",
    "POUTER",
    "ROUTER",
    "RMW",
    "GUSTS",
    "EYE",
    "SUBREGION",
    "MAXSEAS",
    "INITIALS",
    "DIR",
    "SPEED",
    "STORMNAME",
    "DEPTH",
    "SEAS",
    "SEASCODE",
    "SEAS1",
    "SEAS2",
    "SEAS3",
    "SEAS4",
    "USERDEFINED",
    #    "userdata",
]


def read_b_deck(input_data: Union[bytes, str]) -> pd.DataFrame:
    """Convert a datastream downloaded from to a pandas DataFrame.

    Parameters
    ----------
    input_data: str, bytes
        Data stream of the b deck data.

    Returns
    -------
    pd.DataFrame: a pandas dataframe representation of the data.
    """

    if isinstance(input_data, bytes):
        data_string = input_data.decode("utf-8")
    else:
        data_string = input_data
    try:
        df = pd.read_csv(
            StringIO(data_string),
            header=None,
            names=b_deck_columns,
            delimiter=",",
            engine="python",
            na_values="",
            # NOTE: Only fields 1-36 seem to be fixed:
            # https://www.nrlmry.navy.mil/atcf_web/docs/database/new/abdeck.txt
            # that means the data needs to be pruned.
            usecols=range(36),
        )
    except Exception as error:
        logger.error_handle(error)
    # Convert the time stamp:
    try:
        df["YYYYMMDDHH"] = pd.to_datetime(df["YYYYMMDDHH"], format="%Y%m%d%H")
    except Exception as error:
        raise ValueError(f"Could not convert time stamps, {error}") from error

    def convert_lat_lon(lat_lon_string: str) -> float:
        """Helper to convert a lon/lat in 120N (120W) format to a float."""
        value = float(lat_lon_string[:-1]) / 10
        direction = lat_lon_string[-1]
        if direction in ("S", "W"):
            value = -value
        return value

    try:
        df["Lat"] = df["Lat"].apply(convert_lat_lon)
        df["Lon"] = df["Lon"].apply(convert_lat_lon)
    except Exception as error:
        raise ValueError(
            "Could not convert positions to float: {error}"
        ) from error
    # Convert units to SI units
    df["VMAX"] *= 0.514444  # kts to m/s
    df["SPEED"] *= 0.51444  # kts to m/s
    df["MAXSEAS"] *= 0.3048  # ft to m
    df["SEAS"] *= 0.3048  # ft to m
    for key in [f"RAD{i}" for i in range(1, 5)] + ["RMW", "ROUTER"]:
        df[key] *= 1609.34  # mi to m
    return df


class Dataset(xr.Dataset):
    """Create a xarray dataset from a given region of interest and resolution.

    Parameters
    ----------
    roi: tuple
        The region of interest
    resolution: tuple
        The dataset lon/lat resolution
    """

    __slots__ = ()

    def __init__(self, **kwargs: Optional[Mapping[Any, Any]]):
        super().__init__(**kwargs)

    @classmethod
    def from_roi(
        cls,
        roi: Tuple[float, ...],
        resolution: Tuple[float, ...],
    ) -> "Dataset":
        lon = xr.DataArray(
            np.arange(
                roi[-2],
                roi[-1] + resolution[-1],
                resolution[-1],
            ),
            name="lon",
            dims=("lon",),
            attrs={
                "long_name": "longitude",
                "units": "degrees_east",
                "axis": "X",
                "short_name": "lon",
            },
        )
        lat = xr.DataArray(
            np.arange(
                roi[0],
                roi[1] + resolution[0],
                resolution[0],
            ),
            name="lat",
            dims="lat",
            attrs={
                "long_name": "latitude",
                "units": "degrees_north",
                "axis": "Y",
                "short_name": "lat",
            },
        )
        return cls(coords={"lon": lon, "lat": lat})

    def calculate_wind_profile(self, b_deck: pd.DataFrame) -> None:
        """The methods adds a wind profile to the data."""
        geo_loc = np.meshgrid(self.lat, self.lon, indexing="ij")
        times = sorted(b_deck["YYYYMMDDHH"].unique())
        wind_speed = []

        # Function to calculate wind speed for a given time
        @dask.delayed  # type: ignore
        def calculate_wind_speed(
            time: np.datetime64,
            lat_lon: List[NDArray[np.float_]],
        ) -> float:
            max_wind = b_deck.loc[b_deck["YYYYMMDDHH"] == time]["VMAX"].values[
                -1
            ]
            wind_radius = b_deck.loc[b_deck["YYYYMMDDHH"] == time][
                "RMW"
            ].values[-1]
            storm_centre = np.meshgrid(*lat_lon, indexing="ij")
            return calculate_wind_at_given_distance(
                max_wind, wind_radius, geo_loc, storm_centre
            )

        # Create Dask delayed objects for lazy computation
        delayed_tasks = []
        for t, time in enumerate(times):
            lat_lon = b_deck.loc[b_deck["YYYYMMDDHH"] == time][
                ["Lat", "Lon"]
            ].values[-1]
            task = calculate_wind_speed(time, lat_lon)
            delayed_tasks.append(task)

        # Execute the delayed computations in parallel using Dask
        wind_speed = dask.array.stack(
            [
                dask.array.from_delayed(
                    task, shape=(len(self.lat), len(self.lon)), dtype=float
                )
                for task in delayed_tasks
            ]
        )
        time_index = pd.DatetimeIndex(times).to_pydatetime()
        self["time"] = xr.DataArray(
            time_index,
            name="time",
            coords={"time": time_index},
            dims=("time",),
            attrs={
                "long_name": "time",
                "axis": "T",
            },
        )
        self["wsp"] = xr.DataArray(
            wind_speed.rechunk().persist(),
            name="wsp",
            dims=("time", "lat", "lon"),
            attrs={
                "long_name": "swath wind speed",
                "short_name": "wsp",
                "units": "m/s",
            },
        )
        self.attrs["time_max"] = time_index[0].strftime("%Y%M%dT%H%M")
        self.attrs["time_min"] = time_index[-1].strftime("%Y%M%dT%H%M")
