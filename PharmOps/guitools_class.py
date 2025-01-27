import tkinter as tk
from tkinter import filedialog, Event, ttk
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
        self.loadDrugReportsButton = tk.Button(self.frame, text="Load saved DrugReports", command=self.load_DrugReports)
        self.loadDrugReportsButton.pack()

    def load_WellData(self):
        fileName = filedialog.askopenfilename(initialdir=r"e:/pharmacodynamics/sample data", 
                                              title='Select a file', 
                                              filetypes=(("Text files",
                                                        "*.txt*"),
                                                       ("all files",
                                                        "*.*")))
        wellDataList = io.read_raw_well_txt(fileName)
        for plate in wellDataList:
            newWindow = tk.Toplevel(self.main)
            WellDataGUI(newWindow, plate)
            self.main.wait_window(newWindow)
    
    def load_DrugReports(self):
        newWindow = tk.Toplevel(self.main)
        DrugReportsGUI(newWindow)
        self.main.wait_window(newWindow)

            
class WellDataGUI:
    def __init__(self, main, plate):
        self.main = main
        self.frame = tk.Frame(self.main)
        self.plate = plate
        dataDict = plate.data.to_dict(orient='index')
        dataDict = {rowKey: {str(colKey): value for colKey, value in colValues.items()} for rowKey, colValues in dataDict.items()}
        self.model = TableModel()
        self.model.importDict(dataDict)
        self.frame.grid(row=0, column=0, columnspan=4)
        self.table = TableCanvas(self.frame, model=self.model, read_only=False)
        self.table.show()
        self.drugLabels = ["Drug 1: ", "Drug 2: ", "Drug 3: ", "Drug 4: "]
        self.drugEntries = []
        self.concentrationLabels = ["Highest concentration 1: ", "Highest concentration 2: ", "Highest concentration 3: ", "Highest concentration 4: "]
        self.concentrationEntries = []
        receptorLabel = ttk.Label(self.main, text="Receptor name: ")
        receptorLabel.grid(row=5, column=1, sticky="E")
        self.receptorName = ttk.Entry(self.main)
        self.receptorName.grid(row=5, column=2, sticky="W")
        makeReportButton = ttk.Button(self.main, text="Make new drug reports", command=self.make_drug_reports)
        makeReportButton.grid(row=6, column=2)
        self.h5Path = io.get_default_h5_path()

        for i, labelText in enumerate(self.drugLabels):
            drugEntry = self.create_drug_entry(self.main, labelText, i + 1, 1, lambda idx=i: self.on_drug_change(idx))
            self.drugEntries.append(drugEntry)

        for i, labelText in enumerate(self.concentrationLabels):
            concEntry = self.create_drug_entry(self.main, labelText, i + 1, 2, lambda idx=i: self.on_conc_change(idx))
            self.concentrationEntries.append(concEntry)


    def create_drug_entry(self, parent, labelText, row, entryNo, callback):
        entryVar = tk.StringVar()
        entryVar.trace_add("write", lambda *args: callback())

        label = ttk.Label(parent, text=labelText)
        label.grid(row=row, column=(entryNo*2)-2, padx=5, pady=5, sticky="E")

        entry = ttk.Entry(parent, textvariable=entryVar)
        entry.grid(row=row, column=(entryNo*2)-1, padx=5, pady=5, sticky="W")

        return entryVar

    def on_drug_change(self, index):
        new_value = self.drugEntries[index].get()

        if isinstance(index, str):
            index = int(index)

        self.plate.update_drugs(new_value, index)


    
    def on_conc_change(self, index):
        
        self.plate.update_conc(int(self.concentrationEntries[index].get()), index)

    def make_drug_reports(self):
        for i, entry in enumerate(self.drugEntries):
            print(f"Drug {i}: {entry.get()}")
            self.plate.update_drugs(entry.get(), i)
        
        self.plate.metadata.receptor = self.receptorName.get()
        
        reports = self.plate.make_all_drug_reports()
        for report in reports:
            io.save_new_h5(report, self.h5Path)
        print(f"Reports saved to {self.h5Path}")

class DrugReportsGUI:
    def __init__(self, main):
        self.main = main
        self.main.geometry("600x300")
        self.h5Path = io.get_default_h5_path()
        self.h5File = h5py.File(self.h5Path, "r")
        self.drugs = list(self.h5File.keys())
        self.dataset = {drug: self.h5File[drug] for drug in self.drugs}
        self.drugLabel = tk.Label(self.main, text="Select a drug: ")
        self.drugLabel.grid(row=0, column=0, sticky="E")
        self.drugSelected = tk.StringVar()
        self.drugDrop = ttk.Combobox(self.main, textvariable=self.drugSelected, values=self.drugs)
        self.drugDrop.grid(row=0, column=2, sticky="W")
        self.receptorLabel = tk.Label(self.main, text="Select a receptor: ")
        self.receptorLabel.grid(row=1, column=0, sticky="E")
        self.receptorClicked = tk.StringVar()
        self.receptorDrop = ttk.Combobox(self.main, textvariable=self.receptorClicked)
        self.receptorDrop.grid(row=1, column=2, sticky="W")
        self.drugDrop.bind("<<ComboboxSelected>>", lambda event: self.update_datasets(event))
        self.receptorDrop.bind("<<ComboboxSelected>>", lambda event: self.update_DrugReports_GUI(event))
        self.columns = ["Average", "Specific", "[Drug]", "Log [Drug]", "Pct Total"]
        self.tree = ttk.Treeview(self.main, columns=self.columns, show="headings")
        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120, anchor="center")
        self.tree.grid(row=2, column=0, columnspan=3, sticky="E, W")
        self.main.grid_columnconfigure(0, weight=1)

    def update_datasets(self, event):
        selected_group = self.drugDrop.get()
        print(f"Selected Drug: '{selected_group}'")  # Debugging line to check the value
        if selected_group:  # Ensure a drug is selected
            # Get the datasets for the selected drug (group)
            new_keys = list(self.dataset[selected_group].keys())  # Sub-datasets for the selected group
            self.receptorDrop['values'] = new_keys  # Update second dropdown values
            self.receptorDrop.set('')  # Clear any previously selected receptor
        else:
            print("No drug selected.")
    
    def update_DrugReports_GUI(self, event):
        drugName = self.drugDrop.get()
        receptorName = self.receptorDrop.get()
        currentDrugReport = io.load_h5_DrugReports(drugName, receptorName, self.h5Path)

        for row in self.tree.get_children():
            self.tree.delete(row)

        for i in range(len(currentDrugReport.average)):
            self.tree.insert("", "end", values=(
                currentDrugReport.average[i],
                currentDrugReport.specific[i],
                currentDrugReport.concentration[i],
                currentDrugReport.logConc[i],
                currentDrugReport.pctTotal[i]
            ))


