import pickle
import h5py
import pandas as pd
import numpy as np
import PharmOps
from PharmOps import WellData
from importlib.metadata import version
from platformdirs import user_data_dir
import os
import re

def read_raw_well_txt(filepath):
    rawData = pd.read_csv(filepath)
    pattern = r"Plate \d+.*?(?=Plate \d+|Total count rate:|$)"
    matches = re.findall(pattern, rawData.to_string(), re.DOTALL)
    plateData = {}
    plateDF = {}
    rowLabels = ["A", "B", "C", "D", "E", "F", "G", "H"]
    for match in matches:
        lines = re.split('\n', match)
        processedLines = []
        for line in lines:
            line = line.replace('\\t', '\t')
            contents = line.split('\t')
            processedLines.append(contents)
        plateNumberMatch = re.search(r"plate (\d+)", match)
        if plateNumberMatch:
            plateNo = plateNumberMatch.group(1)
            plateData[f"Plate_{plateNo}"] = processedLines

    cleanedData = {}
    for plate, rows in plateData.items():
        numericRows = []
        for row in rows:
            rowLabel = row[0].strip()[-1]
            if rowLabel not in rowLabels:
                continue
            dataColumns = row[1:13]
            try:
                dataColumnsInt = [int(value) for value in dataColumns]
                numericRows.append(dataColumnsInt)
            except ValueError:
                continue

        df = pd.DataFrame(numericRows, columns=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12])
        df.index = [row[0].strip()[-1] for row in rows if row[0].strip()[-1] in rowLabels]
        cleanedData[plate] = df

    wellDataObjects = []
    for plate, df in cleanedData.items():
        wellDataObjects.append(WellData(df, plate))
    return wellDataObjects


def read_raw_well_csv(filepath):
    rawData = pd.read_excel(filepath)
    rawWellValues = rawData.loc[rawData.index[0:8], range(1, 12)]    
    return rawWellValues

def get_default_h5_path(appName="PharmOps", fileName="data_store.h5"):
    # Determine the platform-specific data directory
    data_dir = user_data_dir(appName, appauthor=False)
    os.makedirs(data_dir, exist_ok=True)  # Ensure the directory exists
    return os.path.join(data_dir, fileName)

def save_new_h5(drugRep, filepath):
    serializedObj = pickle.dumps(drugRep)
    serializedArray = np.frombuffer(serializedObj, dtype='uint8')
    drugName = drugRep.drug
    receptorName = drugRep.metadata.receptor
    with h5py.File(filepath, "a") as h5file:
        group = h5file.require_group(drugName)
        if receptorName in group:
            print(f"Receptor '{receptorName}' already exists for drug '{drugName}'")
            return
        grp = group.create_dataset(receptorName, data=serializedArray)
        currentVersion = version("PharmOps")
        group.attrs["version"] = currentVersion

def load_h5_DrugReports(drugName, receptorName, filepath):
    with h5py.File(filepath, "r") as h5file:
        if drugName not in h5file:
            raise KeyError(f"No drug '{drugName}' found in h5 file")
        if receptorName not in h5file[drugName]:
            raise KeyError(f"No receptor '{receptorName}' data found for '{drugName}'")
        serializedArray = h5file[drugName][receptorName][:]
    loadedRawData = pickle.loads(serializedArray.tobytes())
    return loadedRawData