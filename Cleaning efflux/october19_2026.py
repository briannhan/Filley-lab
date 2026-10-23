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
