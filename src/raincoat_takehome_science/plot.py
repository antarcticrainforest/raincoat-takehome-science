"""Routines for displaying data."""

import cartopy.crs as ccrs
from matplotlib import pyplot as plt
import xarray as xr
import pandas as pd

import ipywidgets as widgets
import matplotlib.pyplot as plt
from IPython.display import display
import xarray as xr


class InteractiveMapPlotWidget:
    """Visualise xarray DataArray with a time dimension.

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

    update_plot(change: dict) -> None:
        Callback function to update the plot based on the time slider value.

    display_widget() -> None:
        Displays the widget with the time slider and output plot.
    """

    def __init__(self, dataarray):
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
        self.cbar = plt.colorbar(
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

    def _update_plot(self, change):
        """
        Callback function to update the plot based on the time slider value.
        """
        with self.plot_output:
            self.im.set_array(
                self.dataarray.isel(
                    time=self._time_slider.value
                ).values.flatten()
            )
            self.fig.canvas.draw_idle()

    def display_widget(self):
        """Displays the widget with the time slider and output plot."""
        display(widgets.VBox([self._time_slider, self.plot_output]))
