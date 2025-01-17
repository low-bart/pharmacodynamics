import pickle
import h5py
import pandas as pd
import numpy as np
import PharmOps
from importlib.metadata import version
from platformdirs import user_data_dir
import os
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