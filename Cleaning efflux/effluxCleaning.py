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
import openpyxl
import os


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
    1. A dataframe containing the metadata and a dataframe containing either only
    CO2 flux data (if the data was collected by an 870) or both CO2 and methane
    fluxes (if the data was collected by a 7810)

    2. A dataframe containing the metadata

    3. A dataframe containing the measurements that were forcefully interrupted
    """
    dataset = jsonDictionary["datasets"]
    metadata = []
    co2fluxData = []
    methaneFluxData = []
    interruptedIDtags = []
    for observation in dataset:
        idTag = list(observation.keys())[0]
        observationLowerLevel = observation[idTag]
        remark = observationLowerLevel["remark"]
        reps = observationLowerLevel["reps"]
        if bool(reps) == True:
            """A dictionary evaluates to True if it's not empty and to False
            if it's empty. This dictionary is empty is the person operating
            the tablet controlling the Smart Chamber decided to stop the
            measurement process on the tablet."""
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
        else:
            interruptedIDtags.append(idTag)
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
    return {"metadata": metadataDF, "data": co2fluxDF, "interruptedMeasurements": interruptedIDtags}


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


def plotAndCollar(df):
    """
    Takes either a dataframe of flux data or a dataframe of metadata (though I
    intend to use this for the dataframe of metadata) and extracts the metadata
    on plot (plot type and plot number) and collar for the flux measurement
    from a measurement's idTag. This function assumes that the idTag is
    formatted as
    plottypePlotnumberCollar, e.g.
    Grass15A

    Parameters
    ----------
    df : Pandas dataframe
        Dataframe containing either flux data or metadata. Dataframe must have
        a column called idTag.

    Returns
    -------
    The same dataframe with new columns containing plot type, plot number, and
    collar
    """
    df["plotType"] = df["idTag"].str.extract(r"^([a-zA-Z]+)")
    df["plotNumber"] = df["idTag"].str.extract(r"^[a-zA-Z]+([0-9]{1,2})")
    df["collar"] = df["idTag"].str.extract(r"^[a-zA-Z]+[0-9]{1,2}([a-zA-Z])")

    df["plotType"] = df["plotType"].str.capitalize()
    df["collar"] = df["collar"].str.upper()
    return df


unitsMetadata1 = [["Units are as follows"],
                  ["- CO2flux: micromole CO2 per square meter per second"],
                  ["- CO2fluxSlope: ppm CO2 in dry air (or micromole CO2 per mole dry air) per second"],
                  ["- methaneFlux: nanomole CH4 per square meter per second"],
                  ["- methaneFluxSlope: ppb CH4 in dry air (or nanomole CH4 per mole dry air) per second"],
                  ["- soilArea: cm squared"],
                  ["- collar offset: cm"],
                  ["- volumes (chamber, gas analyzer, and total): cm cubed"],
                  ["- initial pressure (P_o): kPa"],
                  ["- initial temperature (T_o): Celsius"],
                  ["- initial fraction of water vapor in air (W_o): mmol water vapor per mole air (total air, not dry air)"],
                  ["- dateTime: date and time written as yyyy-mm-dd HH:MM:SS where hour (HH) is written out of 24 hours rather than as AM or PM"]
                  ]


def exportCleanData(path, df, readMe):
    """
    Exports an Excel file of the cleaned flux data.

    Parameters
    ----------
    path : path-like object
        The file path for the data once the data is exported.
    df : Pandas dataframe
        Dataframe containing the cleaned flux data.
    readMe : list of string
        A list of string that will be the ReadMe tab in the output Excel file.

    Returns
    -------
    None
    """
    if os.path.exists(path) is False:
        wb = openpyxl.Workbook()
        readMeTab = wb.active
        readMeTab.title = "ReadMe"
        for line in readMe:
            readMeTab.append(line)
        data = wb.create_sheet("Data")
        data.append(df.columns.tolist())
        dataList = df.to_numpy().tolist()
        for line in dataList:
            data.append(line)
        wb.save(path)
        print("File saved")
    else:
        print("File already exists")
    return
