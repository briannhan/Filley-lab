# -*- coding: utf-8 -*-
"""
Created on Mon Nov  9 15:47:51 2026

@author: brian

This script cleans the flux data we measured on November 9, 2026. Things went
very smoothly that day for the most part, we only redid measurements twice,
once for grass 15 collar C and then a second time for a grass collar in grass
either 16 or 17.
"""
import os
from pathlib import Path
import pandas as pd
import json
import effluxCleaning as ec

cwd = Path(os.getcwd())
repository = Path(os.path.dirname(cwd))
dataFolder = repository/"Data"
inputFolder = dataFolder/"Input"
effluxDataFolder = inputFolder/"Soil gas efflux"
novemberFolder = effluxDataFolder/"2026"/"November"
cleanFolder = novemberFolder/"Clean"

novemberJsonPath = novemberFolder/"20261109_KAEFS.json"
j = open(novemberJsonPath, "r")
november9dict = json.load(j)
j.close()
# %%
november9 = ec.extractData(november9dict)
november9metadata = november9["metadata"]
november9data = november9["data"]
november9metadata = ec.plotAndCollar(november9metadata)

"""For grass 15 collar C, I'll drop the measurement with the ID tag of
Grass15C and keep the one with Grass15C_1 since Grass15C, the concentration was
rising a little too slowly so I was wondering if there was a leak. In the field,
we saw that there were some grass blades stuck between the smart chamber and
the top of the collar, and that might have led to the flux being a bit too low
even though the R2 is quite good.

For grass 17 collar b, I'll drop the measurement with the ID tag Grass17b and
keep the one called Grass17b2 since the 7810 dropped onto its side while
measuring Grass17b, producing some really weird concentrations.
"""

november9metadata = november9metadata.loc[~november9metadata.idTag.isin(["Grass15C", "Grass17b"])]
november9data = november9data.merge(november9metadata, "inner", "idTag")
# %%
# Exporting the data

n = [["This is cleaned flux data measured on November 9, 2026. Things went"],
     ["smoothly for the most part. We had to redo measurements for grass 15"],
     ["collar C and grass 17 collar B. While doing the 1st measurement for"],
     ["grass 15 collar C, the concentration seemed like it was rising fairly"],
     ["slowly to me, so we checked under the smart chamber and removed some"],
     ["grass blades between the collar rim and the smart chamber. We redid"],
     ["grass 15 collar C once, resulting in the idTag Grass15C_1. And while"],
     ["measuring flux for grass 17 collar B,"],
     ["the 7810 fell on its side, resulting in some wonky concentration readings."],
     ["After waiting for a couple minutes after the smart chamber stopped measuring"],
     ["and checking the concentration readings on the 7810, we started measuring"],
     ["this collar again, resulting in Grass17b2. I removed the 2 initial"],
     ["measurements for grass 15 collar C and grass 17 collar B and kept the 2"],
     ["final ones. This final dataset has 40 measurements, 1 for each collar."],
     ["Every collar was measured."],
     [""]
     ]
n.extend(ec.unitsMetadata1)
exportPath = cleanFolder/"November 9, 2026 fluxes.xlsx"
ec.exportCleanData(exportPath, november9data, n)
