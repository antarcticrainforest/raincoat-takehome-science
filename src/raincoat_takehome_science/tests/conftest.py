"""Definitions for pytest."""
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Iterator

import pytest
import yaml


@pytest.fixture(scope="session")
def config_file() -> Iterator[Path]:
    """Definition of a test configuration."""
    with TemporaryDirectory() as temp_dir:
        config = {
            "input": {"year": 2017, "storm_number": 15, "basin": "al"},
            "roi": {
                "min_latitude": 17.5,
                "max_latitude": 18.5,
                "min_longitude": -67.5,
                "max_longitude": -65.5,
            },
            "output": {
                "resolution": [0.1, 0.1],
                "netcdf_dir": str(Path(temp_dir) / "data"),
                "plot_dir": str(Path(temp_dir) / "data"),
            },
        }
        config_file = Path(temp_dir) / "config.yml"
        with config_file.open("w") as stream:
            stream.write(yaml.dump(config))
        yield config_file
