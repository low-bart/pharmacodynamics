import tkinter as tk
from tkinter import filedialog
from tkintertable import TableCanvas, TableModel
from PharmOps import WellData
from PharmOps import io
import pandas as pd
import h5py
import re

class BindingGUI:
    def __init__(self, main):
        self.main = main
        self.frame = tk.Frame(self.main)
        self.loadWellDataButton = tk.Button(self.frame, text="Load new WellData", command=self.load_WellData)
        self.loadWellDataButton.pack()
        self.frame.pack()

    def load_WellData():
        filedialog.askopenfilename(initialdir='/', title='Select a file', filetypes=('Text files', '*.txt#'))
        
            
class WellDataGUI:
    def __init__(self, main):
        self.main = main
        self.frame = tk.Frame(self.main)
