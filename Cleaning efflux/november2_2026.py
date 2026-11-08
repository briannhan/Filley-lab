# -*- coding: utf-8 -*-
"""
Created on Sat Nov  7 17:50:34 2026

@author: brian

This script cleans the soil efflux data that was taken on Monday November 2,
2026. We used the 7810 in the field that day, although we had technical issues
with the Ethernet connection. Some measurements in grove 2 read exactly 0 flux
(0.000 micromole CO2 per square meter per second, same thing with methane).
Furthermore, the gas tubing inadvertently became loose during transport from
the North plots to the South plots, so our initial measurements for Grass 16 &
17 should be dropped.
"""
import os
from pathlib import Path
import pandas as pd
import effluxCleaning as ec
import json
import openpyxl

cwd = Path(os.getcwd())
repository = Path(os.path.dirname(cwd))
dataFolder = repository/"Data"
inputFolder = dataFolder/"Input"
novemberFolder = inputFolder/"Soil gas efflux"/"2026"/"November"
november2jsonPath = novemberFolder/"20261102_KAEFS.json"
with open(november2jsonPath, "r") as j:
    november2json = json.load(j)
# %%
november2 = ec.extractData(november2json)
november2metadata = november2[0]
november2metadata["dateTime"] = pd.to_datetime(november2metadata["dateTime"])
november2data = november2[1]
november2metadata["plotType"] = november2metadata.idTag.str.extract(r"^([a-zA-Z]+)")
november2metadata["plotNumber"] = november2metadata.idTag.str.extract(r"^[a-zA-Z]+([0-9]{1,2})")
november2metadata["collar"] = november2metadata.idTag.str.extract(r"^[a-zA-Z]+[0-9]{1,2}([a-zA-Z])")
november2data = november2data.merge(november2metadata, "inner", "idTag")

"""The following ID tags have fluxes of exactly 0

- Grass 11, collar B
- Grove 2, collar A
- Grove 2, collar C

I didn't notice that grass 11 collar B had this error in the field so I only
took a single flux measurement for this collar, so I don't have another good
measurement of this collar that I can use instead.

Grove 2 collars A and C had this same issue but I caught them, fixed the
Ethernet connection, and redid them.
"""
november2data = november2data.query("CO2flux != 0")

"""On the Southern plots, we had issues in which CO2 concentration just wasn't
changing that we diagnosed at ~12:50 PM to be due to the tubing not being
attached on tight enough. Until then, the measurements on the southern plots
are incredibly suspect, so the measurements that were taken between 12:06:41 PM
(grass 16 collar C) and 12:47:07 PM (tree 17 collar A, the 1st redo attempt)
must be discarded."""
grass16Ctime = november2data.loc[november2data.idTag == "Grass16C", "dateTime"].tolist()[0]
tree17Aredo1time = november2data.loc[november2data.idTag == "Tree17A_redo", "dateTime"].tolist()[0]
november2data = november2data.loc[(november2data.dateTime < grass16Ctime) | (november2data.dateTime > tree17Aredo1time)]
# %%
# Exporting the data
n = [["This is cleaned soil efflux data that was collected on Monday November 2, 2026."],
     ["We exclusively used the 7810 this day, so we for each collar, we have both"],
     ["CO2 flux and methane flux. We had 3 types of technical issues:"],
     [""],
     ["1. Ethernet connection connection was lost between"],
     ["the 7810 and the smart chamber despite the 2 of them being physically"],
     ["connected"],
     ["2. concentration being mysteriously shown as constant"],
     ["on the tablet controlling the smart chamber, leading to fluxes being"],
     ["measured as 0.000"],
     ["2. The ends of the gas tubings that are attached to the 7810 were loose,"],
     ["leading to leakage and the CO2 concentration readings on the tablet"],
     ["fluctuating around atmospheric concentrations."],
     [""],
     ["Whenever Ethernet connection was lost, we would unplug and replug both"],
     ["ends of the Ethernet cable and select the gas analyzer again on the"],
     ["tablet controlling the smart chamber. This specific Ethernet issue"],
     ["did not cause us to lose any measurements but, rather, it made the"],
     ["overall flux measurement process take more time than I intended. Now,"],
     ["regarding CO2 concentration being shown as not changing at all, I'm"],
     ["not entirely sure if this was because of an issue with the Ethernet"],
     ["connection or something else. This first happened with grass 11 collar B"],
     ["and I didn't catch it so I didn't redo the measurement for this collar,"],
     ["so I removed this collar in the cleaning process. This also happened"],
     ["with all collars in grove 2, but I caught it then and fixed it the"],
     ["same way I fixed the Ethernet connection being lost (unplugging and"],
     ["replugging both ends of the Ethernet cable). We were able to get good"],
     ["measurements for all collars in grove 2 because of that."],
     [""],
     ["When we were initially doing fluxes on the south side, we noticed that"],
     ["CO2 concentrations would hover around atmospheric concentrations."],
     ["This was despite us checking thoroughly when placing the smart chamber"],
     ["on the collars in the grass plots for grass blades that were on the"],
     ["collar rim that could have prevented a seal between the smart chamber"],
     ["and the collar. We finally diagnosed the issue to be the gas tubing ends"],
     ["on the 7810 being loose. Since we didn't have this issue on the north"],
     ["side, the tubing likely came loose during transport to the south side."],
     ["We tightened the gas tubing ends and were able to get good measurements"],
     ["for all collars on the south side. In total, we got good measurements"],
     ["for 39 out of the 40 collars in the field."],
     [""],
     ["Units for the fields are the following"],
     ["- CO2flux: micromole CO2 per square cm per s"],
     ["- CO2fluxSlope: CO2 concentration in dry air (ppm) per s"],
     ["- methaneFlux: nanomole CO2 per square cm per s"],
     ["- methaneFluxSlope: methane concentration in dry air (ppb) per s"],
     ["- soilArea: square cm"],
     ["- offset: cm"],
     ["- volumes (chamber, gas analyzer, and total): cm cubed"],
     ["- initial chamber pressure (P_o): kPa"],
     ["- initial air temperature (T_o): Celsius"],
     ["- initial water vapor fraction in air (W_o): mmol water vapor per mol air"],
     ["- date and time when each measurement started: date followed by time,"],
     ["written as yyyy-mm-dd hh:mm:ss"]
     ]

cleanFolder = novemberFolder/"Clean"
filePath = cleanFolder/"November 2, 2026 fluxes.xlsx"
if os.path.exists(filePath) is False:
    wb = openpyxl.Workbook()
    readMe = wb.active
    readMe.title = "ReadMe"
    for line in n:
        readMe.append(line)
    data = wb.create_sheet("Data")
    data.append(november2data.columns.tolist())
    november2dataList = november2data.to_numpy().tolist()
    for line in november2dataList:
        data.append(line)
    wb.save(filePath)
