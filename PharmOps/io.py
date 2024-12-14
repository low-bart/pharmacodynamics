import pickle
import h5py
import pandas as pd
import numpy as np
import PharmOps
from importlib.metadata import version
def read_raw_well_csv(filepath):
    rawData = pd.read_excel(filepath)
    rawWellValues = rawData.loc[rawData.index[0:8], range(1, 12)]    
    return rawWellValues

def save_new_h5(drugRep, filepath):
    serializedObj = pickle.dumps(drugRep)
    serializedArray = np.frombuffer(serializedObj, dtype='uint8')
    drugName = drugRep.drug
    receptorName = drugRep.receptor
    with h5py.File(filepath, "a") as h5file:
        group = h5file.require_group(drugName)
        if receptorName in group:
            print(f"Receptor '{receptorName}' already exists for drug '{drugName}'")
            return
        group.create_dataset(receptorName, data=serializedArray)
        metadata = h5file.require_group("metadata")
        currentVersion = version("PharmOps")
        if metadata.attrs["version"] != currentVersion:
            print("Warning: version mismatch. Contents from older version may not load properly.")
        metadata.attrs["version"] = currentVersion
def load_h5_DrugReports(drugName, receptorName, filepath):
    with h5py.File(filepath, "r") as h5file:
        if drugName not in h5file:
            raise KeyError(f"No drug '{drugName}' found in h5 file")
        if receptorName not in h5file[drugName]:
            raise KeyError(f"No receptor '{receptorName}' data found for '{drugName}'")
        serializedArray = h5file[drugName][receptorName][:]
    loadedRawData = pickle.loads(serializedArray.tobytes())
    return loadedRawData