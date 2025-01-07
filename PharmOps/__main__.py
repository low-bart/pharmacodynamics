from guitools import *
from platformdirs import user_data_dir
import os

def get_default_h5_path(appName="PharmOps", fileName="data_store.h5"):
    # Determine the platform-specific data directory
    data_dir = user_data_dir(appName, appauthor=False)
    os.makedirs(data_dir, exist_ok=True)  # Ensure the directory exists
    return os.path.join(data_dir, fileName)

def main():
    pass

if __name__ == "__main__":
    main()
    # load sample data
    # make GUI window appear
    sPath = get_default_h5_path()
    print(sPath)
    sampleWellPlate = 'sample data\\Binding Template for RAW transformations.xlsx'
    initialize_GUI()
    # load directories of h5 or xlsx files
    # make new DrugReports
    