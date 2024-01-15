"""Command line interface (cli) for calculating swath profiles."""

import argparse
import logging
from pathlib import Path
from typing import List, Optional, Union

import nbclient
import nbformat
from ipykernel.kernelspec import install as install_kernel
from nbparameterise import (
    extract_parameters,
    parameter_values,
    replace_definitions,
)
from tqdm import tqdm

from raincoat_takehome_science import __version__, calculate_swath, logger

CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}


def swath_cli(argv: Optional[List[str]] = None) -> None:
    """Command line interface for calculating swath profiles."""

    parser = argparse.ArgumentParser(
        prog=logger.name,
        description=(
            "This command takes a given yaml configuration file and "
            "calculates the swath profiles from hurricane b-deck "
            "track data provided by NOAHH. Swath profile calculation "
            "is based on the  Jelesnianski formula for w2nd speed."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        epilog=(
            "See https://github.com/antarcticrainforest/raincoat-takehome-science"
            " for more details."
        ),
    )
    parser.add_argument(
        "config_path",
        type=Path,
        help=(
            "Path to the yaml configuration file, holding"
            "the necessary information"
        ),
    )
    parser.add_argument(
        "--plot",
        action="store_true",
        default=False,
        help="Create plots of the calculated data",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        help="Increase verbosity (debug mode).",
        default=0,
        action="count",
    )
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version="%(prog)s {version}".format(version=__version__),
    )

    args = parser.parse_args(argv)
    log_levels = [logging.ERROR, logging.WARNING, logging.INFO, logging.DEBUG]
    log_level = log_levels[min(args.verbose, len(log_levels) - 1)]
    logger.setLevel(log_level)
    logger.cli = True
    nc_dataset = calculate_swath(args.config_path.expanduser())
    Path(nc_dataset.attrs["file_name"]).unlink(missing_ok=True)
    nc_dataset.to_netcdf(
        nc_dataset.attrs["file_name"], engine="h5netcdf", mode="w"
    )
    execute_notebook(
        Path(__file__).parent / "notebooks" / "windfield-tmpl.ipynb",
        args.config_path.parent / "notebooks" / "windfield.ipynb",
        netcdf_file=nc_dataset.attrs["file_name"],
        variable="wsp",
    )


def execute_notebook(
    notebook_tmpl: Union[str, Path],
    notebook_output: Union[str, Path],
    **params: Union[str, int, float, bool],
) -> None:
    """Parametrise and execute a jupyter notebook.

    Parameters
    ----------
    notebook_tmpl: str, Path
        The input notebook that is parametrised.
    notebook_output: str, Path
        The parametrised notebook that executed.
    **params:
        Parameters that are added to the parametrised notebook.
    """
    install_kernel(user=True, kernel_name="swath", display_name="Swath")
    with open(notebook_tmpl) as stream:
        nb = nbformat.read(stream, as_version=4)
    parameters = parameter_values(
        extract_parameters(nb, tag="parameters"), **params
    )
    new_notebook = replace_definitions(nb, parameters)
    notebook_output = Path(notebook_output).expanduser().absolute()
    notebook_output.parent.mkdir(exist_ok=True, parents=True)
    client = nbclient.NotebookClient(new_notebook, store_widget_state=False)
    with client.setup_kernel():
        try:
            for num, cell in tqdm(
                enumerate(new_notebook.cells),
                desc="Executing notebook",
                leave=True,
                total=len(new_notebook.cells),
            ):
                client.execute_cell(cell, num)
        except Exception:
            logger.error('Error executing the notebook "%s".', notebook_output)
            raise
        finally:
            nbformat.write(new_notebook, notebook_output)
    log_level = logger.getEffectiveLevel()
    logger.setLevel(logging.INFO)
    logger.info(
        "Notebook execution successful, find your notebook in %s",
        notebook_output,
    )
    logger.setLevel(log_level)


if __name__ == "__main__":
    swath_cli()
