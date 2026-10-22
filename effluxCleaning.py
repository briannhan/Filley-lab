# -*- coding: utf-8 -*-
"""
Created on Wed Oct 21 23:17:56 2026

@author: brian

This module contains functions for cleaning the raw efflux data. This module
will be imported into other scripts meant for cleaning specific efflux
datasets. The efflux datasets will be gathered using a Licor smart chamber and
a Licor gas analyzer, either a 7810 (which measures fluxes for both CO2 &
methane) or an 870 (which only measures CO2 flux)
"""
import pandas as pd


def extractData(jsonDictionary):
    """
    This function takes a dictionary that was created from the json file
    containing a dataset and then extracts data and metadata from the
    dictionary. This function is assuming that there are no erroneous
    observations that did not have their fluxes calculated.

    Parameters
    ----------
    jsonDictionary : dictionary
        A dictionary created from the json file that contains a flux dataset
        from a specific date.

    Returns
    -------
    A dataframe containing the metadata and a dataframe containing either only
    CO2 flux data (if the data was collected by an 870) or both CO2 and methane
    fluxes (if the data was collected by a 7810)
    """
    dataset = jsonDictionary["datasets"]
    metadata = []
    co2fluxData = []
    methaneFluxData = []
    for observation in dataset:
        idTag = list(observation.keys())[0]
        observationLowerLevel = observation[idTag]
        remark = observationLowerLevel["remark"]
        reps = observationLowerLevel["reps"]
        rep1 = reps["REP_1"]
        header = rep1["header"]
        gasAnalyzer = header["InstrumentModel"]
        
        # Extracting metadata
        metadata.append([idTag, remark, gasAnalyzer, header["Area"], header["Offset"], header["ChamVolume"], header["IrgaVolume"], header["TotalVolume"], header["Date"]])

        # Extracting flux data
        footer = rep1["footer"]
        fluxes = footer["fluxes"]
        if gasAnalyzer.endswith("870"):
            co2flux = fluxes[0]
        elif gasAnalyzer.endswith("7810"):
            methaneFlux = fluxes[0]
            if methaneFlux["name"] == "ch4":
                methaneFluxData.append([idTag, methaneFlux["F_o"], methaneFlux["slope"], methaneFlux["r2"]])
            co2flux = fluxes[1]
        co2fluxData.append([idTag, co2flux["F_o"], co2flux["slope"], co2flux["r2"]])
    metadataColumns = ["idTag", "remark", "gasAnalyzer", "soilArea", "offset",
                       "chamberVolume", "gasAnalyzerVolume", "totalVolume",
                       "dateTime"]
    metadataDF = pd.DataFrame(metadata, columns=metadataColumns)

    co2fluxColumns = ["idTag", "CO2flux", "CO2fluxSlope", "CO2flux_Rsquared"]
    co2fluxDF = pd.DataFrame(co2fluxData, columns=co2fluxColumns)
    
    methaneFluxColumns = ["idTag", "methaneFlux", "methaneFluxSlope",
                          "methaneFlux_Rsquared"]
    if len(methaneFluxData) > 0:
        methaneFluxDF = pd.DataFrame(methaneFluxData, columns=methaneFluxColumns)
        co2fluxDF = co2fluxDF.merge(methaneFluxDF, "outer", "idTag")
    return metadataDF, co2fluxDF
