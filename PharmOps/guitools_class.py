import tkinter as tk
from tkinter import filedialog, Event, ttk
from tkintertable import TableCanvas, TableModel
from PharmOps import WellData
from PharmOps import io
import pandas as pd
import numpy as np
import h5py
import re

class BindingGUI:
    def __init__(self, main):
        self.main = main
        self.frame = tk.Frame(self.main)
        self.loadWellDataButton = tk.Button(self.frame, 
                                            text="Load new WellData", 
                                            command=self.load_WellData)
        self.loadWellDataButton.pack()
        self.frame.pack()
        self.loadDrugReportsButton = tk.Button(self.frame, 
                                               text="Load saved DrugReports", 
                                               command=self.load_DrugReports)
        self.loadDrugReportsButton.pack()

    def load_WellData(self):
        fileName = filedialog.askopenfilename(initialdir=r"e:/pharmacodynamics/sample data", 
                                              title='Select a file', 
                                              filetypes=(("Text files",
                                                        "*.txt*"),
                                                       ("all files",
                                                        "*.*")))
        wellDataList = io.read_raw_well_txt(fileName)
        numPlates = len(wellDataList)
        countPlate, multFactor = self.choose_count_plate(numPlates)
        if countPlate == 0 or multFactor == 0:
            return
        countData = wellDataList[countPlate-1].data
        radioactivity = 0
        for num, plate in enumerate(wellDataList):
            if num == countPlate-1:
                continue
            newWindow = tk.Toplevel(self.main)
            WellDataGUI(newWindow, plate)
            self.main.wait_window(newWindow)

    def choose_count_plate(self, numCountPlates):
        plateSelectWindow = tk.Toplevel(self.main)
        selectedPlate = tk.StringVar(self.main)
        volumeAdded = tk.StringVar(self.main)
        volumeEntry = tk.Entry(plateSelectWindow, textvariable=volumeAdded)
        defaultVal = "Choose a plate"
        selectedPlate.set(defaultVal)
        multiplicationFactor = tk.IntVar(self.main)
        availablePlates = np.arange(1, numCountPlates + 1)
        plateStrings = []
        for plate in availablePlates:
            plateStrings.append(str(plate))
        self.countWindowClosed=False

        def on_closing_plateSelection():
            selectedPlate=0
            multiplicationFactor=0
            plateSelectWindow.destroy()
            plateSelectWindow.update()
            self.countWindowClosed=True

        def confirm_count_plate():
            try:
                volume = float(volumeEntry.get())
                if volume <= 0:
                    raise Exception()
            except:
                volume = 0
                print("Please enter a valid volume in mL, with only positive numbers containing at most one decimal")
            if multiplicationFactor.get() == 0 or selectedPlate.get() == defaultVal or not volume:
                print("Please ensure you have selected the count plate and the multiplication factor, and have entered the volume of radioligand added.")
                return
            plateSelectWindow.destroy()
            plateSelectWindow.update()

        plateSelectWindow.protocol("WM_DELETE_WINDOW", on_closing_plateSelection)
        plateLabel = tk.Label(plateSelectWindow, text="Select the count plate: ")
        plateLabel.grid(row=0, column=0, sticky="E")
        plateDropdown = tk.OptionMenu(plateSelectWindow, selectedPlate, *plateStrings)
        plateDropdown.grid(row=0, column=1, sticky="W")
        multLabel = tk.Label(plateSelectWindow, text="Confirm your multiplication factor: ")
        multLabel.grid(row=1, column=0, rowspan=2)
        radioButton5x = tk.Radiobutton(plateSelectWindow, text="5x", variable=multiplicationFactor, value=5)
        radioButton10x = tk.Radiobutton(plateSelectWindow, text="10x", variable=multiplicationFactor, value=10)
        radioButton5x.grid(row=1, column=1)
        radioButton10x.grid(row=2, column=1)
        volumeLabel = tk.Label(plateSelectWindow, text="Volume of radioligand added: ")
        volumeLabel.grid(row=3, column=0, sticky="E")
        volumeEntry.grid(row=3, column=1, sticky="W")
        plateConfirm = tk.Button(plateSelectWindow, text="Confirm count plate", command=confirm_count_plate)
        plateConfirm.grid(row=4, column=0, columnspan=2)
        self.main.wait_window(plateSelectWindow)
        if self.countWindowClosed:
            return 0, 0
        try:
            selectedPlateInt = int(selectedPlate.get())
        except:
            selectedPlateInt = 0
        return selectedPlateInt, multiplicationFactor.get()

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
        self.frame.grid(row=0, column=0, columnspan=4, sticky="N, E, W")
        self.main.grid_rowconfigure(0, weight=0)
        self.main.grid_columnconfigure(0, weight=1)
        self.main.grid_columnconfigure(1, weight=1)
        self.main.grid_columnconfigure(2, weight=1)
        self.main.grid_columnconfigure(3, weight=1)
        self.table = TableCanvas(self.frame, model=self.model, read_only=False)
        self.table.show()
        self.drugLabels = ["Drug 1: ", "Drug 2: ", "Drug 3: ", "Drug 4: "]
        self.drugEntries = []
        self.concentrationLabels = ["Highest concentration 1: ", "Highest concentration 2: ", "Highest concentration 3: ", "Highest concentration 4: "]
        self.concentrationEntries = []
        receptorLabel = ttk.Label(self.main, text="Receptor name: ")
        receptorLabel.grid(row=5, column=0, sticky="E")
        self.receptorName = ttk.Entry(self.main)
        self.receptorName.grid(row=5, column=1, sticky="W")
        makeReportButton = ttk.Button(self.main, text="Make new drug reports", command=self.make_drug_reports)
        makeReportButton.grid(row=5, column=2, columnspan=2)
        self.h5Path = io.get_default_h5_path()
            
        def on_resize(event):
            table_width = event.width
            column_width = self.table.cellwidth
            max_visible_columns = max(1, table_width // column_width)
            self.table.model.columnWidths = [column_width] * max_visible_columns
            self.table.redraw()

        self.frame.bind("<Configure>", on_resize)

        for i, labelText in enumerate(self.drugLabels):
            drugEntry = self.create_drug_entry(self.main, labelText, i + 1, 1)
            self.drugEntries.append(drugEntry)

        for i, labelText in enumerate(self.concentrationLabels):
            concEntry = self.create_drug_entry(self.main, labelText, i + 1, 2)
            self.concentrationEntries.append(concEntry)

    def create_drug_entry(self, parent, labelText, row, entryNo):
        entryVar = tk.StringVar()
        label = ttk.Label(parent, text=labelText)
        label.grid(row=row, column=(entryNo*2)-2, padx=5, pady=5, sticky="E")
        entry = ttk.Entry(parent, textvariable=entryVar)
        entry.grid(row=row, column=(entryNo*2)-1, padx=5, pady=5, sticky="W")
        return entryVar

    def make_drug_reports(self):
        self.validate_user_input()
        self.update_plate()
        reports = self.plate.make_all_drug_reports()
        for report in reports:
            io.save_new_h5(report, self.h5Path)
        print(f"Reports saved to {self.h5Path}")
        self.main.destroy()
        self.main.update()
    
    def validate_user_input(self):
        floatReg ="\d+\.\d+|(?<=angle\s)\d+"
        for entry in self.concentrationEntries:
            try: 
                float(entry.get())
            except ValueError:
                raise TypeError('bad datatype for concentration: enter int or float')
            
    def update_plate(self):
        for i, entry in enumerate(self.drugEntries):
            self.plate.update_conc(float(self.concentrationEntries[i].get()), i)
            self.plate.update_drugs(entry.get(), i) 
        self.plate.update_receptor(self.receptorName.get())

class DrugReportsGUI:
    def __init__(self, main):
        self.main = main
        self.main.geometry("600x300")
        self.h5Path = io.get_default_h5_path()
        self.h5File = h5py.File(self.h5Path, "r")
        self.drugs = list(self.h5File.keys())
        self.dataset = {drug: self.h5File[drug] for drug in self.drugs}
        self.drugLabel = tk.Label(self.main, text="Select a drug: ")
        self.drugLabel.grid(row=0, column=0, sticky="NEW")
        self.drugSelected = tk.StringVar()
        self.drugDrop = ttk.Combobox(self.main, textvariable=self.drugSelected, values=self.drugs)
        self.drugDrop.grid(row=0, column=1, sticky="NW")
        self.receptorLabel = tk.Label(self.main, text="Select a receptor: ")
        self.receptorLabel.grid(row=1, column=0, sticky="NEW")
        self.receptorClicked = tk.StringVar()
        self.receptorDrop = ttk.Combobox(self.main, textvariable=self.receptorClicked)
        self.receptorDrop.grid(row=1, column=1, sticky="NW")
        self.dateLabel = tk.Label(self.main, text="Select an assay date: ")
        self.dateLabel.grid(row=2, column=0, sticky="NEW")
        self.dateSelected = tk.StringVar()
        self.dateDrop = ttk.Combobox(self.main, textvariable=self.dateSelected)
        self.dateDrop.grid(row=2, column=1, sticky="NW")
        self.drugDrop.bind("<<ComboboxSelected>>", lambda event: self.update_receptors(event))
        self.receptorDrop.bind("<<ComboboxSelected>>", lambda event: self.update_dates(event))
        self.dateDrop.bind("<<ComboboxSelected>>", lambda event: self.update_DrugReports_GUI(event))
        self.columns = ["Average", "Specific", "[Drug]", "Log [Drug]", "Pct Total"]
        self.tree = ttk.Treeview(self.main, columns=self.columns, show="headings")
        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120, anchor="center")
        self.tree.grid(row=3, column=0, columnspan=3, sticky="E, W")
        self.main.grid_columnconfigure(0, weight=1)

    def update_receptors(self, event):
        self.selectedDrug = self.drugDrop.get()
        if self.selectedDrug:
            receptorKeys = list(self.dataset[self.selectedDrug].keys())
            self.receptorDrop['values'] = receptorKeys
            self.receptorDrop.set('')
        else:
            print("No drug selected.")

    def update_dates(self, event):
        self.selectedReceptor = self.receptorDrop.get()
        if self.selectedReceptor:
            dateKeys = list(self.dataset[self.selectedDrug][self.selectedReceptor].keys())
            self.dateDrop['values'] = dateKeys
            self.dateDrop.set('')
        else:
            print("No date selected")
    
    def update_DrugReports_GUI(self, event):
        selectedDate = self.dateDrop.get()
        currentDrugReport = io.load_h5_DrugReports(self.selectedDrug, self.selectedReceptor, selectedDate, self.h5Path)

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