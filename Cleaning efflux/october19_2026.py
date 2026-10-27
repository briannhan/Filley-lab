# -*- coding: utf-8 -*-
"""
Created on Fri Oct 23 00:03:43 2026

@author: brian

This script cleans efflux data collected on Monday October 19, 2026. The efflux
data consists of (1) normal efflux measurements at all 40 collars and (2)
efflux measurements made as part of a litter experiment.
"""
import os
from pathlib import Path
import json
import pandas as pd
import openpyxl
import effluxCleaning

cwd = Path(os.getcwd())
repository = Path(os.path.dirname(cwd))
dataFolder = repository/"Data"
inputFolder = dataFolder/"Input"
effluxFolder = inputFolder/"Soil gas efflux"
october2026folder = effluxFolder/"2026"/"October"
october19path = october2026folder/"20261019_KAEFS.json"
october19file = open(october19path, "r")
october19json = json.load(october19file)
october19file.close()
# %%
october19metadata, october19fluxes = effluxCleaning.extractData(october19json)
october19metadata.loc[october19metadata.idTag.str.contains(r"^Grass"), "plotType"] = "Grass"
october19metadata.loc[october19metadata.idTag.str.contains(r"^Grove"), "plotType"] = "Grove"
october19metadata.loc[october19metadata.idTag.str.contains(r"^(TREE|Tree)"), "plotType"] = "Tree"
october19metadata["plotNumber"] = october19metadata.idTag.str.extract(r"^[a-zA-Z]+([0-9]{1,2})")
october19metadata["collar"] = october19metadata.idTag.str.extract(r"^[a-zA-Z]+[0-9]{1,2}([a-zA-Z])")

"""Gonna separate the data for the litter experiment as well as normal flux
measurements"""
october19metadataNormal = october19metadata.loc[october19metadata.collar.notna()]
october19metadataNormal.loc[october19metadataNormal.idTag == "Grass15B", "collar"] = "C"
idTagsDrop = ["Grass17A"]
october19metadataNormal = october19metadataNormal.query("idTag != @idTagsDrop")
october19normal = october19fluxes.merge(october19metadataNormal, "inner", "idTag")
october19metadataLitterExperiment = october19metadata.query("plotType == 'Grove'")
october19metadataLitterExperiment.loc[october19metadataLitterExperiment.idTag.str.contains("litter1?$"), "collar"] = "litter 1"
october19metadataLitterExperiment.loc[october19metadataLitterExperiment.idTag.str.contains("litter2$"), "collar"] = "litter 2"
october19metadataLitterExperiment.loc[october19metadataLitterExperiment.idTag.str.contains("litter3$"), "collar"] = "litter 3"

october19metadataLitterExperiment.loc[october19metadataLitterExperiment.idTag.str.contains(r"rep[0-9]$"), "collar"] = "litter 1 rep " + october19metadataLitterExperiment.idTag.str[-1]
october19metadataLitterExperiment.loc[october19metadataLitterExperiment.idTag == "Grove1_emptyTrayCollar", "collar"] = "empty dummy collar"
october19litterExperiment = october19fluxes.merge(october19metadataLitterExperiment, "inner", "idTag")
# %%
"""I'm going to recalculate some fluxes now. For the normal fluxes, I want to
recalculate the flux values for grove 1 collar B, grass 15 collar C,
and grove 3 collar B. For grass 15 collar C, I accidentally used the collar
offset for B when I should have used the value for C. For grove 1 collar B and
grove 3 collar B, the mean offset that Zack calculated in the field seemed to
have been wrong compared to what I calculated afterwards
"""
october19normalRecalculate = october19normal.loc[october19normal.idTag.str.contains(r"^(Grove[13]B|Grass15B$)")]
october19normalRecalculate.loc[october19normalRecalculate.plotNumber == "15", "offset"] = 4.075
october19normalRecalculate.loc[october19normalRecalculate.plotNumber == "1", "offset"] = 4.1
october19normalRecalculate.loc[october19normalRecalculate.plotNumber == "1", "offset"] = 5.075
october19normalRecalculate = effluxCleaning.recalculateVolume(october19normalRecalculate)
october19normalRecalculate = effluxCleaning.recalculateFlux(october19normalRecalculate, "CO2")

october19normal = october19normal.loc[~october19normal.idTag.str.contains(r"^(Grove[13]B|Grass15B$)")]
october19normal = pd.concat([october19normal, october19normalRecalculate], ignore_index=True)
# %%
"""Let's just export the normal dataset sans the litter experiment."""
exportPath = october2026folder/"Clean"/"October 19, 2026 fluxes.xlsx"
note = [["This file contains the flux data collected on Monday October 19,"],
        ["2026. The data collected on this day included both normal flux"],
        ["measurements as well as measurements taken as part of Tim's ad-hoc"],
        ["litter experiment measuring fluxes from just litter. As of October"],
        ["26, 2026, this Excel file only contains the normal flux measurements."],
        [""],
        ["I recalculated fluxes for grove 1 collar B, grove 3 collar B, and"],
        ["grass 15 collar C. For grass 15 collar C, the measurement was"],
        ["physically taken at collar C but I mislabelled the observation as"],
        ["though I was at collar B instead and, as a result, I used the"],
        ["offset for collar B. For grove 1 collar B and grove 3 collar B,"],
        ["the mean offsets for these 2 collars as calculated in the field were"],
        ["slightly inaccurate and were different from when I calculated them"],
        ["afterwards. The person doing the measuring might have mistyped some"],
        ["numbers when doing the mean calculations. I only recalculated CO2 flux"],
        ["for these 3 collars since we only used the 870 gas analyzer on this"],
        ["date which could only measure CO2. The data are in the 'Data' tab."],
        [""],
        ["CO2 flux is in units of micromole CO2 per square meter per second."],
        ["Collar offset is in centimeters, soil area is in centimeters square,"],
        ["and the 3 volumes (chamberVolume, gasAnalyzerVolume, and totalVolume)"],
        ["are in cubic centimeters. totalVolume is calculated as the sum of"],
        ["the chamber volume, the gas analyzer volume, and the product of"],
        ["soil area and collar offset. The slope for the flux is in units of"],
        ["micromole CO2 per mole dry air per second. The smart chamber also"],
        ["produced values at the beginning after chamber closure, ending in"],
        ["an underscore and the letter o. Initial chamber pressur (P_o) are"],
        ["in kPa, initial temperature (T_o) are in Celsius, and the initial"],
        ["fraction of water vapor in air (W_o) is in mmol water vapor per"],
        ["mole of air."]]
if os.path.exists(exportPath) is False:
    wb = openpyxl.Workbook()
    readMe = wb.active
    readMe.title = "ReadMe"
    for line in note:
        readMe.append(line)
    dataTab = wb.create_sheet("Data")
    dataTab.append(october19normal.columns.tolist())
    october19list = october19normal.to_numpy().tolist()
    for line in october19list:
        dataTab.append(line)
    wb.save(exportPath)
