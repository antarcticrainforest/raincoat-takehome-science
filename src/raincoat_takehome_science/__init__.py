"""Hurricane Track Analysis and Swath Generation for a given Hurricane.

This Python package processes hurricane track data provided in b-deck files.

It calculates the maximum wind speed using the Jelesnianski (1965) formula
for V(r) and generates a swath over a region of interest based on the
calculated wind speeds.

The calculated wind fields are saved in netCDF4 format, additionally
the package provides a simple plotting routine for displaying the wind
intensity over Puerto Rico in units of m/s.

For more information, refer to the README file or additional documentation.
"""
from pathlib import Path
from typing import Union
import xarray as xr

from .utils import Config, logger, download_file
from .data import read_b_deck, Dataset

__version__ = "2023.0.0"

__all__ = ["Config", "logger", "calculate_swath"]


def calculate_swath(config_path: Union[str, Path]) -> xr.Dataset:
    """Calculate the swath."""

    cfg = Config(config_path)
    # deck_data = read_b_deck(download_file(cfg.url))
    deck_data = read_b_deck(
        Path("~/Downloads/bal152017.dat").expanduser().read_text()
    )
    try:
        dset = Dataset.from_roi(cfg.roi or (), cfg.resolution or ())
        dset.calculate_wind_profile(deck_data)
    except Exception as error:
        logger.error_handle(error, "Could not calculate wind speeds")
    out_file = (
        cfg.netcdf_dir
        / f"swath_output_{dset.attrs['time_min']}-{dset.attrs['time_max']}.nc"
    )
    cfg.netcdf_dir.mkdir(exist_ok=True, parents=True)
    dset.attrs["file_name"] = str(out_file)
    return dset
