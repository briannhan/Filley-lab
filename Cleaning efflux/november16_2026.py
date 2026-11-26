# -*- coding: utf-8 -*-
"""
Created on Wed Nov 25 15:42:51 2026

@author: brian

This script cleans flux data measured on Monday November 16, 2026.
"""
import effluxCleaning as ec
import pandas as pd
from pathlib import Path
import os
import json
from openpyxl import Workbook

cwd = Path(os.getcwd())
repository = Path(os.path.dirname(cwd))
dataFolder = repository/"Data"
november2026effluxFolder = dataFolder/"Input"/"Soil gas efflux"/"2026"/"November"
november16path = november2026effluxFolder/"20261116_Kessler.json"
november16file = open(november16path, "r")
november16raw = json.load(november16file)
november16file.close()
# %%
november16extracted = ec.extractData(november16raw)
november16data = november16extracted["data"].query("methaneFlux.notna() & CO2flux_Rsquared > 0")
november16metadata = november16extracted["metadata"]
november16data = november16data.merge(november16metadata, "inner", "idTag")
november16data = ec.plotAndCollar(november16data)
# %%
n = [["These are flux measurements taken on Monday November 16, 2026 using"],
     ["the 7810, and so both methane and CO2 fluxes are recorded. CO2 fluxes"],
     ["were incredibly low in grasses, so we measured grass 17 collar B with"],
     ["the 7810 and then again with the 870. CO2 fluxes from both instruments"],
     ["were low, so the low fluxes didn't appear to be an instrumentation"],
     ["problem but moreso because actual fluxes were low. It rained a bit on"],
     ["Saturday November 14 and then it rained about 1 in on Sunday November 15."],
     ["Soils were still waterlogged from the rains over the weekend, likely"],
     ["explaining the low fluxes."],
     [""]
     ]
n.extend(ec.unitsMetadata1)
cleanFolder = november2026effluxFolder/"Clean"
exportPath = cleanFolder/"November 16, 2026 fluxes.xlsx"
if os.path.exists(exportPath) is False:
    wb = Workbook()
    readMe = wb.active
    readMe.title = "ReadMe"
    for line in n:
        readMe.append(line)
    dataTab = wb.create_sheet("Data")
    dataTab.append(november16data.columns.tolist())
    november16dataOnly = november16data.to_numpy().tolist()
    for line in november16dataOnly:
        dataTab.append(line)
    wb.save(exportPath)
