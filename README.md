# Raincoat Swath Profiler


[![Pipeline](https://github.com/antarcticrainforest/raincoat-takehome-science/actions/workflows/ci_job.yml/badge.svg)](https://github.com/antarcticrainforest/raincoat-takehome-science/actions)
[![codecov](https://codecov.io/gh/antarcticrainforest/raincoat-takehome-science/branch/cli-setup/graph/badge.svg)](https://app.codecov.io/gh/antarcticrainforest/raincoat-takehome-science)

This repository contains a command-line tool, swath-profiler, designed to
calculate hurricane wind profiles over a specified region using
the Jelesnianski (1965) formula for wind speed. The tool utilizes b-deck track
data provided by NOAA's National Hurricane Center (NHC) to generate a gridded
data fields of wind, which are then stored in NetCDF files.
Additionally, the tool creates a Jupyter notebook for visualising and
analysing the calculated wind profiles.


## Installation

To install the swath-profiler tool and its dependencies, follow these steps:

 - Clone the repository to your local machine:
    ```console
    git clone https://github.com/antarcticrainforest/raincoat-takehome-science.git
    ```
 - Navigate to the project directory:
    ```console
    cd raincoat-takehome-science
    ```
 - Install the required Python packages:
    ```console
    python3 -m pip install .
    ```


## Usage
### Configuration

Create a YAML configuration file (e.g., config.yml) with the required input
parameters. An example configuration file is provided in the repository.

```yaml

# Example YAML configuration file for hurricane analysis
---
input:
  year: 2017
  storm_number: 15
  basin: al
roi:
  min_latitude: 17.5
  max_latitude: 18.5
  min_longitude: -67.5
  max_longitude: -65.5
output:
  resolution: [0.1, 0.1]
  netcdf_dir: ~/workspace/raincoat-takehome-science/output/data
  plot_dir: ~/workspace/raincoat-takehome-science/output/png
```

### Running the Tool

Execute the swath-profiler command with the path to the configuration file:

```console

swath-profiler config.yml

Options:

    -v or --verbose: Increase verbosity (debug mode) (default: 0)
    -V or --version: Show program's version number and exit
```
The help menu is a follows:

```console
usage: swath-profiler [-h] [-v] [-V] config_path

This command takes a given yaml configuration file and calculates the swath profiles from hurricane b-deck track data provided by NOAHH. Swath profile calculation is
based on the Jelesnianski formula for w2nd speed.

positional arguments:
  config_path    Path to the yaml configuration file, holdingthe necessary information

options:
  -h, --help     show this help message and exit
  -v, --verbose  Increase verbosity (debug mode). (default: 0)
  -V, --version  show program's version number and exit

See https://github.com/antarcticrainforest/raincoat-takehome-science for more details.
```


### Jupyter Notebook

After running the tool, a Jupyter notebook is created. Open this notebook to
visualize and interact with the calculated wind profiles. The notebook
contains interactive widgets for inspecting the data and performing additional
analysis.

An example notebook can be found in [notebooks/windfield.ipynb](notebooks/windfield.ipynb).
