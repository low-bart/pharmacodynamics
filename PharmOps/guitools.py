import tkinter as tk
from tkinter import filedialog, ttk
from PharmOps import io
import numpy as np
import h5py
from bindMods import *
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass

# Class for the gui window that acts as home screen
class BindingGUI:
    def __init__(self, main):
        self.main = main
        self.frame = tk.Frame(self.main)
        self.frame.pack()
        self.newBindingPlateButton = tk.Button(self.frame, 
                                            text="Load new binding assay", 
                                            command=self.import_BindingPlate)
        self.loadBindingPlateButton = tk.Button(self.frame,
                                            text="Load saved binding assay",
                                            command=self.load_BindingPlate)
        self.loadDrugReportsButton = tk.Button(self.frame, 
                                               text="Load saved DrugReports", 
                                               command=self.load_DrugReports)
        self.generateSummaryTableButton = tk.Button(self.frame,
                                                    text="Generate summary tables",
                                                    command=self.generate_summary_tables)
        self.generateTemplateButton = tk.Button(self.frame,
                                                text="Create excel templates",
                                                command=self.generate_excel_templates)
        self.labelTriplicatesButton = tk.Button(self.frame,
                                                text="Label triplicate data",
                                                command=self.parse_triplicates)
        self.newBindingPlateButton.pack()
        self.loadBindingPlateButton.pack()
        self.loadDrugReportsButton.pack()
        self.generateSummaryTableButton.pack()
        self.generateTemplateButton.pack()
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
    
    # loads new window from BindingPlateGUI class to import BindingPlate from text file
    def import_BindingPlate(self):
        fileName = filedialog.askopenfilename(
            initialdir=r"e:/PharmOps-sample-data/sample data", 
            title='Select a file', 
            filetypes=(("Text files",
                    "*.txt*"),
                    ("all files",
                    "*.*")))
        wellDataList = io.read_raw_well_txt(fileName, BindingPlate)
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
            BindingPlateGUI(newWindow, plate)
            self.main.wait_window(newWindow)

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

    # will load and display BindingPlate from h5 file
    def load_BindingPlate(self):
        pass

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
        fileName = filedialog.askopenfilename(
            initialdir="~", 
            title='Select a file', 
            filetypes=(("Text files",
                    "*.txt*"),
                    ("all files",
                    "*.*")))
        wellDataList = io.read_raw_well_txt(fileName, ScreeningPlate)
        plate = wellDataList[0]
        newWindow = tk.Toplevel(self.main)
        TriplicateGUI(newWindow, plate)
        self.main.wait_window(newWindow)

# abstract base class to inherit modes of cell selection from
class SelectionStrategy(ABC):
    @abstractmethod
    def on_click(self, row, col, event):
        pass

    def on_drag(self, row, col, event, currentSelection):
        return currentSelection
    
    def on_release(self, row, col, event, currentSelection):
        return currentSelection
    
    def on_up_arrow(self, row, col, event, currentSelection):
        pass

    def on_down_arrow(self, row, col, event, currentSelection):
        pass

    def on_left_arrow(self, row, col, event, currentSelection):
        pass

    def on_right_arrow(self, row, col, event, currentSelection):
        pass
    
    def add_selection(self, row, col):
        pass

    def get_selected_cells(self):
        pass

    def get_locked_cells(self):
        return {}
    
# select/deselect the cell that was clicked
class SingleCellSelector(SelectionStrategy):
    def __init__(self, selectedCell, lockedCells):
        self.selectedCell = selectedCell
        self.lockedCells = lockedCells

    def on_click(self, row, col):
        if (row, col) in self.lockedCells:
            return
        if (row, col) == self.selectedCell:
            self.selectedCell.clear()
        else:
            self.selectedCell.clear()
            self.selectedCell.add((row, col))

    def get_selected_cells(self):
        return self.selectedCell

# allow multiple cells to be selected at once
class MultiCellSelector(SelectionStrategy):
    def __init__(self, selectedCells, lockedCells):
        self.selectedCells = selectedCells
        self.lockedCells = lockedCells

    def on_click(self, row, col):
        if (row, col) in self.lockedCells:
            return
        if (row, col) in self.selectedCells:
            self.selectedCells.remove((row, col))
        else:
            self.selectedCells.add((row, col))

    def get_selected_cells(self):
        return self.selectedCells

# select/deselect the triplet containing the cell that was clicked
class SingleTripletSelector(SelectionStrategy):
    def __init__(self, selectedTriplets, lockedTriplets):
        self.selectedTriplets = selectedTriplets
        self.lockedTriplets = lockedTriplets
        self.clickX = None
        self.clickY = None
        self.rowClicked = None
        self.colClicked = None

    def on_click(self, row, col, event):
        self.clickX = event.x
        self.clickY = event.y
        self.rowClicked = row
        self.colClicked = col
        triplet = col // 3
    
    def on_drag(self, row, col, event):
        latestX = event.x
        latestY = event.y
        return([self.clickX, self.clickY, latestX, latestY])
    
    def on_release(self, row, col, event):
        triplet = self.colClicked // 3
        if (self.rowClicked, triplet) in self.lockedTriplets:
            return
        if (self.rowClicked, triplet) in self.selectedTriplets:
            self.selectedTriplets.remove((self.rowClicked, triplet))
            return
        self.add_selection(self.rowClicked, triplet)

    def add_selection(self, row, triplet):
        self.selectedTriplets.clear()
        self.selectedTriplets.add((row, triplet))

    def on_up_arrow(self, row, col):
        triplet = col // 3
        if row == 0:
            row = 7
        else:
            row -= 1
        self.add_selection(row, triplet)

    def on_down_arrow(self, row, col):
        triplet = col // 3
        if row == 7:
            row = 0
        else:
            row += 1
        self.add_selection(row, triplet)

    def on_left_arrow(self, row, col):
        triplet = col // 3
        if triplet == 0:
            triplet = 3
        else:
            triplet -= 1
        self.add_selection(row, triplet)

    def on_right_arrow(self, row, col):
        triplet = col // 3
        if triplet == 3:
            triplet = 0
        else:
            triplet += 1
        self.add_selection(row, triplet)

    def get_selected_cells(self):
        return{(row, col) 
               for (row, startCol) in self.selectedTriplets 
               for col in range(startCol*3, startCol*3 + 3)}
    
    def get_locked_cells(self):
        return{(row, col) 
               for (row, startCol) in self.lockedTriplets 
               for col in range(startCol*3, startCol*3 + 3)}

# allow multiple triplets to be selected
class MultiTripletSelector(SingleTripletSelector):
    def on_release(self, row, col, event):
        if row < 0:
            row = 0
        if row > 7:
            row = 7
        if col < 0:
            col = 0
        if col > 11:
            col = 11
        rows = [row, self.rowClicked]
        cols = [col, self.colClicked]
        rowRange = range(min(rows), max(rows) + 1)
        colRange = range(min(cols), max(cols) + 1)
        tripletsIncluded = np.unique([x // 3 for x in colRange])
        for row in rowRange:
            for triplet in tripletsIncluded:
                if (row, triplet) in self.lockedTriplets:
                    continue
                elif (row, triplet) in self.selectedTriplets:
                    self.selectedTriplets.remove((row, triplet))
                else:
                    self.selectedTriplets.add((row, triplet))
    

# select cells by row (no single selector yet)
class RowSelector(SelectionStrategy):
    def __init__(self, selectedRows, lockedRows):
        self.selectedRows = selectedRows
        self.lockedRows = lockedRows
        self.clickX = None
        self.clickY = None
        self.rowClicked = None
        self.colClicked = None

    def on_click(self, row, col, event):
        if col not in range(0, 12):
            return
        #if row in self.lockedRows:
        #    return
        self.clickX = event.x
        self.clickY = event.y
        self.rowClicked = row
        self.colClicked = col
        #if row in self.selectedRows:
        #    self.selectedRows.remove(row)
        #    return
        #self.selectedRows.clear() #commented out while i figure out how to divide multiselect
        #self.selectedRows.add(row)

    def on_drag(self, row, col, event):
        latestX = event.x
        latestY = event.y
        return([self.clickX, self.clickY, latestX, latestY])
    
    def on_release(self, row, col, event):
        if row < 0:
            row = 0
        if row > 7:
            row = 7
        rows = [row, self.rowClicked]
        rowRange = range(min(rows), max(rows) + 1)
        for row in rowRange:
            if row in self.lockedRows:
                continue
            if row in self.selectedRows:
                self.selectedRows.remove(row)
            else:
                self.selectedRows.add(row)

    def get_selected_cells(self):
        return {(row, col)
                for row in self.selectedRows
                for col in range(0, 12)}
    
    def get_locked_cells(self):
        return{(row, col)
               for row in self.lockedRows
               for col in range(0, 12)}
    
# contains default cell styling params to pass to CustomTable
@dataclass
class CellStyle:
    fill: str = "white"
    outline: str = "black"
    text: str = ""
    font: str = "TkDefaultFont"
    width: int = 2
    stipple: str = None

# abstract base class for different stylings, returning a CellStyle object
class CellStyleResolver(ABC):
    @abstractmethod
    def get_cell_style(self, row, col) -> CellStyle:
        # returns drawing properties for different contexts
        pass

class HighlightSelection(CellStyleResolver):
    def __init__(self, selectionSet, selectionStrategy):
        self.selectionSet = selectionSet
        self.strategy = selectionStrategy

    def get_cell_style(self, row, col):
        parentSelection = self.strategy.get_selected_cells()
        if (row, col) in parentSelection:
            return CellStyle(fill="firebrick1", outline="black", width=2)
        return CellStyle
        
class HighlightAndLockSelection(CellStyleResolver):
    def __init__(self, selectionStrategy):
        self.strategy = selectionStrategy

    def get_cell_style(self, row, col):
        parentSelection = self.strategy.get_selected_cells() or {}
        parentLock = self.strategy.get_locked_cells() or {}
        if (row, col) in parentSelection:
            return CellStyle(fill="firebrick1")
        elif (row, col) in parentLock:
            return CellStyle(fill="dodger blue")
        return CellStyle
        
class HighlightAndBlockSelection(CellStyleResolver):
    def __init__(self, blockedCells, selectionStrategy):
        self.blockedCells = blockedCells
        self.strategy = selectionStrategy

    def get_cell_style(self, row, col):
        parentSelection = self.strategy.get_selected_cells() or {}
        parentLock = self.strategy.get_locked_cells() or {}
        if (row, col) in self.blockedCells:
            return CellStyle(fill="gray", stipple='gray50')
        if (row, col) in parentSelection:
            return CellStyle(fill="firebrick1")
        if (row, col) in parentLock:
            return CellStyle(fill="dodger blue")
        return CellStyle
    
class BlueWeighingSelection(HighlightAndBlockSelection):
    def get_cell_style(self, row, col):
        parentSelection = self.strategy.get_selected_cells() or {}
        parentLock = self.strategy.get_locked_cells() or {}     
        if (row, col) in self.blockedCells:
            return CellStyle(fill="gray", stipple='gray50')
        if (row, col) in parentSelection:
            return CellStyle(fill="Blue")
        if (row, col) in parentLock:
            return CellStyle(fill="Blue", outline="dark slate gray")
        return CellStyle
        
class BlackWeighingSelection(HighlightAndBlockSelection):
    def get_cell_style(self, row, col):
        parentSelection = self.strategy.get_selected_cells() or {}
        parentLock = self.strategy.get_locked_cells() or {}
        if (row, col) in self.blockedCells:
            return CellStyle(fill="gray", stipple='gray50')
        if (row, col) in parentSelection:
            return CellStyle(fill="gray10")
        if (row, col) in parentLock:
            return CellStyle(fill="black")
        return CellStyle
    
# Allows for custom behavior in tabular data like cell selection and highlighting
class CustomTable(tk.Frame):
    def __init__(self, 
                 parent, 
                 data, 
                 showData=True, 
                 cellStyle: CellStyleResolver=None):
        
        super().__init__(parent)
        self.showData = showData
        if self.showData:
            self.cellWidth = 60
            self.cellHeight = 30
        else:
            self.cellWidth = 30
            self.cellHeight = 15
        self.numRows = 8
        self.numColumns = 12
        self.canvas = tk.Canvas(self, 
                                bg="white", 
                                bd=0, 
                                highlightthickness=0, 
                                height=self.cellHeight*self.numRows, 
                                width=self.cellWidth*self.numColumns)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.bindings = {}
        self.data = data
        self.cellStyle = cellStyle
        self.draw_table(self.cellStyle)
    
    # controls bindings via passing SelectionStrategy methods in
    def configure_interaction_mode(self, 
                                   allowDrag=False, 
                                   cellStyle: CellStyleResolver=None,
                                   on_click=None, 
                                   on_drag=None, 
                                   on_release=None):
        self.unbind_all_mouse_events()
        self.cellStyle = cellStyle
        if on_click:
            self.bindings["<Button-1>"] = self.canvas.bind("<Button-1>", on_click)
        if allowDrag and on_drag:
            self.bindings["<B1-Motion>"] = self.canvas.bind("<B1-Motion>", on_drag)
        if on_release:
            self.bindings["<ButtonRelease-1>"] = self.canvas.bind("<ButtonRelease-1>", on_release)
    def unbind_all_mouse_events(self):
        for eventType, bindID in self.bindings.items():
            self.canvas.unbind(eventType, bindID)
        self.bindings.clear()

    # updates table according to style and selection strategy
    def draw_table(self, styleResolver: CellStyleResolver):
        self.canvas.delete("all")
        for (row, col), value in self.data.items():
            # should be uncommented when a solution is found for blending cell styles
            #if (row, col) in styleResolver.strategy.get_locked_cells():
            #    continue
            self.draw_cell(row, col, styleResolver)

    def draw_cell(self, row, col, styleResolver):
        x1 = col * self.cellWidth
        y1 = row * self.cellHeight
        x2 = x1 + self.cellWidth
        y2 = y1 + self.cellHeight
        style = styleResolver.get_cell_style(row, col)
        inset = style.width / 2
        insetRect = [x1 + inset, y1 + inset, x2 - inset, y2 - inset]
        self.canvas.create_rectangle(*insetRect, 
                                        outline=style.outline, 
                                        fill=style.fill, 
                                        width=style.width,
                                        stipple=style.stipple)
        if self.showData:
            value = self.data[(row, col)]
            self.canvas.create_text(x1 + self.cellWidth/2, 
                                    y1 + self.cellHeight/2, 
                                    text=value)


    def cell_from_event(self, event):
        row = event.y // self.cellHeight
        col = event.x // self.cellWidth
        return row, col
    
    def get_pixel_width(self):
        return self.numColumns * self.cellWidth
    
# allows for manual entry of triplicate data and concentrations
class TriplicateGUI:
    def __init__(self, main, plate: ScreeningPlate):
        self.selectedRows = set()
        self.selectedTriplets = set()
        self.assignedTriplets = set()
        self.unusedTriplets = set()
        self.unusedCells = set()
        self.assignedRows = set()
        self.displayEntries = False
        self.selectionStrategy = MultiTripletSelector(self.selectedTriplets,
                                                      self.assignedTriplets)
        self.styleStrategy = HighlightAndLockSelection(self.selectionStrategy)
        self.receptorByRow = 8*[None]
        self.main = main
        self.dataFrame = tk.Frame(self.main)
        self.entryFrame = tk.Frame(self.main)
        self.dataFrame.pack()
        self.dataFrame.pack_propagate
        self.entryFrame.pack()
        self.columns = ["1", "2", "3"]
        self.receptorList = {}
        self.plate = plate
        plateData = plate.data.reset_index(drop=True)
        self.dataDict = {}
        self.nameRequired = True
        self.originalData = {(rowIdx, colIdx): value for rowIdx, row in plateData.iterrows() for colIdx, value in enumerate(row)}
        for rowIdx, row in plateData.iterrows():
            numCols = 4
            for triplicate in range(0, numCols):
                self.dataDict[rowIdx, triplicate] = row.iloc[0 + triplicate*3:3 + triplicate*3].to_list()
                self.plate.screeningDict[rowIdx, triplicate] = ScreeningTriplet()
        self.table = CustomTable(self.dataFrame, 
                                             self.originalData, 
                                             showData=False, 
                                             cellStyle=self.styleStrategy)
        self.table.configure_interaction_mode(allowDrag=True, 
                                              on_click=self.handle_row_click,
                                              on_drag=self.handle_row_drag,
                                              on_release = self.handle_row_release)
        self.selectionRect = None
        self.table.pack(expand=True, fill="both")
        self.tableWidth = self.table.get_pixel_width()
        self.confirmUnusedTriplicatesButton = tk.Button(self.entryFrame,
                                                        text="Confirm unused triplicates",
                                                        command = self.load_receptor_gui)
        self.confirmUnusedTriplicatesButton.pack()
    # bound to mouse 1 when selecting rows for receptors
    def handle_row_click(self, event):
        row, col = self.table.cell_from_event(event)
        self.selectionStrategy.on_click(row, col, event)
        self.table.draw_table(self.styleStrategy)

    def handle_row_drag(self, event):
        row, col = self.table.cell_from_event(event)
        rectCoords = self.selectionStrategy.on_drag(row, col, event)
        self.table.canvas.delete(self.selectionRect)
        self.selectionRect = self.table.canvas.create_rectangle(*rectCoords)

    def handle_row_release(self, event):
        row, col = self.table.cell_from_event(event)
        self.selectionStrategy.on_release(row, col, event)
        self.table.draw_table(self.styleStrategy)
    
    def confirm_unused_area(self):
        for trip in self.selectedTriplets:
            self.unusedTriplets.add(trip)
            self.plate.drugDict[trip] = None
            self.plate.concDict[trip] = None
            self.plate.screeningDict[trip] = None
            selectedCells = [(trip[0], col) for col in range(trip[1]*3, trip[1]*3 + 3)]
            for cell in selectedCells:
                self.unusedCells.add(cell)
            #self.unusedCells.add([(i[0], col) for col in range(i[1], i[1] + 4)])
        self.confirmUnusedTriplicatesButton.pack_forget()

    def load_receptor_gui(self):
        self.confirm_unused_area()
        self.selectedRows = set()
        self.selectedTriplets = set()
        self.assignedTriplets = set()
        self.assignedRows = set()
        for row, idx in enumerate(self.receptorByRow):
            if all([(row, c) in self.unusedCells for c in range(0, 12)]):
                self.assignedRows.add(row)
        self.selectionStrategy = RowSelector(self.selectedRows, self.assignedRows)
        self.styleStrategy = HighlightAndBlockSelection(self.unusedCells, self.selectionStrategy)
        self.table.draw_table(self.styleStrategy)
        self.receptorInfo = ttk.Treeview(self.dataFrame,
                                         columns=("labels"),
                                         height=1)
        self.receptorInfo.heading("#0", text="Receptor Name")
        self.receptorInfo.heading("labels", text="Row Labels")
        self.receptorInfo.column("#0", width=self.tableWidth // 2, stretch=False)
        self.receptorInfo.column("labels", width=self.tableWidth // 2, stretch=False)
        self.receptorInfo.pack(fill="both", expand=True)
        self.receptorEntry = tk.Entry(self.entryFrame)
        self.receptorAddButton = tk.Button(self.entryFrame,
                                           text="Assign receptor",
                                           command = lambda: self.update_receptors(self.receptorEntry.get()))
        self.receptorsConfirmButton = tk.Button(self.entryFrame,
                                                text="Confirm layout",
                                                command=self.assign_receptors,
                                                state='disabled')
        self.receptorRemoveButton = tk.Button(self.entryFrame, 
                                              text="Remove receptor", 
                                              command = self.remove_receptor)
        self.selectAllRowsButton = tk.Button(self.entryFrame,
                                             text="Select all rows",
                                             command=self.select_all_rows)
        self.receptorEntry.grid(row=0, column=0)
        self.receptorAddButton.grid(row=1, column=0)
        self.receptorsConfirmButton.grid(row=1, column=1)
        self.receptorRemoveButton.grid(row=1, column=2)
        self.selectAllRowsButton.grid(row=1, column=3)
        self.receptorsAssigned = False

    # for ease of assigning a whole plate to a receptor
    def select_all_rows(self):
        self.selectedRows.clear()
        for row in range(0, 8):
            if row in self.assignedRows:
                continue
            self.selectedRows.add((row))
        self.table.draw_table(self.styleStrategy)

    # adjust height of receptor Treeview when changed
    def update_treeview(self):
        rowCount = len(self.receptorInfo.get_children()) + 1
        self.receptorInfo.config(height=rowCount)
        
    # assign new rows to a receptor and lock them
    def update_receptors(self, receptorName):
        if receptorName == "" or self.selectedRows == set():
            return
        self.receptorList[receptorName] = self.selectedRows
        self.receptorEntry.delete(0, tk.END)
        rowLetters = [chr(ord('A') + row) for row in self.selectedRows]
        rowString = ', '.join(rowLetters)
        for i in self.selectedRows:
            self.assignedRows.add(i)
            self.receptorByRow[i] = receptorName
        self.update_treeview()
        self.receptorInfo.insert("", 
                                tk.END, 
                                text=receptorName,
                                values=[rowString])
        self.selectedRows.clear()
        self.table.draw_table(self.styleStrategy)
        self.ui_state()

    # remove a receptor assignment and unlock the rows
    def remove_receptor(self):
        curItem = self.receptorInfo.focus()
        itemContents = self.receptorInfo.item(curItem)
        itemRows = itemContents["values"][0]
        receptorName = itemContents["text"]
        rowList = itemRows.split(', ')
        self.receptorList.pop(receptorName)
        for row in rowList:
            rowIdx = ord(row) - ord('A')
            self.assignedRows.remove(rowIdx)
        self.receptorInfo.delete(curItem)
        self.update_treeview()
        self.table.draw_table(self.styleStrategy)
        self.ui_state()

    # allow confirm when all rows are assigned
    def ui_state(self):
        if len(self.assignedRows) == 8:
            self.receptorsConfirmButton["state"] = "normal"
            self.receptorAddButton["state"] = "disabled"
            self.receptorEntry["state"] = "disabled"
        else:
            self.receptorsConfirmButton["state"] = "disabled"
            self.receptorAddButton["state"] = "normal"
            self.receptorEntry["state"] = "normal"

    # confirm receptor assignment and proceed to triplicate
    def assign_receptors(self):
        self.unload_receptor_gui()
        self.assign_weighings()
        
    # remove receptor related gui items, leaving only the Treeview
    def unload_receptor_gui(self):
        self.table.pack_forget()
        self.receptorEntry.grid_forget()
        self.receptorAddButton.grid_forget()
        self.receptorRemoveButton.grid_forget()
        self.receptorsConfirmButton.grid_forget()
        self.selectAllRowsButton.grid_forget()

    def assign_weighings(self):
        self.selectionStrategy = MultiTripletSelector(self.selectedTriplets, self.unusedTriplets)
        self.styleStrategy = HighlightAndBlockSelection(self.unusedCells, self.selectionStrategy)
        self.table = CustomTable(self.dataFrame, 
                                       self.originalData, 
                                       showData=False, 
                                       cellStyle=self.styleStrategy)  
        self.table.pack(expand=True, fill='both')
        self.blueWeighingButton = tk.Button(self.entryFrame,
                                            text="Select blue weighing",
                                            command=self.assign_blue_weighing)
        self.blackWeighingButton = tk.Button(self.entryFrame,
                                             text="Select black weighing",
                                             command=self.assign_black_weighing)
        self.assignWeighingButton = tk.Button(self.entryFrame,
                                              text="Assign experiment",
                                              command=self.confirm_weighing)
        self.labelTriplicatesButton = tk.Button(self.entryFrame,
                                                text="Label triplicates",
                                                command=self.label_data)
        self.blueWeighingButton.grid(row=0, column=0)
        self.blackWeighingButton.grid(row=0, column=1)
        self.assignWeighingButton.grid(row=1, column=0)
        self.labelTriplicatesButton.grid(row=1, column=1)
        
    def assign_blue_weighing(self):
        self.selectionStrategy = MultiTripletSelector(self.selectedTriplets,
                                                      self.assignedTriplets)
        self.styleStrategy = BlueWeighingSelection(self.unusedCells, self.selectionStrategy)
        self.table.configure_interaction_mode(allowDrag=True,
                                              cellStyle=self.styleStrategy,
                                              on_click=self.handle_trip_click,
                                              on_drag=self.handle_trip_drag,
                                              on_release=self.handle_trip_release)
        self.blueWeighingButton["state"] = "disabled"
        self.blackWeighingButton["state"] = "normal"
        self.reset_triplets()
        self.currentWeighing = 'blue'

    def assign_black_weighing(self):
        self.selectionStrategy = MultiTripletSelector(self.selectedTriplets,
                                                      self.assignedTriplets)
        self.styleStrategy = BlackWeighingSelection(self.unusedCells, self.selectionStrategy)
        self.table.configure_interaction_mode(allowDrag=True,
                                              cellStyle=self.styleStrategy,
                                              on_click=self.handle_trip_click,
                                              on_drag=self.handle_trip_drag,
                                              on_release=self.handle_trip_release)
        self.blackWeighingButton["state"] = "disabled"
        self.blueWeighingButton["state"] = "normal"
        self.reset_triplets()
        self.currentWeighing = 'black'

    def confirm_weighing(self):
        for trip in self.selectedTriplets:
            if trip not in self.unusedTriplets:
                self.plate.screeningDict[trip].weighing = self.currentWeighing
        self.reset_triplets()
        self.blackWeighingButton["state"] = "normal"
        self.blueWeighingButton["state"] = "normal"

    def label_data(self):
        self.blueWeighingButton.grid_forget()
        self.blackWeighingButton.grid_forget()
        self.assignWeighingButton.grid_forget()
        self.labelTriplicatesButton.grid_forget()
        self.displayEntries = True
        self.assign_triplicate_info()
        self.dataTree = ttk.Treeview(self.dataFrame, 
                                 columns=self.columns, 
                                 show="headings", 
                                 height=1)
        self.saveTree = ttk.Treeview(self.dataFrame,
                                     columns=("conc", "weigh"),
                                     height=1)
        self.saveTree.heading("#0", text="Drug Name")
        self.saveTree.heading("conc", text="Concentration")
        self.saveTree.heading("weigh", text="Weighing")
        tableWidth = self.table.get_pixel_width()
        self.saveTree.column("#0", width=tableWidth // 3)
        self.saveTree.column("conc", width=tableWidth // 3)
        self.saveTree.column("weigh", width=tableWidth // 3)
        for col in self.columns:
            self.dataTree.heading(col, text=col)
            self.dataTree.column(col, width=tableWidth // len(self.columns), anchor = "center")
        self.dataTree.pack(expand=True, fill='both')
        self.saveTree.pack(expand=True, fill='both')
        self.concentrationVal = tk.IntVar()
        self.radio1 = tk.Radiobutton(self.entryFrame,
                                     text="100 nM",
                                     variable=self.concentrationVal,
                                     value = -7,
                                     command = self.enable_entries)
        self.radio2 = tk.Radiobutton(self.entryFrame,
                                     text="1 μM",
                                     variable=self.concentrationVal,
                                     value = -6,
                                     command = self.enable_entries)
        self.radio3 = tk.Radiobutton(self.entryFrame,
                                     text="10 μM",
                                     variable=self.concentrationVal,
                                     value = -5,
                                     command = self.enable_entries)
        self.radioNSB = tk.Radiobutton(self.entryFrame,
                                     text="Non-specific",
                                     variable=self.concentrationVal,
                                     value = 0,
                                     command = self.disable_entries)
        self.radioTotals = tk.Radiobutton(self.entryFrame,
                                     text="Totals",
                                     variable=self.concentrationVal,
                                     value=1,
                                     command = self.disable_entries)
        self.radio1.grid(row=0, column=0)
        self.radio2.grid(row=0, column=1)
        self.radio3.grid(row=0, column=2)
        self.radioNSB.grid(row=1, column=0, sticky='E')
        self.radioTotals.grid(row=1, column=2, sticky='W')
        self.triplicateLabel = tk.Label(self.entryFrame,
                                        text="Enter drug name:")
        self.triplicateLabel.grid(row=2, column=0)
        self.triplicateEntry = tk.Entry(self.entryFrame)
        self.triplicateEntry.grid(row=2, column=1)
        self.changeButton = tk.Button(self.entryFrame,
                                      text="Save entries",
                                      command=self.cycle_data)
        self.changeButton.grid(row=3, column=0)
        self.screeningCompleteButton = tk.Button(self.entryFrame,
                                                 text="Save data to file",
                                                 command=self.save_triplicate_screening)
        self.screeningCompleteButton.grid(row=3, column=2)
        self.currentKey = (0, 0)
        self.selectedTriplets.add(self.currentKey)
        while self.currentKey in self.unusedTriplets:
            self.select_next_triplicate()
        self.select_triplicate(self.currentKey)
        self.table.draw_table(self.styleStrategy)

    # bound to mouse 1 when selecting triplicates
    def handle_trip_click(self, event):
        row, col = self.table.cell_from_event(event)
        self.selectionStrategy.on_click(row, col, event)
        self.select_triplicate((row, col // 3))
        self.table.draw_table(self.styleStrategy)

    def handle_trip_drag(self, event):
        row, col = self.table.cell_from_event(event)
        rectCoords = self.selectionStrategy.on_drag(row, col, event)
        self.table.draw_table(self.styleStrategy)
        self.selectionRect = self.table.canvas.create_rectangle(*rectCoords)

    def handle_trip_release(self, event):
        row, col = self.table.cell_from_event(event)
        self.selectionStrategy.on_release(row, col, event)
        self.table.draw_table(self.styleStrategy)     
   
    def assign_triplicate_info(self):
        self.selectedTriplets = set()
        self.selectionStrategy = SingleTripletSelector(self.selectedTriplets, self.unusedTriplets)
        self.styleStrategy = HighlightAndBlockSelection(self.unusedCells, self.selectionStrategy)
        self.table.configure_interaction_mode(allowDrag=False, 
                                              cellStyle=self.styleStrategy,
                                              on_click=self.handle_trip_click,
                                              on_drag=self.handle_trip_drag,
                                              on_release=self.handle_trip_release)
        self.reset_triplets()

    def reset_triplets(self):
        self.selectedTriplets.clear()
        self.table.draw_table(self.styleStrategy)

    # used if there is a concentration of drug
    def enable_entries(self):
        self.nameRequired = True
        self.triplicateEntry["state"] = "normal"

    # used for totals and non-specific
    def disable_entries(self):
        self.nameRequired = False
        self.triplicateEntry["state"] = "disabled"

    # cycle selection to next trip without checking for unused trips
    def select_next_triplicate(self):
        rowIdx = self.currentKey[0]
        tripIdx = self.currentKey[1]
        if tripIdx >= 3:
            tripIdx = 0
            rowIdx += 1
        else:
            tripIdx += 1
        if rowIdx > 7:
            rowIdx = 0
        self.currentKey = (rowIdx, tripIdx)
        self.selectedTriplets.clear()
        self.selectedTriplets.add(self.currentKey)

    # adds entered information to table and selects next triplicate
    def cycle_data(self):
        if not self.update_current_triplicate():
            return
        self.select_next_triplicate()
        while not self.select_triplicate(self.currentKey):
            self.select_next_triplicate()
        self.table.draw_table(self.styleStrategy)
        self.screening_calculation()
        self.enable_entries()

    # fetch data for triplet and show in Treeview, filtering out unused trips
    def select_triplicate(self, key):
        if key not in self.dataDict.keys():
            return False
        if key in self.unusedTriplets:
            return False
        if not self.displayEntries:
            return False
        self.currentKey = key
        tripData = self.dataDict[self.currentKey]
        self.triplicateEntry.delete(0, tk.END)
        self.concentrationVal.set(None)
        for row in self.dataTree.get_children():
            self.dataTree.delete(row)
        for row in self.saveTree.get_children():
            self.saveTree.delete(row)
        self.dataTree.insert("", "end", values=tripData)
        if self.currentKey in self.plate.concDict and self.currentKey in self.plate.drugDict:
            self.saveTree.insert("", "end", 
                                 text=self.plate.drugDict[self.currentKey],
                                 values=[self.plate.concDict[self.currentKey], self.plate.screeningDict[self.currentKey].weighing])
        return True
    
    # confirmation of proper field entries in cycle_data
    def update_current_triplicate(self):
        if self.nameRequired:
            drugName = self.triplicateEntry.get()
        else:
            drugName = "None"
        if drugName == "":
            print("Enter a drug name")
            return 0
        try:
            concVal = self.concentrationVal.get()
        except:
            print("Select a concentration")
            return 0
        try:
            concVal = self.concentrationVal.get()
        except:
            concVal = None
        match(concVal):
            case 0:
                concVal = "Non Specific"
            case 1:
                concVal = "Totals"
        self.plate.drugDict[self.currentKey] = drugName
        self.plate.concDict[self.currentKey] = concVal
        self.plate.screeningDict[self.currentKey].receptor = self.receptorByRow[self.currentKey[0]]
        self.plate.screeningDict[self.currentKey].drug = drugName
        self.plate.screeningDict[self.currentKey].concentration = concVal
        self.plate.screeningDict[self.currentKey].plate = self.plate.metadata.plateNo
        return 1

    def save_triplicate_screening(self):
        dateStr = self.plate.metadata.date
        plateNo = self.plate.metadata.plateNo
        if not all(x in self.plate.drugDict for x in self.dataDict):
            print("Incomplete")
        for key, metadata in self.plate.screeningDict.items():
            if metadata is None:
                continue
            #print(f"Unique triplet hash: {'|'.join([dateStr,plateNo,key,metadata.weighing])}")
        io.save_new_screening_plate(self.plate, r"E:/Test/test.h5")

    # deprecated but right idea - logic needs to move to h5/json/external storage
    # need a good way to divide experiments by identifiers
    def screening_calculation(self):
        if not all(x in self.plate.drugDict for x in self.dataDict):
            return
        results = {}
        averages = {}
        sem = {}
        nonSpecific = {receptor: [] for receptor in self.receptorList}
        totals = {receptor: [] for receptor in self.receptorList}
        for key, drugName in self.plate.drugDict.items():
            conc = self.plate.concDict[key]
            data = self.dataDict[key]
            receptor = self.receptorByRow[key[0]]
            if receptor not in results:
                results[receptor] = {}
                averages[receptor] = {}
                sem[receptor] = {}
            if drugName not in results[receptor]:
                results[receptor][drugName] = {}
                averages[receptor][drugName] = {}
                sem[receptor][drugName] = {}
            if conc not in results[receptor][drugName]:
                results[receptor][drugName][conc] = []
            results[receptor][drugName][conc].append([val for val in data])
        print(f"All data: {results}")
        for receptor, drugs in results.items():
            for drugName, concentrations in drugs.items():
                if drugName == "None":
                    print(concentrations)
                    nonSpecific[receptor] = np.mean(concentrations["Non Specific"])
                    totals[receptor] = np.mean(concentrations["Totals"])
                    continue
                for conc, values in concentrations.items():
                    averages[receptor][drugName][conc] = np.mean(values)
                    sem[receptor][drugName][conc] = np.std(values)/np.sqrt(len(values))
        print(f"Non-Specific: {nonSpecific}")
        print(f"Totals: {totals}")
        print(f"Averages: {averages}")
        print(f"SEM: {sem}")
        for key in self.plate.screeningDict:
            tripletObj = self.plate.screeningDict[key]
            if tripletObj is not None:
                print(f"Row {key[0] + 1}, Col {key[1] + 1}: {tripletObj}")
                
# guitools for displaying and manipulating new and saved BindingPlate        
class BindingPlateGUI:
    def __init__(self, main, plate):
        self.main = main
        self.dataFrame = tk.Frame(self.main)
        self.entryFrame = tk.Frame(self.main)
        self.plate = plate
        plateData = plate.data.reset_index(drop=True)
        dataDict = {(rowIdx, colIdx): value for rowIdx, row in plateData.iterrows() for colIdx, value in enumerate(row)}

        self.dataFrame.pack(fill="both", expand="yes")
        self.entryFrame.pack(fill="both", expand="yes")
        self.selectedCells = set()
        self.assignedCells = set()
        self.selectionStrategy = MultiCellSelector(self.selectedCells, self.assignedCells)
        self.styleStrategy = HighlightAndLockSelection(self.selectionStrategy)
        self.table = CustomTable(self.dataFrame, 
                                             dataDict, 
                                             showData=True, 
                                             cellStyle=self.styleStrategy)
        self.table.canvas.bind("<Button-1>", self.handle_click)
        self.table.pack(expand=True, fill='both')
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
        colWidth = self.table.cellWidth
        totalWidth = numCols * colWidth
        colHeight = self.table.cellHeight
        totalHeight = numRows * colHeight
        self.dataFrame.height = totalHeight
        self.main.geometry(f"{totalWidth}x500")

    def handle_click(self, event):
        row, col = self.table.cell_from_event(event)
        self.selectionStrategy.on_click(row, col)
        self.table.draw_table(self.styleStrategy)

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

# used to create excel templates for assays
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
