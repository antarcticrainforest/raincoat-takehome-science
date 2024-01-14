"""Utility methods and classes for data processing."""

from io import BytesIO
import gzip
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

import appdirs
import requests
import yaml

APP_NAME = "swath-profiler"


class DownloadError(Exception):
    """Custom exception class for download errors."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class _Logger(logging.Logger):
    """Custom Logger class that extends the functionality of logging.Logger.

    This class overrides the error method to handle logging based on log levels.
    If the log level is DEBUG or below, it logs the exception and raises
    SystemExit; otherwise, it emits an error message.

    Attributes
    ----------
        name: str
            Name of the logger.
    """

    def __init__(self, name: str) -> None:
        """Initializes the CustomLogger instance and adds a rotating file handler.

        Parameters:
            name: str
                Name of the logger.
        """
        super().__init__(name)
        self.cli = False
        self._file_handle: RotatingFileHandler = self._get_file_handle()
        self._add_stream_handler()
        self.addHandler(self._file_handle)

    def _add_stream_handler(self) -> logging.StreamHandler:
        """
        Add a stream handler to the logger for logging to console.

        Returns:
            logging.StreamHandler: StreamHandler instance for logging to console.
        """
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.ERROR)

        # Set the format for the log messages
        stream_handler.setFormatter(logger_format)

        # Add the stream handler to the logger
        self.addHandler(stream_handler)
        return stream_handler

    @staticmethod
    def _get_file_handle() -> RotatingFileHandler:
        """Get a file log handle for the logger."""

        log_dir = Path(appdirs.user_log_dir(APP_NAME))
        log_dir.mkdir(exist_ok=True, parents=True)
        logger_file_handle = RotatingFileHandler(
            log_dir / f"{APP_NAME}.log",
            mode="a",
            maxBytes=5 * 1024**2,
            backupCount=5,
            encoding="utf-8",
            delay=False,
        )
        logger_file_handle.setFormatter(logger_format)
        logger_file_handle.setLevel(logging.INFO)
        return logger_file_handle

    @property
    def verbose_msg(self) -> str:
        """Define a message that tells the user what to do for more info."""
        if self.getEffectiveLevel() <= logging.DEBUG:
            return ""

        if self.cli:
            return "Increase verbosity (-v) for more information"
        return f"Use {__package__}.logger.setLevel(10) for more information"

    def error_handle(
        self, exception: BaseException, *args: Any, **kwargs: Any
    ) -> None:
        """
        Overrides the error method to handle logging based on log levels.

        Parameters
        ----------
            exception BaseException:
                Exception that occured.
            *args Any:
                Additional arguments.
            **kwargs Any:
                Additional keyword arguments.
        Raises:
            SystemExit, BaseException:
        """
        exception_to_raise: Union[SystemExit, BaseException] = exception
        if self.cli is True:
            exception_to_raise = SystemExit(1)
        if self.getEffectiveLevel() <= logging.DEBUG:
            self.exception(exception, *args, **kwargs)
        self.error("%s\n\n%s", exception, self.verbose_msg, *args, **kwargs)
        raise exception_to_raise

    def setLevel(self, level: Union[int, str]) -> None:
        """
        Overrides the setLevel method to synchronize the log level with the
        file handler.

        Parameters:
            level int, str:
                Log level to be set.
        """
        super().setLevel(level)
        for handle in self.handlers:
            handle.setLevel(level)
        self._file_handle.setLevel(level)


logging.basicConfig(
    format="%(name)s - %(asctime)s - %(levelname)s: %(message)s",
    level=logging.ERROR,
    datefmt="[%Y-%m-%dT%H:%M:%S]",
)
logger_format = logging.Formatter(
    "%(name)s - %(asctime)s - %(levelname)s: %(message)s",
    datefmt="[%Y-%m-%dT%H:%M:%S]",
)
logger = _Logger(APP_NAME)


class Config:
    """Configuration class to read and hold variables from a YAML file.

    Attributes
    ----------

    parsed_config:
        Parsed configuration that has been loaded from the yaml file.
    """

    url_tmpl: str = (
        "https://ftp.nhc.noaa.gov/atcf/archive/"
        "{year:04d}/b{basin}{storm_number:02d}{year:04d}.dat.gz"
    )

    def __init__(self, config_path: Union[str, Path]) -> None:
        """Initialises the class by reading the YAML file.

        Parameters
        ----------

        config_path:  str, Path
            Path to the YAML configuration file.
        """
        self.config_path = Path(config_path).expanduser()
        self.url: str = ""
        self.netcdf_dir: Optional[Path] = None
        self.plot_dir: Optional[Path] = None
        self.roi: Tuple[float, float, float, float] = ()
        self._resolution: Tuple[float, float] = ()
        try:
            self._load_config(self.config_path)
        except Exception as error:
            logger.critical(
                "Could not load configuration: %s", self.config_path
            )
            logger.error_handle(error)

    def _load_config(self, config_path: Path) -> None:
        """Load the yaml config file."""
        with config_path.open(encoding="utf-8") as file_path:
            config = yaml.safe_load(file_path)
        self.url = self.url_tmpl.format(**config["input"])
        self.netcdf_dir = Path(config["output"]["netcdf_dir"]).expanduser()
        if config["output"].get("plot_dir"):
            self.plot_dir = Path(config["output"]["plot_dir"]).expanduser()
        self.roi = tuple(
            float(config["roi"][k])
            for k in (
                "min_latitude",
                "max_latitude",
                "min_longitude",
                "max_longitude",
            )
        )
        self._resolution = list(map(float, config["output"]["resolution"]))

    @property
    def resolution(self) -> Tuple[float, float]:
        """Define the lon/lat resolution of the output data."""
        return tuple(map(float, self._resolution))


def download_file(url: str) -> bytes:
    """Download and read a file from the given URL.

    Parameters
    ----------
        url: str
            The URL of the file to download.

    Returns:
        bytes: The byte content of the downloaded file

    Raises:
        DownloadError: If the file could not be downloaded or read.
    """

    def _download(url: str) -> bytes:
        try:
            # Send GET request to download the file
            response = requests.get(url)
            if response.status_code == 200:
                # Read the content of the downloaded file
                file_content = BytesIO(response.content)
                if url.endswith(".gz"):
                    with gzip.open(file_content, "rb") as f:
                        return f.read()
                else:
                    return file_content.read()
            else:
                raise DownloadError(
                    "Failed to download file. "
                    f"Status code: {response.status_code}"
                )
        except requests.RequestException as error:
            raise DownloadError(f"Request Exception: {error}") from error

    try:
        return _download(url)
    except Exception as error:
        logger.error_handle(error)
