# -*- coding: utf-8 -*-
"""
Created on Mon Oct 26 23:47:52 2026

@author: brian

This script cleans the flux measurement data at Kessler taken on Monday October
26, 2026. Measurements were made using the 7810, which I've successfully
mastered this time. I've finally figured out how to work the Ethernet port on
the machine.
"""
import os
from pathlib import Path
import pandas as pd
import openpyxl
import effluxCleaning
import json

cwd = Path(os.getcwd())
repository = Path(os.path.dirname(cwd))
octoberFolder = repository/"Data"/"Input"/"Soil gas efflux"/"2026"/"October"
october26path = octoberFolder/"20261026_KAEFS.json"
october26file = open(october26path, "r")
october26dict = json.load(october26file)
october26file.close()
october26metadata, october26data = effluxCleaning.extractData(october26dict)
# %%
october26metadata["plotType"] = october26metadata.idTag.str.extract(r"^([a-zA-Z]+)")
october26metadata["plotNumber"] = october26metadata.idTag.str.extract(r"^[a-zA-Z]+([0-9]{1,2})")
october26metadata["collar"] = october26metadata.idTag.str.extract(r"^[a-zA-Z]+[0-9]{1,2}([A-Z])")

"""There was some discussion between Adam and I on what the internal diameter
for some of the collars should be. I'm inclined to trust the internal diameters
from October 19 rather than on this date. I'll change internal diameters to
the values from October 19. This requires changing internal diameters (and soil
area) for the following

- Tree 16 collar B, from 19.5 cm (on the 26th) to 20 cm (on the 19th)
- Tree 13 collar B, from 19.5 cm (on the 26th) to 20 cm (on the 19th)
- Tree 15 collars A and B, from 20 cm (on the 26th) to 19.5 cm (on the 19th)
- Tree 11 collar A, from 20 cm (on the 26th) to 19.5 cm (on the 19th)
- Grove 5 collar C, from 20 cm (on the 26th) to 19.5 cm (on the 19th)

I will also need to update offset values as well. I've recalculated 2 offset
values from Zack (grove 1 collar B and grove 3 collar B) and I will need to
update them here
- Grove 3 collar B, update to 5.075 cm
- Grove 1 collar B, update to 4.1 cm
"""
october26metadata.loc[october26metadata.idTag.str.contains(r"^Tree1[36]B"), "soilArea"] = 314.16
october26metadata.loc[october26metadata.idTag.str.contains(r"^(Tree1(1A|5)|Grove5C)"), "soilArea"] = 298.65
october26metadata.loc[october26metadata.idTag == "Grove3B", "offset"] = 5.075
october26metadata.loc[october26metadata.idTag == "Grove1B", "offset"] = 4.1
october26data = october26data.merge(october26metadata, "inner", "idTag")
# %%

# Recalculating fluxes for 8 collars
october26recalc = october26data.loc[october26data.idTag.str.contains(r"^(Tree1([36]B|5|1A)|Grove(5C|[13]B))")]
october26recalc = effluxCleaning.recalculateVolume(october26recalc)
october26recalc = effluxCleaning.recalculateFlux(october26recalc, "CO2")
october26recalc = effluxCleaning.recalculateFlux(october26recalc, "methane")
october26good = october26data.loc[~october26data.idTag.str.contains(r"^(Tree1([36]B|5|1A)|Grove(5C|[13]B))")]

october26final = pd.concat([october26good, october26recalc], ignore_index=True)
# %%
# Exporting the data
note = [["This Excel file contains the flux data collected on Monday October"],
        ["26, 2026. I was able to use the 7810 after reverting to the black"],
        ["Ethernet cable, plugging the cable into the 7810 tightly, and"],
        ["visually checking the connection to see if it's plugged in tightly."],
        ["So this dataset has CO2 and methane flux values. This dataset uses"],
        ["collar offset values and diameters measured on October 19; we did"],
        ["not measure new offset values for the 26th."],
        [""],
        ["I recalculated fluxes for a total of 8 collars. I recalculated"],
        ["fluxes for 2 collars (collar B in groves 1 & 3) because the mean"],
        ["offset calculated in the field on the 19th was slightly wrong."],
        ["I also recalculated fluxes for an additional 6 collars. We initially"],
        ["believed that collars under a single tree consistently have the same"],
        ["internal diameter and collars under groves should be the same."],
        ["Furthermore, I did not check internal diameters for collars under"],
        ["trees 11 & 15 and so used 20 cm for them in the field. These led to"],
        ["discrepancies with collar diameters on the 19th. I decided to use"],
        ["collar diameters on the 19th because they were actually measured on"],
        ["that date. This led to me changing diameters for 6 collars, resulting"],
        ["in a total of 8 collars whose fluxes needed to be recalculated."],
        [""],
        ["Collars whose fluxes I recalculated due to discrepancies in offsets"],
        ["were"],
        ["- Grove 3 collar B"],
        ["- Grove 1 collar B"],
        [""],
        ["Collars whose fluxes I recalculated due to discrepancies in internal"],
        ["diameters were"],
        ["- Tree 16 collar B"],
        ["- Tree 13 collar B"],
        ["- Tree 15 collar A"],
        ["- Tree 15 collar B"],
        ["- Tree 11 collar A"],
        ["- Grove 5 collar C"],
        [""],
        ["Units:"],
        ["- CO2 flux: micromole CO2 per square meter per second"],
        ["- methane flux: nanomole CH4 per square meter per second"],
        ["- soil area: centimeter square"],
        ["- offset: centimeter"],
        ["- volumes (chamber, gas analyzer, and total): centimeter cube"],
        ["- Initial pressure (P_o): kPa"],
        ["- Initial temperature (T_o): Celsius"],
        ["- Initial water vapor mole fraction (W_o): mmol H2O/mol air"]]
exportPath = octoberFolder/"Clean"/"October 26, 2026 fluxes.xlsx"
if os.path.exists(exportPath) is False:
    wb = openpyxl.Workbook()
    readMe = wb.active
    readMe.title = "ReadMe"
    for line in note:
        readMe.append(line)
    dataTab = wb.create_sheet("Data")
    dataTab.append(october26final.columns.tolist())
    october26list = october26final.to_numpy().tolist()
    for line in october26list:
        dataTab.append(line)
    wb.save(exportPath)
