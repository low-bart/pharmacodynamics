from importlib.metadata import version
from platformdirs import user_data_dir
import PharmOps
from PharmOps import io
import h5py

defaultName = io.get_default_h5_path()
print(defaultName)

with h5py.File(defaultName, "r") as h5file:
    print(list(h5file.keys()))
