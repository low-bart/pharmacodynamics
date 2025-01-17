import tkinter as tk
from tkinter import Event, ttk
from tkintertable import TableCanvas, TableModel
from PharmOps import WellData
from PharmOps import io
import pandas as pd
import h5py



def read_WellData(filepath):
    rawData = pd.read_excel(filepath)
    loadedData = WellData(rawData)
    return loadedData


def initialize_GUI():



    # root properties
    defaultH5Path = io.get_default_h5_path()
    root = tk.Tk()
    root.title("Pharmacodynamics GUI")
    root.geometry("300x200")
    appStyle = ttk.Style()
    appStyle.configure("Custom.TFrame", background="lightblue")
    topFrame = ttk.Frame(root, style="Custom.TFrame")
    topFrame['borderwidth'] = 10
    topFrame['relief'] = 'groove'
    topFrame.grid(row=0, column=0, sticky="N, S, E, W", padx=5, pady=5)
    bottomFrame = ttk.Frame(root, style="Custom.TFrame")
    bottomFrame['borderwidth'] = 10
    bottomFrame['relief'] = 'groove'
    bottomFrame.grid(row=1, column=0, sticky="N, S, E, W", padx=5, pady=5)


    addButton = ttk.Button(root, text="Add new well data", command=lambda: load_WellData_GUI('sample data\\Binding Template for RAW transformations.xlsx'))
    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(0, weight=1)
    addButton.grid(row=0, column=0)

    loadButton = ttk.Button(root, text="Load saved DrugReports", command=lambda: view_DrugReports_GUI(defaultH5Path))
    root.grid_rowconfigure(1, weight=1)
    loadButton.grid(row=1, column=0)

    root.mainloop()


def create_drug_entry(currentObj, parent, labelText, row, entryNo, callback):
    entryVar = tk.StringVar()
    entryVar.trace_add("write", lambda var=entryVar, idx=None, mode=None, index=row-1: callback(index, var, idx, mode))
    print(f"Created entryVar for row {row}, trace added.")

    label = ttk.Label(parent, text=labelText)
    label.grid(row=row, column=(entryNo*2)-2, padx=5, pady=5, sticky="E")

    entry = ttk.Entry(parent, textvariable=entryVar)
    entry.grid(row=row, column=(entryNo*2)-1, padx=5, pady=5, sticky="W")
    return entry

def make_drug_reports(root, obj, drugEntries, receptor):
    for i, entry in enumerate(drugEntries):
        obj.update_drugs(entry.get(), i)
    obj.metadata.receptor = receptor.get()
    reports = obj.make_all_drug_reports()
    h5Path = io.get_default_h5_path()
    print(h5Path)
    for report in reports:
        io.save_new_h5(report, h5Path)
        print(report.drug)
        print(report.metadata.receptor)

def load_WellData_GUI(filepath):
    # root properties
    root = tk.Tk()
    root.title("Load new well plate data")

    # WellData
    currentObj = read_WellData('sample data\\Binding Template for RAW transformations.xlsx')
    dataDict = currentObj.data.to_dict(orient='index')
    dataDict = {row_key: {str(col_key): value for col_key, value in col_values.items()} 
            for row_key, col_values in dataDict.items()}
    model = TableModel()
    model.importDict(dataDict)

    # Create a table canvas and set it to editable
    tableFrame = tk.Frame(root)
    tableFrame.grid(row=0, column=0, columnspan=4)
    #tableFrame.pack(fill=tk.BOTH, expand=True)

    # Create a table model
    model = TableModel()
    model.importDict(dataDict)
    # Create a table canvas inside the frame and set it to editable
    table = TableCanvas(tableFrame, model=model, read_only=False)
    table.show()
    drugLabels = ["Drug 1: ", "Drug 2: ", "Drug 3: ", "Drug 4: "]
    drugEntries = []
    concentrationLabels = ["Highest concentration 1: ", "Highest concentration 2: ", "Highest concentration 3: ", "Highest concentration 4: "]
    concentrationEntries = []
    def on_drug_change(index, var, idx, mode):
        print("Drug change detected")
        currentObj.update_drugs(index, var.get())
        print(currentObj.drugs)
    
    def on_conc_change(index, var, idx, mode):
        currentObj.update_conc(index, var.get())

    for i, labelText in enumerate(drugLabels):
        drugEntry = create_drug_entry(currentObj, root, labelText, i + 1, 1, on_drug_change)
        drugEntries.append(drugEntry)

    for i, labelText in enumerate(concentrationLabels):
        concEntry = create_drug_entry(currentObj, root, labelText, i + 1, 2, on_conc_change)
        concentrationEntries.append(concEntry)

    receptorLabel = ttk.Label(root, text="Receptor name: ")
    receptorLabel.grid(row=5, column=1, sticky="E")
    receptorName = ttk.Entry(root)
    receptorName.grid(row=5, column=2, sticky="W")
    makeReportButton = ttk.Button(root, text="Make new drug reports", command=lambda: make_drug_reports(root, currentObj, drugEntries, receptorName))

    makeReportButton.grid(row=6, column=2)
    def on_cell_edit(event=None):
        """
        Persist the updated value after editing a cell.
        """
        if table.currentrow is not None and table.currentcol is not None:
            row = table.currentrow  # Get the current row index
            col = table.currentcol  # Get the current column index

            # Retrieve the value from the Entry widget
            if table.cellentry is not None:
                updated_value = table.cellentry.get().strip()  # Use .strip() to clean up spaces

                if updated_value:  # Only process non-empty values
                    # Save the updated value to the model
                    model.setValueAt(updated_value, row, col)

                    # Debug print
                    print(f"Cell [{row}, {col}] updated to: {updated_value}")

                    # Redraw the table to reflect the changes
                    table.redraw()

    def bind_edit_events():
        """
        Attach FocusOut and Return bindings to the Entry widget used for editing cells.
        """
        if table.cellentry is not None:
            # Bind FocusOut to handle when the user leaves the cell
            table.cellentry.bind("<FocusOut>", on_cell_edit)

            # Bind Return (Enter key) to commit the edit
            table.cellentry.bind("<Return>", on_cell_edit)

    # Override table's `drawCellEntry` to attach bindings after creating the cell editor
    original_drawCellEntry = table.drawCellEntry

    def drawCellEntryOverride(row, col):
        original_drawCellEntry(row, col)
        bind_edit_events()

    table.drawCellEntry = drawCellEntryOverride
    root.mainloop()



def view_DrugReports_GUI(filepath):
    root = tk.Tk()
    root.title("Browse DrugReports")
    root.geometry("625x300")
    mainframe = ttk.Frame(root)
    mainframe['borderwidth'] = 10
    mainframe['relief'] = 'raised'
    mainframe.grid(row=0, column=0, sticky="N, S, E, W", padx=5, pady=5)
    root.grid_rowconfigure(0, weight=1)
    with h5py.File(filepath, "r") as f:
        alist = []
        ls = list(f.keys())
        print('List of datasets: \n', ls)
        clicked = tk.StringVar() 
    
        # initial menu text 
        clicked.set("Select a drug: ")
        
        clicked2 = tk.StringVar()
        clicked2.set("Select a receptor: ")

        # Create Dropdown menu 
        drugLabel = tk.Label(root, text="Select a drug: ")
        drugLabel.grid(row=0, column=0, sticky="E")
        drop = tk.ComboBox(root, clicked, *ls, command=lambda value: drug_selected(clicked, filepath)) 
        drop.grid(row=0, column=2, sticky="W") 
        receptorLabel = tk.Label(root, text="Select a receptor: ")
        receptorLabel.grid(row=1, column=0, sticky="E")
        drop2 = tk.OptionMenu(root, clicked2, *list(f[clicked].keys()), command=lambda value: receptor_selected(clicked.get(), clicked2, filepath))
        drop2.grid(row=1, column=2, sticky="W")
    root.mainloop()
          
def drug_selected(selectedVal, h5File):
    with h5py.File(h5File, "r") as f:
        ls = list(f.keys())
        print(ls)
        receptorsTested = list(f[selectedVal.get()].keys())
        print(receptorsTested)

def receptor_selected(selectedDrug, selectedReceptor, h5File):
    with h5py.File(h5File, "r") as f:
        ls = list(f[selectedDrug].keys())
        print(ls)

def on_cell_click(event, table):
    # Get the clicked cell position (row, col)
    row_clicked = table.get_row_clicked(event)
    
    # Ensure the row is within bounds
    if row_clicked is None:
        print("Click was outside table rows.")
        return
    
    # Retrieve column names
    column_names = table.model.columnNames
    num_columns = len(column_names)
    
    # Calculate which column was clicked
    col_width = table.cellwidth
    x_position = event.x
    col_clicked = x_position // col_width  # Determine column index
    
    # Ensure the column index is within bounds
    if 0 <= col_clicked < num_columns:
        col_name = column_names[col_clicked]
        print(f"Row: {row_clicked}, Column: {col_clicked} ({col_name})")
        
        # Fetch the value using the column name
        cell_value = table.model.data[row_clicked][col_name]
        print(f"Cell Value: {cell_value}")
    else:
        print("Click was outside table columns.")
  