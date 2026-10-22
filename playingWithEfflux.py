# -*- coding: utf-8 -*-
"""
Created on Wed Oct 14 23:22:46 2026

@author: brian

I'm going to play with the efflux data that we took on Monday October 5, 2026.
I had a conversation with a licor representative on October 14 and the rep
informed me that the smart chamber calculates fluxes using an exponential fit.
When I imported some flux data into SoilFLuxPro, I noticed that the exponential
fluxes calculated by SoilFluxPro were slightly different from the exponential
fluxes that the smart chamber produced. I want to inspect these differences.

Also SoilFluxPro can be used to adjust certain observations to get a better fit
to the CO2 concentrations measured for the observation. I want to see if I can
produce a json file containing only problematic observations to adjust in
SoilFluxPro
"""
import os
from pathlib import Path
import json
import pandas as pd
import scipy
from matplotlib import pyplot as plt
import openpyxl

repository = Path(os.getcwd())
october2026effluxFolder = repository/"Data"/"Input"/"Soil gas efflux"/"2026"/"October"
october5path = october2026effluxFolder/"2026105_KAEFS.json"
october5file = open(october5path, "r")
october5json = json.load(october5file)
october5file.close()
# %%
october5datasets = october5json["datasets"]
october5idTags = [list(dictionary)[0] for dictionary in october5datasets]
idTags = []
emptyObservation = []
methaneSummary = []
co2summary = []
concentrationDFs = []
metadata = []

for observation in october5datasets:
    idTag = list(observation)[0]
    idTags.append(idTag)
    """To access the underlying CO2 concentration & flux data, I need to go
    down several levels of dictionaries"""
    observationDict = observation[idTag]
    repsDictionary = observationDict["reps"]
    if len(repsDictionary) != 0: # if repsDictionary is an empty dictionary
        rep1dictionary = repsDictionary["REP_1"]
        header = rep1dictionary["header"]
        dataDictionary = rep1dictionary["data"]
        footerDictionary = rep1dictionary["footer"]
        fluxes = footerDictionary["fluxes"]
    if not fluxes: # if fluxes is an empty list
        emptyObservation.append(idTag)
    else:
        methaneFluxDict = fluxes[0]
        # methaneSummary.append({idTag: {"F_o": methaneFluxDict["F_o"], "t_o": methaneFluxDict["t_o"], "C_o": methaneFluxDict["C_o"], "a": methaneFluxDict["a"], "C_x": methaneFluxDict["C_x"], "r2": methaneFluxDict["r2"], "slope": methaneFluxDict["slope"]}})
        methaneSummary.append([idTag, methaneFluxDict["F_o"], methaneFluxDict["t_o"], methaneFluxDict["C_o"], methaneFluxDict["a"], methaneFluxDict["C_x"], methaneFluxDict["r2"], methaneFluxDict["slope"]])
        
        co2fluxDict = fluxes[1]
        co2summary.append([idTag, co2fluxDict["F_o"], co2fluxDict["t_o"], co2fluxDict["C_o"], co2fluxDict["a"], co2fluxDict["C_x"], co2fluxDict["r2"], co2fluxDict["slope"]])
        
        metadata.append([idTag, header["Area"], header["TotalVolume"],
                         header["Date"], header["Offset"]])
        timestamps = dataDictionary["timestamp"]
        concentrationDFs.append(pd.DataFrame({"idTag": len(timestamps)*[idTag], "time": timestamps, "ch4": dataDictionary["ch4"], "co2": dataDictionary["co2"]}))

fluxColumns = ["idTag", "F_o", "t_o", "C_o", "a", "C_x", "r2", "slope"]

metadataDF = pd.DataFrame(metadata, columns=["idTag", "soilArea", "totalVolume", "dateTime", "offset"])
metadataDF.dateTime = pd.to_datetime(metadataDF.dateTime)
methaneFluxDF = pd.DataFrame(methaneSummary, columns=fluxColumns)
co2fluxDF = pd.DataFrame(co2summary, columns=fluxColumns)
concentrations = pd.concat(concentrationDFs, ignore_index=True)
# %%
"""Assigning plot type, plot number, and collar to each observation"""

metadataDF.loc[metadataDF.idTag.str.contains(r"^ERCG"), "plotType"] = "Grove"
metadataDF.loc[metadataDF.idTag.str.contains(r"^TG"), "plotType"] = "Grass"
metadataDF.loc[metadataDF.idTag.str.contains(r"^ERCT"), "plotType"] = "Tree"
metadataDF.loc[metadataDF.idTag == "G17B", "plotType"] = "Grass"
metadataDF.loc[metadataDF.idTag == "T16A", "plotType"] = "Tree"
metadataDF["plotNumber"] = metadataDF.idTag.str.extract(r"^[A-Z]+([0-9]{1,2})")
metadataDF["collar"] = metadataDF.idTag.str.extract(r"^[A-Z]+[0-9]{1,2}([A-Z]{1})")
metadataDF.loc[metadataDF.idTag == "ERCT13_repB", "collar"] = "B"

if "plotType" not in co2fluxDF.columns.tolist():
    co2fluxDF = co2fluxDF.merge(metadataDF, on="idTag")
    methaneFluxDF = methaneFluxDF.merge(metadataDF, on="idTag")

    concentrations = concentrations.merge(metadataDF, on="idTag")

"""I extracted data for 43 observations when there should only have been 40
observations. Let's see why there are 3 extra observations.

So the plots we can collect fluxes for are

grass & tree 11, 15, 13, 16, and 17

grove 1, 2, 3, 4, 5

We're missing
- tree 15 (2 measurements)
- tree 11 collar B (1 measurement)

We have extra measurements of
- grass 13 collars A & C (2 measurements)
- tree 13, I'm assuming as collar B (1 measurement)
- tree 17, collar B (1 measurement)
- grove 5 collars B & C (2 measurements)

so missing 3 measurements & having 6 extra measurements
6 - 3 = 3 extra measurements

For grove 5 collars B & C, let's just keep the 1st measurement for each collar
since the 1st measurements have fairly high R2 values already, so they're
fairly good in quality. For tree 13 collar B, let's keep the 2nd measurement
because the 1st measurement has an extremely low R2 for both CO2 & methane.
For tree 17 collar B, I will also treat it like grove 5 collars B & C, keeping
the 1st measurement for the collar since the 1st measurement has a high enough
R2. Same thing with grass 13 collars A & C. So, of the plots & collars that
have 2 measurements, I will keep the 1st measurement for the following plots
& collars:
- grove 5 collar B
- grove 5 collar C
- tree 17 collar B
- grass 13 collar A
- grass 13 collar C

And for the following plot & collar, I will keep the 2nd measurement
- tree 13 collar B
"""
idTagsDrop = ["ERCG5BRep2", "ERCG5CRep2", "ERCT17Brep2", "TG13A_R2",
              "TG13C_R2", "ERCT13B"]
metadataDF = metadataDF.loc[~metadataDF.idTag.isin(idTagsDrop)]
co2fluxDF = co2fluxDF.loc[~co2fluxDF.idTag.isin(idTagsDrop)]
methaneFluxDF = methaneFluxDF.loc[~methaneFluxDF.idTag.isin(idTagsDrop)]
concentrations = concentrations.loc[~concentrations.idTag.isin(idTagsDrop)]

"""There are now 37 flux observations. For each observation, the smart chamber
& gas analyzer should have taken 120 data points of concentration vs time.
Therefore, there should be 37 * 120 = 4,440 data points of concentration vs
time in total. However, there are only 4,435. I'm trying to see why there's
this discrepancy."""
datapointsCount = (concentrations.groupby("idTag")["time"].count()
                   .reset_index()
                   .rename(columns={"time": "numberOfDatapoints"})
                   )
"""
So like for tree 5 collar B, there are only 115 data points. If you look
towards 100 - 110s, you'll see that some time points are skipped and not
collected by the smart chamber for some reason

I mean, not like it matters, right? There's no way that I would have known
in the field that a single flux measurement doesn't have enough data points.
If I take multiple measurements per collar to determine which measurement has
enough data points, then that would just be too time consuming. So, I don't
think this matters too much at this point."""
# %%
"""So I finished extracting the fluxes and the concentration data. I also
finished cleaning the data. In this chunk, I will compare the fluxes calculated
by the smart chamber vs the fluxes calculated by SoilFluxPro."""

# Reading in the fluxes calculated by SoilFluxPro
soilFluxProPath = october2026effluxFolder/"2026105_KAEFS_fromSoilFluxPro.csv"
soilFluxPro = pd.read_csv(soilFluxProPath, header=1)
soilFluxPro = soilFluxPro[3:]
soilFluxPro.FCO2_DRY = soilFluxPro.FCO2_DRY.astype("float")

# Assigning id tags, plot, and collar to each observation from SoilFLuxPro
soilFluxPro["DATE_TIME initial_value"] = pd.to_datetime(soilFluxPro["DATE_TIME initial_value"])
soilFluxPro = (soilFluxPro.merge(metadataDF, "inner", left_on="DATE_TIME initial_value", right_on="dateTime")
               .drop(columns=["DATE_TIME initial_value"])
               )

"""Now, I'm going to do a regression between the fluxes from the smart chamber
and from SoilFLuxPro"""
combinedCO2fluxes = soilFluxPro.merge(co2fluxDF, "inner", ["idTag", "dateTime", "plotType", "plotNumber", "collar", "soilArea", "totalVolume", "offset"])
CO2regression = scipy.stats.linregress(combinedCO2fluxes.F_o, combinedCO2fluxes.FCO2_DRY)
minCO2flux = co2fluxDF.F_o.min()
maxCO2flux = co2fluxDF.F_o.max()
minSoilFluxProCO2flux = (CO2regression.slope * minCO2flux) + CO2regression.intercept
maxSoilFluxProCO2flux = (CO2regression.slope * maxCO2flux) + CO2regression.intercept
CO2regressionFigure = plt.figure("SoilFluxPro vs smart chamber", (20, 20))
CO2regressionSubplot = CO2regressionFigure.add_subplot(111)
CO2regressionSubplot.set_xlabel("Smart chamber flux")
CO2regressionSubplot.set_ylabel("SoilFluxPro flux")
CO2regressionSubplot.grid()
CO2regressionScatter = CO2regressionSubplot.scatter(combinedCO2fluxes.F_o, combinedCO2fluxes.FCO2_DRY, label="Data")
CO2regressionLine = CO2regressionSubplot.plot([minCO2flux, maxCO2flux], [minSoilFluxProCO2flux, maxSoilFluxProCO2flux], label="Regression of the data")
max1to1 = (1 * maxCO2flux) + 0
oneToOneLine = CO2regressionSubplot.plot([minCO2flux, maxCO2flux], [minCO2flux, max1to1], label="1:1 relationship")
CO2regressionSubplot.legend()

"""Fluxes from SoilFLuxPro is very, very slightly higher than the fluxes from
the smart chamber. But the difference between the 2 is so tiny that it
practically doesn't matter."""

"""Ok let's export the CO2 and methane fluxes for October 5, 2026. I'll just
export it as an Excel file."""
fluxes20261005 = (co2fluxDF.filter(["idTag", "plotType", "plotNumber", "collar", "F_o", "r2", "soilArea", "offset"])
                  .rename(columns={"F_o": "CO2flux", "r2": "CO2flux_Rsquared"})
                  .merge(methaneFluxDF, "inner", ["idTag", "plotType", "plotNumber", "collar", "soilArea", "offset"])
                  .rename(columns={"F_o": "methaneFlux", "r2": "methaneFlux_Rsquared"})
                  .filter(["idTag", "dateTime", "soilArea", "offset", "plotType", "plotNumber", "collar", "CO2flux", "CO2flux_Rsquared", "methaneFlux", "methaneFlux_Rsquared"])
                  )
# %%
# Exporting the flux data from October 5, 2026
cleanFolder = october2026effluxFolder/"Clean"
fluxes20261005path = cleanFolder/"October 5, 2026 fluxes.xlsx"

note1 = ["This Excel file contains methane and CO2 efflux data taken on",
         "October 5, 2026 after I cleaned them. The raw dataset contained 46",
         "flux measurements that I've narrowed down to 37 measurements for",
         "a total of 37 collars, with each collar having 1 measurement.",
         "Each tree has 2 collars and each grass plot and grove has 3",
         "collars. There are 5 grasses (11, 13, 15, 16, 17), 5 trees",
         "(same plot numbers as the grasses), and 5 groves (1, 2, 3, 4, 5).",
         "There are a total of 15 collars in grass plots, 10 collars in trees",
         "and 15 collars in groves, leading to a total of 40 collars and a",
         "maximum of 40 observations in this dataset. Since I narrowed it down",
         "to 37 measurements, there are 3 collars that were not measured.",
         "Tree 15 was not measured at all while grass 11 did not get its",
         "collar B measured.",
         "",
         "I imported the json file that contained the data into Python and",
         "cleaned the data. I believe that the data is sufficiently cleaned",
         "now, and the cleaned data is in the tab 'Data'. The tab contains",
         "both CO2 and methane fluxes for each of the 37 collars, and",
         "associated with each flux is an R-squared value that the smart",
         "chamber calculated. The CO2 fluxes all have R-squared > 0.99 with",
         "the exception of grass 15 collar C (R-squared > 0.98). Methane",
         "fluxes have a lower R-squared, > 0.96 for all except for grove 2",
         "collar A (0.66) and collar C (0.73). This is likely because the",
         "flux is so close to 0. I could not improve their R-squared when I",
         "tried adjusting these 2 flux values on SoilFluxPro, likely because",
         "of the fluxes being so close to 0.",
         "",
         "Fluxes for both CO2 and methane have units of micromole per square",
         "meter per second. Soil area is in centimeter square while offset",
         "is in centimeter. For each observation, I included its ID tag",
         "(the name you assign each observation prior to starting measurement)",
         "and the date and time when the measurement was taken. The smart",
         "chamber automatically records the date, time, and GPS location of",
         "each observation."]
readMe1 = []
for line in note1:
    readMe1.append([line])

"""I was going to use pandas ExcelWriter but it seems like this was broken ever
since pandas upgraded from major version 1 to 2 (this version is 3.0.5). So I'm
just going to export the data using openpyxl"""
if os.path.exists(fluxes20261005path) is False:
    fluxes20261015file = openpyxl.Workbook()
    readMeTab = fluxes20261015file.active
    readMeTab.title = "ReadMe"
    for line in readMe1:
        readMeTab.append(line)

    dataTab = fluxes20261015file.create_sheet("Data")

    fluxes20261005columns = fluxes20261005.columns.tolist()
    dataTab.append(fluxes20261005columns)

    fluxes20261005valuesList = fluxes20261005.to_numpy().tolist()
    for row in fluxes20261005valuesList:
        dataTab.append(row)

    fluxes20261015file.save(fluxes20261005path)
# %%
"""And now, I'm going to clean the flux data for October 12. This new dataset
should be much more straightforward since we took all 40 measurements with no
repeated measurement for a single collar."""

"""Reading in the json file. Not parsing it yet"""
october12path = october2026effluxFolder/"kaefs261012.json"
october12file = open(october12path, "r")
october12json = json.load(october12file)
october12file.close()

# Parsing the json file
october12datasets = october12json["datasets"]
october12datasets = october12datasets[1:]  
# Removed the 1st observation because this observation was taken at SRTC
metadata = []
co2flux = []
for observation in october12datasets:
    idTag = list(observation.keys())[0]
    observationLowerLevel = observation[idTag]
    repsDictionary = observationLowerLevel["reps"]
    rep1dictionary = repsDictionary["REP_1"]
    
    # Noting down the metadata for each observation like id tag, collar offset, etc,.
    header = rep1dictionary["header"]
    metadata.append([idTag, header["Date"], header["Offset"], header["Area"]])

    """Noting down the flux values that the smart chamber calculated. The gas
    analyzer used for this dataset for October 12 was the licor-870 which only
    recorded CO2, not methane, so only recording CO2 values here"""
    footer = rep1dictionary["footer"]
    fluxes = footer["fluxes"]
    co2fluxMeasurement = fluxes[0]
    co2flux.append([idTag, co2fluxMeasurement["F_o"], co2fluxMeasurement["r2"]])

metadataDF = pd.DataFrame(metadata, columns=["idTag", "dateTime", "offset", "soilArea"])
co2fluxDF = pd.DataFrame(co2flux, columns=["idTag", "CO2flux", "CO2flux_Rsquared"])

"""I am curious as to the relationship between the magnitude of the flux and
its R-squared value. Gonna do a regression to test that out now"""
fluxRsquared = scipy.stats.linregress(co2fluxDF.CO2flux, co2fluxDF.CO2flux_Rsquared)
"""So there's a bit of a positive correlation between the magnitude of a flux
and its R-squared value. The bigger the flux, the better its R-squared value"""

metadataDF["plotType"] = metadataDF.idTag.str.extract(r"^([a-zA-Z]+)")
metadataDF["plotNumber"] = metadataDF.idTag.str.extract(r"[a-zA-Z]+([0-9]{1,2})")
metadataDF["collar"] = metadataDF.idTag.str.extract(r"[a-zA-Z]+[0-9]{1,2}([a-zA-Z])")
metadataDF.loc[metadataDF.collar == metadataDF.collar.str.lower(), "collar"] = metadataDF.collar.str.upper()

co2fluxDF = co2fluxDF.merge(metadataDF, "inner", "idTag")
# %%
# Exporting the flux data for October 12
note2 = [["The flux data for October 12 was taken with the licor-870. There were"],
         ["connectivity issues between the licor-7810 and the smart chamber"],
         ["such that we could not select the gas analyzer when setting up"],
         ["the flux measurement process on the tablet. This was later"],
         ["troubleshot by Jani and I back in the processing lab as a faulty"],
         ["Ethernet cable. Thus, we switched to the 870 instead. The 870"],
         ["can only measure CO2 and so this dataset only included CO2 fluxes."],
         [""],
         ["We successfully measured all 40 collars with no repeated measurements"],
         ["at any collars. The 2 measurements with the lowest R-squared"],
         ["are tree 11 collar B (0.914) and grove 5 collar C (0.953). Similar"],
         ["to the methane fluxes taken on October 5, these lower R-squared"],
         ["values might be due to the relatively low magnitude of the flux values."],
         ["I computed a linear regression between the flux values and their"],
         ["respective R-squared values and found that there's a positive"],
         ["correlation between the 2, and the R-squared of this linear"],
         ["regression is 0.338. This seems to indicate that the higher the"],
         ["magnitude of the flux (whether a positive or negative flux), the"],
         ["higher the R-squared of the flux, and the lower the magnitude of"],
         ["the flux, the lower the R-squared."],
         [""],
         ["Once again, the fluxes are in units of micromole per square meter"],
         ["per second."]]

fluxes20261012path = cleanFolder/"October 12, 2026 fluxes.xlsx"
if os.path.exists(fluxes20261012path) is False:
    file = openpyxl.Workbook()
    readMe = file.active
    readMe.title = "ReadMe"
    for line in note2:
        readMe.append(line)
    dataTab = file.create_sheet("Data")
    dataTab.append(co2fluxDF.columns.tolist())
    co2fluxList = co2fluxDF.to_numpy().tolist()
    for row in co2fluxList:
        dataTab.append(row)
    file.save(fluxes20261012path)
