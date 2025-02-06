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
from datetime import datetime

def read_raw_well_txt(filepath):
    rawData = pd.read_csv(filepath)
    pattern = r"Plate \d+.*?(?=Plate \d+|Total count rate:|$)"
    datePattern = r"\b(\d{1,2}-[A-Za-z]{3}-\d{4})\b"    # for regex to find the date
    for i in range(min(len(rawData), 10)):              # limit to the first 10 rows
        for col in rawData.columns:  
            cell = str(rawData.iloc[i][col])
            match = re.search(datePattern, cell)
            if match:
                assayDate = match.group(0)              # return the first matched date
                break

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
        wellDataObjects[-1].set_date(assayDate)
        
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
    dateStr = drugRep.metadata.date
    print(dateStr)
    parsedDate = datetime.strptime(dateStr, "%d-%b-%Y")
    parsedDate = parsedDate.strftime("%Y%m%d")
    with h5py.File(filepath, "a") as h5file:
        group = h5file.require_group(drugName + "/" + receptorName)
        '''
        if receptorName in group:
            print(f"Receptor '{receptorName}' already exists for drug '{drugName}'")
            return
        '''
        grp = group.create_dataset(parsedDate, data=serializedArray)
        currentVersion = version("PharmOps")
        group.attrs["version"] = currentVersion

def load_h5_DrugReports(drugName, receptorName, dateStr, filepath):
    with h5py.File(filepath, "r") as h5file:
        if drugName not in h5file:
            raise KeyError(f"No drug '{drugName}' found in h5 file")
        if receptorName not in h5file[drugName]:
            raise KeyError(f"No receptor '{receptorName}' data found for '{drugName}'")
        if dateStr not in h5file[drugName][receptorName]:
            raise KeyError(f"No assay on '{dateStr}' for drug '{drugName}' and receptor '{receptorName}'")
        serializedArray = h5file[drugName][receptorName][dateStr][:]
    loadedRawData = pickle.loads(serializedArray.tobytes())
    return loadedRawData