# -*- coding: utf-8 -*-
"""
Created on Tue Oct 27 17:04:01 2026

@author: brian

This script does some exploratory analysis of flux data collected during the
month of October 2026. Flux measurements have been collected every Monday this
month and have been cleaned. As of this analysis, I have some uncertainty
around the internal collar diameters. I'd like to verify the diameters again
in the field.
"""
import os
from pathlib import Path
import pandas as pd
import numpy as np
import statsmodels as sm
from matplotlib import pyplot as plt

repository = Path(os.getcwd())
octoberFolder = repository/"Data"/"Input"/"Soil gas efflux"/"2026"/"October"/"Clean"
outputFolder = repository/"Data"/"Output"

fluxes5path = octoberFolder/"October 5, 2026 fluxes.xlsx"
fluxes5 = pd.read_excel(fluxes5path, "Data")
fluxes5["date"] = 5

fluxes12path = octoberFolder/"October 12, 2026 fluxes.xlsx"
fluxes12 = pd.read_excel(fluxes12path, "Data")
fluxes12["date"] = 12

fluxes19path = octoberFolder/"October 19, 2026 fluxes.xlsx"
fluxes19 = pd.read_excel(fluxes19path, "Data")
fluxes19["date"] = 19

fluxes26path = octoberFolder/"October 26, 2026 fluxes.xlsx"
fluxes26 = pd.read_excel(fluxes26path, "Data")
fluxes26["date"] = 26
# %%
"""Let's just focus on CO2. For each plot on each day, let's take the mean of
the 2 or 3 measurements for that plot."""
fluxesColumnsDrop = ["CO2fluxSlope", "remark", "gasAnalyzer", "chamberVolume",
                     "gasAnalyzerVolume", "totalVolume", "P_o", "T_o", "W_o",
                     "methaneFluxSlope", "dateTime", "idTag"]
fluxesCombined = (pd.concat([fluxes5, fluxes12, fluxes19, fluxes26])
                  .drop(columns=fluxesColumnsDrop)
                  )
fluxesCO2 = fluxesCombined.drop(columns=["methaneFlux", "methaneFlux_Rsquared"])

# Calculating mean CO2 flux per plot at each time point
CO2perPlot = (fluxesCO2.groupby(["date", "plotType", "plotNumber"])["CO2flux"].mean()
              .reset_index()
              )
CO2perPlot["subject"] = CO2perPlot.plotType + CO2perPlot.plotNumber.astype("string")
CO2perPlotERConly = CO2perPlot.query("plotType != 'Grass'")

"""Getting summary statistics for CO2 flux per plot type at a specific date"""
CO2perPlotType = (CO2perPlot.groupby(["date", "plotType"])["CO2flux"].describe()
                  .reset_index()
                  )

"""Now let's make a time series line plot of flux values for the 3 plot types
vs each date. I will plot the mean flux for each plot type as a line and I will
shade around the mean using the 25th and 75h percentiles. For color schemes, I
will use the color palette proposed by Okabe and Ito
https://jfly.uni-koeln.de/color/
"""
figure = plt.Figure((15, 6))
timeSeries = figure.add_subplot(1, 2, 1)
colors = {"Tree": (204/255, 121/255, 167/255), "Grove": (0, 158/255, 115/255), "Grass": (240/255, 228/255, 66/255)}
for plotType in colors:
    color = colors[plotType]
    df = CO2perPlotType.loc[CO2perPlotType.plotType == plotType]
    timeSeries.plot(df["date"], df["50%"], ".-", color=color, label=plotType)
    timeSeries.fill_between(df["date"], df["25%"], df["75%"], color=color, alpha=0.4)
timeSeries.legend()
timeSeries.set_xticks([5, 12, 19, 26])
timeSeries.set_yticks(np.arange(0, 10))
timeSeries.grid()
timeSeries.set_xlabel("Day in October")
timeSeries.set_ylabel(r"$CO_2\/\/ flux\/\/ (\mu mol\/\/ CO_2/(m^2 * s))$")

"""Out of curiosity, I'm gonna look at methane, too."""
fluxesMethane = (fluxesCombined.query("methaneFlux.notna()")
                 .drop(columns=["CO2flux", "CO2flux_Rsquared"])
                 )
methanePerPlot = (fluxesMethane.groupby(["date", "plotType", "plotNumber"])["methaneFlux"].mean()
                  .reset_index()
                  )
"""Let's flip signs for the flux values to reflect drawdown instead."""
methanePerPlot["methaneDrawdown"] = -1 * methanePerPlot.methaneFlux

methanePerPlotType = (methanePerPlot.groupby(["date", "plotType"])["methaneDrawdown"].describe()
                      .reset_index()
                      )




timeSeries2 = figure.add_subplot(1, 2, 2)
for plotType in colors:
    color = colors[plotType]
    df = methanePerPlotType.loc[methanePerPlotType.plotType == plotType]
    timeSeries2.plot(df["date"], df["50%"], ".-", color=color)
    timeSeries2.fill_between(df["date"], df["25%"], df["75%"], color=color, alpha=0.4)
timeSeries2.set_xticks([5, 26])
timeSeries2.grid()
timeSeries2.set_xlabel("Day in October")
timeSeries2.set_xlabel("Day in October")
timeSeries2.set_ylabel(r"$CH_4\/\/ drawdown\/\/ (nmol\/\/ CH_4/(m^2 * s))$")

# %%
# Exporting the figure
exportPath = outputFolder/"Soil gas efflux"/"October 2026 efflux.png"
if os.path.exists(exportPath) is False:
    figure.savefig(exportPath, bbox_inches="tight", dpi=400)
