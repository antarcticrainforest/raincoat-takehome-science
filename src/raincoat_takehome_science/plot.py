"""Routines for displaying data."""
from typing import Any, Optional

import cartopy.crs as ccrs
import ipywidgets as widgets
import matplotlib.pyplot as plt
import pandas as pd
import xarray as xr
from IPython.display import clear_output, display
from matplotlib.colorbar import Colorbar


class InteractiveMapPlotWidget:
    """
    Visualize xarray DataArray with a time dimension.

    Parameters
    ----------
    dataarray : xarray.DataArray
        The input data array with dimensions (time, lat, lon).

    Attributes
    ----------
    dataarray : xarray.DataArray
        The input data array with dimensions (time, lat, lon).

    Methods
    -------
    plot_map(time_index: int) -> None:
        Plots the map for the specified time index using Cartopy.

    _update_plot(change: dict) -> None:
        Callback function to update the plot based on the time slider value.

    display_widget() -> None:
        Displays the widget with the time slider and output plot.
    """

    def __init__(self, dataarray: xr.DataArray) -> None:
        """
        Initialize the InteractiveMapPlotWidget2 class.

        Parameters
        ----------
        dataarray : xarray.DataArray
            The input data array with dimensions (time, lat, lon).
        """
        self.dataarray = dataarray
        self._time_slider = widgets.SelectionSlider(
            options=[
                (pd.Timestamp(time).strftime("%Y-%m-%d %H:%M"), i)
                for i, time in enumerate(dataarray.time.values)
            ],
            value=0,
            description="Select time step:",
            continuous_update=True,
            style={"description_width": "initial"},
            layout={"width": "80%"},
        )
        self.plot_output = widgets.Output()

        # Set up the initial plot
        self.fig, self.ax = plt.subplots(
            figsize=(10, 6), subplot_kw={"projection": ccrs.PlateCarree()}
        )
        self.im = self.ax.pcolormesh(
            dataarray.lon,
            dataarray.lat,
            dataarray.isel(time=0),
            cmap="viridis",
            transform=ccrs.PlateCarree(),
            vmin=float(self.dataarray.quantile(0.01).values),
            vmax=float(self.dataarray.quantile(0.99).values),
            shading="auto",
        )
        self.ax.coastlines()

        # Add colorbar
        self.cbar: Optional[Colorbar] = plt.colorbar(
            self.im,
            ax=self.ax,
            orientation="horizontal",
            shrink=0.7,
            extend="both",
            label=f"{dataarray.attrs['long_name']} [{dataarray.attrs['units']}]",
        )

        # Define the callback function for the slider
        self._time_slider.observe(self._update_plot, names="value")

        # Display the widget
        self.display_widget()

    def plot_map(self, time_index: int) -> None:
        """
        Plots the map for the specified time index using Cartopy.

        Parameters
        ----------
        time_index : int
            Index corresponding to the selected time step.
        """
        # Extract the data for the specified time index
        data_at_time = self.dataarray.isel(time=time_index)

        # Check if the figure already exists
        if not hasattr(self, "fig") or not plt.fignum_exists(self.fig.number):
            # If the figure doesn't exist, create a new one
            self.fig, self.ax = plt.subplots(
                figsize=(10, 6), subplot_kw={"projection": ccrs.PlateCarree()}
            )
            self.ax.coastlines()
            self.cbar = None

        # Clear the previous plot
        self.ax.clear()

        # Create a plot using Cartopy
        self.im = self.ax.pcolormesh(
            data_at_time.lon,
            data_at_time.lat,
            data_at_time,
            cmap="viridis",
            transform=ccrs.PlateCarree(),
            vmin=float(self.dataarray.quantile(0.01).values),
            vmax=float(self.dataarray.quantile(0.99).values),
            shading="auto",
        )

        # Add colorbar if it doesn't exist
        if self.cbar is None:
            self.cbar = plt.colorbar(
                self.im,
                ax=self.ax,
                orientation="horizontal",
                shrink=0.7,
                extend="both",
                label=f"{self.dataarray.attrs['long_name']} [{self.dataarray.attrs['units']}]",
            )

        self.ax.coastlines()

    def _update_plot(self, *args: Any, **kwargs: Any) -> None:
        """
        Callback function to update the plot based on the time slider value.
        """
        with self.plot_output:
            clear_output(wait=True)
            self.plot_map(self._time_slider.value)

    def display_widget(self) -> None:
        """Displays the widget with the time slider and output plot."""
        display(widgets.VBox([self._time_slider, self.plot_output]))
