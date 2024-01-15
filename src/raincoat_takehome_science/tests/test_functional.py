"""Simple functional tests."""
from pathlib import Path

import xarray as xr
import yaml

from raincoat_takehome_science import calculate_swath
from raincoat_takehome_science.cli import swath_cli


def test_calculate_swath(config_file: Path) -> None:
    """Test the calculate swath method."""

    nc_dataset = calculate_swath(config_file)
    assert isinstance(nc_dataset, xr.Dataset)
    assert "wsp" in nc_dataset


def test_cli(config_file: Path) -> None:
    """Test the command line interface."""
    with config_file.open() as stream:
        config = yaml.safe_load(stream)
    swath_cli([str(config_file)])
    nc_dir = Path(config["output"]["netcdf_dir"])
    notebook_files = list(config_file.parent.rglob("*.ipynb"))
    netcdf_files = list(nc_dir.parent.rglob("*.ipynb"))
    assert len(netcdf_files) == 1
    assert len(notebook_files) == 1
