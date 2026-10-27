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
        footer = rep1["footer"]
        
        # Extracting metadata
        metadata.append([idTag, remark, gasAnalyzer, header["Area"], header["Offset"], header["ChamVolume"], header["IrgaVolume"], header["TotalVolume"], header["Date"], footer["P_o"], footer["T_o"], footer["W_o"]])

        # Extracting flux data
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
                       "dateTime", "P_o", "T_o", "W_o"]
    metadataDF = pd.DataFrame(metadata, columns=metadataColumns)

    co2fluxColumns = ["idTag", "CO2flux", "CO2fluxSlope", "CO2flux_Rsquared"]
    co2fluxDF = pd.DataFrame(co2fluxData, columns=co2fluxColumns)
    
    methaneFluxColumns = ["idTag", "methaneFlux", "methaneFluxSlope",
                          "methaneFlux_Rsquared"]
    if len(methaneFluxData) > 0:
        methaneFluxDF = pd.DataFrame(methaneFluxData, columns=methaneFluxColumns)
        co2fluxDF = co2fluxDF.merge(methaneFluxDF, "outer", "idTag")
    return metadataDF, co2fluxDF


def recalculateVolume(df):
    """
    Recalculates the total volume for a measurement based on corrections to
    either the collar offset or collar diameter. This function assumes that
    newer, more accurate measurements for collar offset or soil area (collar
    diameter) have already been entered into the dataframe.

    Parameters
    ----------
    df : Pandas dataframe
        Dataframe where each row is an observation whose total volume should be
        recalculated and whose offset and soilArea columns have already been
        updated with new measurements.

    Returns
    -------
    The same dataframe where the total volumes are recalculated
    """
    df.totalVolume = (df.soilArea * df.offset) + df.chamberVolume + df.gasAnalyzerVolume
    return df


def recalculateFlux(df, gas):
    """
    Takes a dataframe where each row is a specific measurement whose flux needs
    to be recalculated and then recalculates the flux based on new measurements
    for volume (e.g. diameter and collar offset)

    Parameters
    ----------
    df : Pandas dataframe
        Dataframe where each row is an observation whose flux needs to be
        recalculated.
    gas : str
        The gas species whose flux is to be recalculated.

    Returns
    -------
    The same dataframe with new flux values.
    """
    if gas == "CO2":
        fluxColumn = "CO2flux"
        slopeColumn = "CO2fluxSlope"
    elif gas == "methane":
        fluxColumn = "methaneFlux"
        slopeColumn = "methaneFluxSlope"
    kelvin = df.T_o + 273.15
    R = 8.31446261815324
    df[fluxColumn] = (df[slopeColumn] * df.P_o * df.totalVolume * 10)/(R * kelvin * df.soilArea)
    return df
