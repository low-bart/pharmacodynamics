import tkinter as tk
from tkinter import filedialog, ttk
from PharmOps import io
import numpy as np
import h5py
from bindMods import SummaryTable, TemplateGenerator
import os
import time

# Class for the gui window that acts as home screen
class BindingGUI:
    def __init__(self, main):
        self.main = main
        self.frame = tk.Frame(self.main)
        self.newWellDataButton = tk.Button(self.frame, 
                                            text="Load new WellData", 
                                            command=self.import_WellData)
        self.newWellDataButton.pack()
        self.frame.pack()
        self.loadWellDataButton = tk.Button(self.frame,
                                            text="Load saved WellData",
                                            command=self.load_WellData)
        self.loadWellDataButton.pack()
        self.loadDrugReportsButton = tk.Button(self.frame, 
                                               text="Load saved DrugReports", 
                                               command=self.load_DrugReports)
        self.loadDrugReportsButton.pack()
        self.generateSummaryTableButton = tk.Button(self.frame,
                                                    text="Generate summary tables",
                                                    command=self.generate_summary_tables)
        self.generateSummaryTableButton.pack()
        self.generateTemplateButton = tk.Button(self.frame,
                                                text="Create excel templates",
                                                command=self.generate_excel_templates)
        self.generateTemplateButton.pack()
        self.labelTriplicatesButton = tk.Button(self.frame,
                                                text="Label triplicate data",
                                                command=self.parse_triplicates)
        self.labelTriplicatesButton.pack()
    # creates new window to verify user
    def get_user_info(self):
        userInfo = tk.Toplevel(self.main)
        userName = tk.StringVar(userInfo)
        latestComment = tk.StringVar(userInfo)
        usernameLabel = tk.Label(userInfo, text="Enter your name: ")
        usernameEntry = tk.Entry(userInfo, textvariable=userName)
        userComment = tk.Entry(userInfo, textvariable=latestComment)
        self.entriesComplete = False
        userComments = []

        def add_comment(comment):
            if comment.get() != "":
                userComments.append(comment.get())
                userComment.delete(0, 'end')
            for co in userComments:
                print(co)

        def on_closing_user_info():
            userInfo.destroy()
            userInfo.update()
            self.entriesComplete = False

        def submit_user_info():
            userInfo.destroy()
            userInfo.update()
            self.entriesComplete = True

        userInfo.protocol("WM_DELETE_WINDOW", on_closing_user_info)
        submitComment = tk.Button(userInfo, text="Add comment", command=lambda: add_comment(userComment))
        completeForm = tk.Button(userInfo, text="Submit", command=submit_user_info)        
        usernameLabel.grid(row=0, column=0)
        usernameEntry.grid(row=0, column=1)
        userComment.grid(row=1, column=1)
        submitComment.grid(row=1, column=0)
        completeForm.grid(row=2, column=0, columnspan=2)
        self.main.wait_window(userInfo)

    def calculate_specific_activity(self, countPlate, multFactor):
        filteredData = countPlate[countPlate > 100]
        averageCounts = filteredData.mean().mean()
        cpmAdded = averageCounts * multFactor
        for index, row in countPlate.iterrows():
            print(row)
    
    # loads new window from WellDataGUI class to import WellData from text file
    def import_WellData(self):
        fileName = filedialog.askopenfilename(initialdir=r"e:/PharmOps-sample-data/sample data", 
                                              title='Select a file', 
                                              filetypes=(("Text files",
                                                        "*.txt*"),
                                                       ("all files",
                                                        "*.*")))
        wellDataList = io.read_raw_well_txt(fileName)
        numPlates = len(wellDataList)
        countPlate, multFactor = self.choose_count_plate(numPlates)
        self.get_user_info()
        if not countPlate or not multFactor or not self.entriesComplete:
            return
        countData = wellDataList[countPlate-1].data
        self.calculate_specific_activity(countData, multFactor)

        for num, plate in enumerate(wellDataList):
            if num == countPlate-1:
                continue
            newWindow = tk.Toplevel(self.main)
            WellDataGUI(newWindow, plate)
            self.main.wait_window(newWindow)

    # will load and display WellData from h5 file
    def load_WellData(self):
        pass

    # loads new waitwindow making user pick count plate, radioligand concentration, and multiplication factor
    def choose_count_plate(self, numCountPlates):
        plateSelectWindow = tk.Toplevel(self.main)
        selectedPlate = tk.StringVar(self.main)
        volumeAdded = tk.StringVar(self.main)
        specificActivity = tk.StringVar(self.main)
        self.specificActivityCpm = []
        volumeEntry = tk.Entry(plateSelectWindow, textvariable=volumeAdded)
        specificActivityEntry = tk.Entry(plateSelectWindow, textvariable=specificActivity)
        defaultVal = "Choose a plate"
        selectedPlate.set(defaultVal)
        multiplicationFactor = tk.IntVar(self.main)
        availablePlates = np.arange(1, numCountPlates + 1)
        plateStrings = []
        for plate in availablePlates:
            plateStrings.append(str(plate))
        self.countWindowClosed=False

        def on_closing_plate_selection():
            selectedPlate=0
            multiplicationFactor=0
            plateSelectWindow.destroy()
            plateSelectWindow.update()
            self.countWindowClosed=True

        def confirm_count_plate():
            try:
                self.volumeAdded = float(volumeEntry.get())
                if self.volumeAdded <= 0:
                    raise Exception()
            except:
                self.volumeAdded = 0
                print("Please enter a valid volume in mL, with only positive numbers containing at most one decimal")
            try:
                specificActivityCi = float(specificActivity.get())
                if specificActivityCi <= 0:
                    raise Exception()
                self.specificActivityCpm = specificActivityCi * 2200 * 0.53
            except:
                self.specificActivityCpm = 0
                print("Enter a valid positive specific activity in Ci/pmol")
                return
            if multiplicationFactor.get() == 0 or selectedPlate.get() == defaultVal or not self.volumeAdded:
                print("Please ensure you have selected the count plate and the multiplication factor.")
                return
            plateSelectWindow.destroy()
            plateSelectWindow.update()

        plateSelectWindow.protocol("WM_DELETE_WINDOW", on_closing_plate_selection)
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
        volumeLabel = tk.Label(plateSelectWindow, text="Volume of radioligand added (mL): ")
        volumeLabel.grid(row=3, column=0, sticky="E")
        volumeEntry.grid(row=3, column=1, sticky="W")
        specificActivityLabel = tk.Label(plateSelectWindow, text="Specific activity (Ci/pmol): ")
        specificActivityLabel.grid(row=4, column=0, sticky="E")
        specificActivityEntry.grid(row=4, column=1, sticky="W")
        plateConfirm = tk.Button(plateSelectWindow, text="Confirm count plate", command=confirm_count_plate)
        plateConfirm.grid(row=5, column=0, columnspan=2)
        self.main.wait_window(plateSelectWindow)
        if self.countWindowClosed:
            return 0, 0
        try:
            selectedPlateInt = int(selectedPlate.get())
        except:
            selectedPlateInt = 0
        return selectedPlateInt, multiplicationFactor.get()

    # loads and displays DrugReports from DrugReportsGUI
    def load_DrugReports(self):
        newWindow = tk.Toplevel(self.main)
        DrugReportsGUI(newWindow)
        self.main.wait_window(newWindow)

    # will make summary tables - unclear if this will remain here
    def generate_summary_tables(self):
        summaryDir = filedialog.askdirectory(
            initialdir = os.path.expanduser("~"),
            title="Select the base directory for summary files: "
        )
        summaryObj = SummaryTable(summaryDir)
        summaryObj.make_binding_summary_tables()
        summaryObj.make_function_summary_tables()

    def generate_excel_templates(self):
        newWindow = tk.Toplevel(self.main)
        TemplateGUI(newWindow)
        self.main.wait_window(newWindow)

    def parse_triplicates(self):
        wellDataList = io.read_raw_well_txt(r"e:\PharmOps-sample-data\sample data\110824_raw data.txt")
        plate = wellDataList[0]
        newWindow = tk.Toplevel(self.main)
        TriplicateGUI(newWindow, plate)
        self.main.wait_window(newWindow)

# allows for manual entry of triplicate data and concentrations
class TriplicateGUI:
    def __init__(self, main, plate):
        self.main = main
        self.dataFrame = tk.Frame(self.main)
        self.entryFrame = tk.Frame(self.main,
                                   )
        self.columns = ["1", "2", "3"]
        self.tree = ttk.Treeview(self.dataFrame, columns=self.columns, show="headings")
        self.plate = plate
        plateData = plate.data.reset_index(drop=True)
        self.dataDict = {}
        self.originalData = {(rowIdx, colIdx): value for rowIdx, row in plateData.iterrows() for colIdx, value in enumerate(row)}
        for rowIdx, row in plateData.iterrows():
            numCols = 4
            for triplicate in range(0, numCols):
                self.dataDict[rowIdx, triplicate] = row.iloc[0 + triplicate*3:3 + triplicate*3].to_list()
        self.customTable = CustomTable(self.dataFrame, self.originalData, showData=False)
        self.customTable.pack(expand=True, fill='both')
        print(self.dataDict)
        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120, anchor = "center")
        self.tree.pack(expand=True, fill='both')
        self.tree.pack_propagate(0)
        self.triplicateEntry = tk.Entry(self.entryFrame)
        self.triplicateEntry.pack()
        self.changeButton = tk.Button(self.entryFrame,
                                      text="cycle through dictionary",
                                      command=self.cycle_data)
        self.changeButton.pack()
        self.currentKey = (0, 0)
        self.customTable.update_highlights([(0, 0), (0, 1), (0, 2)])
        self.tree.insert("", "end", values = self.dataDict[self.currentKey])
        self.dataFrame.pack(fill="both", expand="yes")
        self.entryFrame.pack(fill="both", expand="yes")
    
    def cycle_data(self):
        rowIdx = self.currentKey[0]
        tripIdx = self.currentKey[1]
        if rowIdx >= 7 and tripIdx >= 3:
            return
        if tripIdx >= 3:
            tripIdx = 0
            rowIdx += 1
        else:
            tripIdx += 1
        self.currentKey = (rowIdx, tripIdx)
            
        testData = self.dataDict[self.currentKey]
        tupleList = []
        for i in range(0, 3):
            tupleList.append(tuple(map(sum, zip(self.currentKey, (0, self.currentKey[1] * 3 + i - self.currentKey[1])))))
        self.customTable.update_highlights(tupleList)
        for row in self.tree.get_children():
            self.tree.delete(row)
        
        self.tree.insert("", "end", values=testData)

        
# guitools for displaying and manipulating new and saved WellData        
class WellDataGUI:
    def __init__(self, main, plate):
        self.main = main
        self.dataFrame = tk.Frame(self.main)
        self.entryFrame = tk.Frame(self.main)
        self.plate = plate
        plateData = plate.data.reset_index(drop=True)
        dataDict = {(rowIdx, colIdx): value for rowIdx, row in plateData.iterrows() for colIdx, value in enumerate(row)}
        #dataDict = plate.data.to_dict(orient='index')
        #dataDict = {rowKey: {str(colKey): value for colKey, value in colValues.items()} for rowKey, colValues in dataDict.items()}
        #self.model = TableModel()
        #self.model.importDict(dataDict)
        #self.frame.grid(row=0, column=0, columnspan=4, sticky="N, E, W")
        self.dataFrame.pack(fill="both", expand="yes")
        self.entryFrame.pack(fill="both", expand="yes")
        self.customTable = CustomTable(self.dataFrame, dataDict)
        self.customTable.pack(fill=tk.BOTH, expand=True)
        #self.table = TableCanvas(self.dataFrame, model=self.model, read_only=True)
        #self.table.show()
        self.main.after(100, self.adjust_window_width)
        self.drugLabels = ["Drug 1: ", "Drug 2: ", "Drug 3: ", "Drug 4: "]
        self.drugEntries = []
        self.concentrationLabels = ["Highest concentration 1: ", "Highest concentration 2: ", "Highest concentration 3: ", "Highest concentration 4: "]
        self.concentrationEntries = []
        receptorLabel = ttk.Label(self.entryFrame, text="Receptor name: ")
        receptorLabel.grid(row=5, column=0, sticky="E")
        self.receptorName = ttk.Entry(self.entryFrame)
        self.receptorName.grid(row=5, column=1, sticky="W")
        makeReportButton = ttk.Button(self.entryFrame, text="Make new drug reports", command=self.make_drug_reports)
        makeReportButton.grid(row=7, column=1, columnspan=2)
        self.h5Path = io.get_default_h5_path()
        self.recentComment = tk.StringVar(self.entryFrame)
        addCommentButton = ttk.Button(self.entryFrame, 
                                  text="Add comment", 
                                  command=lambda: self.add_comment(self.recentComment.get()))
        self.recentCommentField = ttk.Entry(self.entryFrame, textvariable=self.recentComment)
        addCommentButton.grid(row=6, column=1)
        self.recentCommentField.grid(row=6, column=2)

        for i, labelText in enumerate(self.drugLabels):
            drugEntry = self.create_drug_entry(self.entryFrame, labelText, i + 1, 1)
            self.drugEntries.append(drugEntry)

        for i, labelText in enumerate(self.concentrationLabels):
            concEntry = self.create_drug_entry(self.entryFrame, labelText, i + 1, 2)
            self.concentrationEntries.append(concEntry)

    def adjust_window_width(self):
        numCols = 12
        numRows = 8
        colWidth = self.customTable.cellWidth
        totalWidth = numCols * colWidth
        colHeight = self.customTable.cellHeight
        totalHeight = numRows * colHeight
        self.dataFrame.height = totalHeight
        self.main.geometry(f"{totalWidth}x500")

    def add_comment(self, comment):
        print("comment added")
        self.plate.add_comment(comment)
        self.plate.display()
        self.recentCommentField.delete(0, 'end')

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
            io.save_new_DrugReport(report, self.h5Path)
        print(f"Reports saved to {self.h5Path}")
        self.main.destroy()
        self.main.update()
    
    def validate_user_input(self):
        floatReg ="\d+\.\d+|(?<=angle\s)\d+"    # cursed regular expression to validate float or int
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

# gui class for displaying saved DrugReports from h5
class DrugReportsGUI:
    def __init__(self, main):
        self.main = main
        self.main.geometry("600x300")
        self.h5Path = io.get_default_h5_path()
        self.h5File = h5py.File(self.h5Path, "r")
        self.drugs = list(self.h5File["reports"].keys())
        self.dataset = {drug: self.h5File["reports"][drug] for drug in self.drugs}
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

# Allows for custom behavior in tabular data like cell selection and highlighting
class CustomTable(tk.Frame):
    def __init__(self, parent, data, showData = True):
        super().__init__(parent)

        self.data = data
        self.selectedCells = set()

        self.canvas = tk.Canvas(self, bg="white", bd=0, highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.showData = showData
        if self.showData:
            self.cellWidth = 60
            self.cellHeight = 30
            self.canvas.bind("<Button-1>", self.handle_click)
        else:
            self.cellWidth = 30
            self.cellHeight = 15

        self.draw_table()
    
    def draw_table(self):
        self.canvas.delete("all")

        for (row, col), value in self.data.items():
            x1 = col * self.cellWidth
            y1 = row * self.cellHeight
            x2 = x1 + self.cellWidth
            y2 = y1 + self.cellHeight

            self.canvas.create_rectangle(x1, y1, x2, y2, outline="black", width=1)
            if self.showData:
                self.canvas.create_text(x1 + self.cellWidth/2, y1 + self.cellHeight/2, text=value)
            
            if (row, col) in self.selectedCells:
                self.canvas.create_rectangle(x1, y1, x2, y2, outline="red", width=3)

    def handle_click(self, event):
        col = event.x // self.cellWidth
        row = event.y // self.cellHeight

        if (row, col) in self.data:
            if (row, col) in self.selectedCells:
                self.selectedCells.remove((row, col))
            else:
                self.selectedCells.add((row, col))
            self.draw_table()
    
    def update_highlights(self, indices):
        self.selectedCells = set()
        for tup in indices:
            self.selectedCells.add(tup)
        self.draw_table()

# used to create excel templates for nida/dea assays
class TemplateGUI:
    def __init__(self, main):
        self.main = main
        self.notebook = ttk.Notebook(self.main)
        self.availableReceptors = ["D1", "D2", "D3", "D4", 
                                   "5HT1A", "5HT2A", "5HT2B", "5HT2C"]
        self.currentMode = ""
        self.tabModes = {"binding": {}, 
                         "function": {}}
        self.standardsListbox = {"binding": {},
                               "function": {}}
        self.standardsEntries = {"binding": {},
                                 "function": {}}
        self.standardsDict = {"binding": {},
                              "function": {}}
        for receptor in self.availableReceptors:
            self.create_tab("binding", receptor)
            self.create_tab("function", receptor)
            
        self.bindingStandards = []
        self.bindingTemplateButton = tk.Button(self.main,
                                               text="Binding template settings",
                                               command=self.configure_binding_template)
        self.bindingTemplateButton.grid(row=0, column=0, columnspan=2)
        self.functionTemplateButton = tk.Button(self.main, 
                                                text="Function template settings",
                                                command=self.configure_function_template)
        self.functionTemplateButton.grid(row=1, column=0, columnspan=2)
        self.notebook.grid(row=2, column=0, columnspan=2)
        self.drugNames = []
        self.drugRangeLowLabel = ttk.Label(self.main, text="Enter low end of drug range: ")
        self.drugRangeLowEntry = ttk.Entry(self.main)
        self.drugRangeHighLabel = ttk.Label(self.main, text="Enter high end of drug range: ")
        self.drugRangeHighEntry = ttk.Entry(self.main)
        self.drugRangeLowLabel.grid(row=3, column=0)
        self.drugRangeLowEntry.grid(row=3, column=1)
        self.drugRangeHighLabel.grid(row=4, column=0)
        self.drugRangeHighEntry.grid(row=4, column=1)
        self.drugSingleLabel = ttk.Button(self.main, 
                                          text="Add a new test drug: ", 
                                          command=self.add_single_drug)
        self.drugSingleEntry = ttk.Entry(self.main)
        self.drugSingleLabel.grid(row=5, column=0)
        self.drugSingleEntry.grid(row=5, column=1)
        self.createTemplateButton = ttk.Button(self.main,
                                               text="Create template files",
                                               command=self.save_templates)
        self.createTemplateButton.grid(row=6, column=0, columnspan=2)

    def create_tab(self, mode, receptor):
        frame = ttk.Frame(self.notebook)
        addStandardButton = ttk.Button(frame,
                          text=f"Add {mode} standard",
                          command=self.add_standard)
        addStandardButton.grid(row=0, column=0, sticky="N")
        standardEntry = ttk.Entry(frame)
        standardEntry.grid(row=1, column=0, sticky="N")
        removeStandardButton = ttk.Button(frame,
                                          text="Remove selected standard",
                                          command=self.remove_standard)
        removeStandardButton.grid(row=2, column=0, sticky="S")
        standardList = tk.Listbox(frame)
        standardList.grid(row=0, column=1, rowspan=3)
        self.tabModes[mode][receptor] = frame
        self.standardsListbox[mode][receptor] = standardList
        self.standardsEntries[mode][receptor] = standardEntry
        
    def switch_tabs(self, mode):
        for tab in self.notebook.tabs():
            self.notebook.forget(tab)

        for tabName, frame in self.tabModes[mode].items():
            self.notebook.add(frame, text=tabName)

        self.currentMode = mode

    def configure_binding_template(self):
        self.bindingTemplateButton["state"] = "disabled"
        self.functionTemplateButton["state"] = "normal"
        self.switch_tabs("binding")

    def configure_function_template(self):
        self.bindingTemplateButton["state"] = "normal"
        self.functionTemplateButton["state"] = "disabled"
        self.switch_tabs("function")

    def add_standard(self):
        currentReceptor = self.notebook.tab(self.notebook.select(), "text")
        currentEntry = self.standardsEntries[self.currentMode][currentReceptor]
        currentListbox = self.standardsListbox[self.currentMode][currentReceptor]
        entryText = currentEntry.get()
        if entryText == "" or entryText in currentListbox.get(0, tk.END):
            return
        
        currentListbox.insert(tk.END, entryText)
        currentEntry.delete(0, tk.END)
        if currentReceptor not in self.standardsDict[self.currentMode]:
            self.standardsDict[self.currentMode][currentReceptor] = []
        self.standardsDict[self.currentMode][currentReceptor].append(entryText)
    
    def remove_standard(self):
        currentReceptor = self.notebook.tab(self.notebook.select(), "text")
        currentListbox = self.standardsListbox[self.currentMode][currentReceptor]
        currentSelection = currentListbox.curselection()
        if currentSelection:
            currentListbox.delete(currentSelection[0])
            del self.standardsDict[self.currentMode][currentReceptor][currentSelection[0]]

    def add_single_drug(self):
        entryText = self.drugSingleEntry.get()
        if entryText == "" or entryText in self.drugNames:
            return
        self.drugNames.append(entryText)
        self.drugSingleEntry.delete(0, tk.END)

    def save_templates(self):
        saveDir = filedialog.askdirectory(
            initialdir = os.path.expanduser("~"),
            title="Select the directory where your templates will be saved: "
            )
        lowEntry = self.drugRangeLowEntry.get()
        highEntry = self.drugRangeHighEntry.get()
        if lowEntry != '' and highEntry != '':
            lowRange = int(self.drugRangeLowEntry.get())
            highRange = int(self.drugRangeHighEntry.get()) + 1
            for drug in range(lowRange, highRange):
                self.drugNames.append(drug)
        TemplateGenerator(saveDir, self.drugNames, self.standardsDict)

