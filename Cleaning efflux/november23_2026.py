# -*- coding: utf-8 -*-
"""
Created on Wed Nov 25 16:18:48 2026

@author: brian

On Monday November 23, 2026, we used the 7825 to measure CO2 fluxes in the
field for each collar twice, such that we were at Kessler 8 AM - 6:30 PM. The
7825 only measured CO2 concentration (similar to the 870, different from the
7810) and, unlike the other 2 gas analyers, it can also measure carbon isotopic
ratios of respiration. This script will clean both flux and carbon isotope
data as measured by the 7825 on this day.

The 7825 has no capability of sending concentration and carbon isotope data to
the smart chamber yet, and so I had to download a file from the smart chamber,
a separate file from the 7825, and merge these together in Soil Flux Pro by
timestamps. The 7825 is 1 hour ahead of the smart chamber, and this is likely
due to the 1 hour time change earlier this month. When I imported the 7825 data
into Soil Flux Pro, I had to adjust the time stamps by 1 hour backwards (-3600 s).
I also had to manually enter the volume of the gas tubing. I then performed
Keeling regressions as well as regressions of 13CO2 concentration vs 12CO2
concentrations on Soil Flux Pro. I then exported the resulting data as a .csv
file. I will be cleaning the .csv file here.
"""
import effluxCleaning as ec
import os
from pathlib import Path
import pandas as pd
from openpyxl import Workbook

cwd = Path(os.getcwd())
repository = Path(os.path.dirname(cwd))
dataFolder = repository/"Data"
november2026data = dataFolder/"Input"/"Soil gas efflux"/"2026"/"November"
november23path = november2026data/"November 23, 2026 fluxes & isotopes.csv"
november23data = pd.read_csv(november23path)
unitsRow = november23data.loc[0]
november23data = november23data.loc[1:]
renameDict = {"TA initial_value": "T_o", "PA initial_value": "P_o",
              "LABEL": "idTag", "COLLAR_HEIGHT": "offset", "AREA": "soilArea",
              "C13_DELTA/CO2 (KEELING) INTERCEPT": "keelingIntercept",
              "C13_DELTA/CO2 (KEELING) r2": "keeling_Rsquared",
              "VOLUME": "chamberVolume", "H2O initial_value": "W_o",
              "C13/C12 (SLOPE) r2": "C13toC12_Rsquared",
              "C13/C12 (SLOPE) SLOPE": "C13toC12slope",
              "DATE_TIME initial_value": "startTime"}
toFloatList = ["T_o", "P_o", "C13_DELTA initial_value", "keelingIntercept",
               "keeling_Rsquared", "FCO2", "FCO2 R2", "FCO2 LIN", "offset",
               "FCO2 LIN_R2", "soilArea", "chamberVolume", "C13toC12_Rsquared",
               "C13toC12slope", "FCO2 dCdt", "FCO2 LIN_dCdt", "W_o"]
toFloatDict = {column: "float" for column in toFloatList}
november23data = (november23data.rename(columns=renameDict)
                  .astype(toFloatDict)
                  )
november23data = ec.plotAndCollar(november23data)
# %%
"""Removing Tree 13 collar B's measurement in the afternoon because it has
insanely low R2 values for flux"""
november23data = november23data.query("idTag != 'Tree13B_am'")

"""Soil flux pro calculates 2 different flux values for each measurment, 1
calculated using an exponential regression and 1 calculated using a linear
regression. I'm going to set conditions for which kind of flux value to use for
each measurement. For measurements where the exponential R squared is less than
0.98, I will use the linear flux value for that measurement since the linear
regressions tend to fit better."""
november23data.loc[november23data["FCO2 R2"] < 0.98, "CO2flux"] = november23data["FCO2 LIN"]
november23data.loc[november23data["FCO2 R2"] < 0.98, "CO2fluxSlope"] = november23data["FCO2 LIN_dCdt"]
november23data.loc[november23data["FCO2 R2"] < 0.98, "fluxRegression"] = "linear"
november23data.loc[november23data["FCO2 R2"] < 0.98, "CO2flux_Rsquared"] = november23data["FCO2 LIN_R2"]

november23data.loc[november23data["FCO2 R2"] >= 0.98, "CO2flux"] = november23data["FCO2"]
november23data.loc[november23data["FCO2 R2"] >= 0.98, "CO2fluxSlope"] = november23data["FCO2 dCdt"]
november23data.loc[november23data["FCO2 R2"] >= 0.98, "fluxRegression"] = "exponential"
november23data.loc[november23data["FCO2 R2"] >= 0.98, "CO2flux_Rsquared"] = november23data["FCO2 R2"]

"""There's 1 measurement that I need to recalculate its flux value for. Tree 15
collar B, the afternoon measurement used the wrong value for the offset. I'm
correcting the offset and flux here"""
november23data.loc[november23data.idTag == "Tree15B_pm", "offset"] = 8.925
tree15BpmVolume = (november23data.loc[november23data.idTag == "Tree15B_pm", "offset"] * november23data.loc[november23data.idTag == "Tree15B_pm", "soilArea"]) + november23data.loc[november23data.idTag == "Tree15B_pm", "chamberVolume"] + 46.96
tree15BpmDryFraction = 1 - (november23data.loc[november23data.idTag == "Tree15B_pm", "W_o"]/1e6)
R = 8.31446261815324
tree15BpmKelvin = november23data.loc[november23data.idTag == "Tree15B_pm", "T_o"] + 273.15
november23data.loc[november23data.idTag == "Tree15B_pm", "CO2flux"] = november23data.loc[november23data.idTag == "Tree15B_pm", "CO2fluxSlope"] * november23data.loc[november23data.idTag == "Tree15B_pm", "P_o"] * tree15BpmVolume * tree15BpmDryFraction * 10/(R * tree15BpmKelvin * november23data.loc[november23data.idTag == "Tree15B_pm", "soilArea"])

# Obtaining time of day from a measurement's idTag
november23data["timeOfDay"] = november23data.idTag.str.extract(r"^[a-zA-Z0-9]+_([a-zA-Z]+)")
november23data.loc[november23data.timeOfDay == "am", "timeOfDay"] = "morning"
november23data.loc[november23data.timeOfDay == "pm", "timeOfDay"] = "afternoon"

"""So the handout that Liukang sent showed 2 ways of estimating carbon isotope
ratios of respiration. The 1st method is using the Keeling plot, which is a
fairly established method in the literature. The 2nd method is doing a linear
regression of the concentration of 13CO2 vs the concentration of 12CO2. Since
the Keeling regressions tend to be so terrible this time around, I'm going to
estimate carbon isotope ratios of respiration using the 2nd method."""
VPDB = 0.0112372
november23data["C13toC12regression_respirationD13C"] = ((november23data.C13toC12slope/VPDB) - 1) * 1000
# %%
"""Preparing the data for export. For each measurement, soil flux pro does 2
regressions to get 2 flux values. I'm just going to drop the original columns
that soil flux pro produced. I don't see a point in possessing 2 estimates for
flux like this."""
columnsDrop = ["FCO2", "FCO2 R2", "FCO2 LIN", "FCO2 LIN_R2", "FCO2 dCdt",
               "FCO2 LIN_dCdt", "COMMENT"]
november23data2 = november23data.drop(columns=columnsDrop)
n = [["On Monday November 23, 2026, we took the LI-7825 to Kessler to measure"],
     ["soil CO2 flux and the isotopic ratio of this CO2 flux from soil. We"],
     ["measured all 40 collars twice, once in the morning to early afternoon"],
     ["and then again from early afternoon till early evening. Afterwards, I"],
     ["downloaded the data from the 7825 and the smart chamber and then merged"],
     ["them together by timestamp using Soil Flux Pro. Unlike the 870 and 7810,"],
     ["which send concentration data to the smart chamber and so I only need to"],
     ["download data from the smart chamber, the 7825 does not send its"],
     ["measurement data (CO2 concentration and CO2 carbon isotopic ratios) to"],
     ["the smart chamber. Instead, users need to download data from each machine"],
     ["and then sync the data together using Soil Flux Pro."],
     [""],
     ["I expected that the syncing step might result in some problems. The time"],
     ["in the 7825 is ahead of the time in the smart chamber by 1 hour. I suspect"],
     ["that this is due to a recent time change earlier this month when clocks"],
     ["are shifted by 1 hour. The smart chamber follows GPS time while the 7825"],
     ["does not, and so the 7825 likely did not follow this 1 hour time change,"],
     ["resulting in a 1 hour mismatch between the 2 machines. While importing"],
     ["7825 data into Soil Flux Pro, I had to adjust the time downwards by 1"],
     ["hour (e.g. if the 7825 reports a measurement starting at 9:08 AM, then"],
     ["the measurement actually started at 8:08 AM and so I adjusted the time downwards)."],
     [""],
     ["Soil flux pro calculates 2 flux values for each measurement, with 1"],
     ["value calculated from an exponential regression while another calculated"],
     ["from a linear regression. The 3 measurements with the worst R-squared"],
     ["values from the exponential regression had R-squared values of 0.97745,"],
     ["0.64287, and less than 0.1. Tree 13 collar B's measurement in the afternoon"],
     ["was the measurement with the exponential R-squared value of less than 0.1,"],
     ["and so I dropped the measurement from the final dataset. Of the 2 remaining"],
     ["measurements (Grass 17 C in the afternoon with exponential R-squared 0.64 and"],
     ["Grass 13 A in the morning with exponential R-squared 0.97), their linear"],
     ["R-squared values were better (0.92321 and 0.99909, respectively), and so"],
     ["I used their linear flux values instead. Aside from these measurements,"],
     ["the R-squared values for flux were, surprisingly, very good, with exponential"],
     ["R-squared values all being greater than 0.998 or 0.999. The final dataset"],
     ["here has 79 measurements in total, with all collars having been measured"],
     ["twice while tree 13 collar B only has its measurement from the morning since"],
     ["I dropped its afternoon measurement."],
     [""],
     ["The R-squared values for the Keeling regressions, on the other hand,"],
     ["tend to be much lower. These R-squared values were all lower in grass"],
     ["than in groves and trees. This might be due to the relatively lower fluxes"],
     ["in grasses resulting in too small of a concentration change to get a"],
     ["good fit to the Keeling curve in grasses. So the Keeling regression is"],
     ["a bit suspect at least in grasses."],
     [""],
     ["Liukang sent a document describing a protocol for using the 7825. In"],
     ["the document, he described 2 methods for estimating the carbon isotopic"],
     ["ratios of respiration. One method is using the Keeling plot, which is"],
     ["fairly established in the literature already. The other method is to"],
     ["do a linear regression of the concentration of 13CO2 vs the concentration"],
     ["of 12CO2, and then use the slope to calculate the carbon isotopic ratio"],
     ["of respiration. This regression has much higher R-squared values than"],
     ["Keeling plot regressions (R-squared > 0.998). I calculated another"],
     ["estimate of delta 13C of respiration using this 2nd method."],
     [""]
     ]

um1 = ec.unitsMetadata1.copy()
um1.remove(["- methaneFlux: nanomole CH4 per square meter per second"])
um1.remove(["- methaneFluxSlope: ppb CH4 in dry air (or nanomole CH4 per mole dry air) per second"])

unitsMetadata2 = [["- startTime: the date and time when a specific measurement began"],
                  ["- C13_DELTA initial_value: initial carbon isotopic ratio of the air inside the chamber"],
                  ["- keelingIntercept: the y-intercept from the Keeling linear regression"],
                  ["- keeling_Rsquared: the R-squared from the Keeling linear regression"],
                  ["- C13toC12_Rsquared: the R-squared from the linear regression of"],
                  ["13CO2 concentration vs 12CO2 concentration"],
                  ["- fluxRegression: the type of regression used for the final flux"],
                  ["value for a measurement"],
                  ["- timeOfDay: when the measurement. 'morning' if the measurement"],
                  ["was the 1st measurement for the collar and taken during the morning"],
                  ["or early afternoon, 'afternoon' if the measurement was the 2nd"],
                  ["measurement for the collar and taken during the afternoon or early"],
                  ["evening"],
                  ["- C13toC12regression_respirationD13C: the carbon isotopic ratio of"],
                  ["soil CO2 efflux as calculated from the linear regression of"],
                  ["13CO2 concentration vs 12CO2 concentration"]
                  ]
n.extend(um1)
n.extend(unitsMetadata2)
exportPath = november2026data/"Clean"/"November 23, 2026 fluxes & isotopes.xlsx"
if os.path.exists(exportPath) is False:
    wb = Workbook()
    readMe = wb.active
    readMe.title = "ReadMe"
    for line in n:
        readMe.append(line)
    dataTab = wb.create_sheet("Data")
    dataTab.append(november23data2.columns.tolist())
    november23dataList = november23data2.to_numpy().tolist()
    for line in november23dataList:
        dataTab.append(line)
    wb.save(exportPath)
