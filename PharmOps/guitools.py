import tkinter as tk
from tkinter import ttk
import pandas as pd
import PharmOps

def read_WellData(filepath):
    rawData = pd.read_excel(filepath)
    loadedData = PharmOps.WellData(rawData)
    return loadedData


def initialize_GUI():
    # root properties
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

    loadButton = ttk.Button(root, text="Load saved DrugReports")
    root.grid_rowconfigure(1, weight=1)
    loadButton.grid(row=1, column=0)

    root.mainloop()

def load_WellData_GUI(filepath):
    # root properties
    root = tk.Tk()
    root.title("Load new well plate data")
    root.geometry("625x300")
    mainframe = ttk.Frame(root)
    mainframe['borderwidth'] = 10
    mainframe['relief'] = 'raised'
    mainframe.grid(row=0, column=0, sticky="N, S, E, W", padx=5, pady=5)
    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(0, weight=1)
    # WellData
    currentObj = read_WellData('sample data\\Binding Template for RAW transformations.xlsx')
    tree = ttk.Treeview(mainframe, columns=list(currentObj.data.columns), show="headings")
    tree.grid(row=0, column=0, sticky="N, S, E, W")

    for col in currentObj.data.columns:
        tree.heading(col, text=col)
        tree.column(col, width=100, anchor=tk.CENTER)

    for _, row in currentObj.data.iterrows():
        tree.insert("", tk.END, values=list(row))

    mainframe.grid_rowconfigure(0, weight=1)
    mainframe.grid_columnconfigure(0, weight=1)

    scroll_x = ttk.Scrollbar(mainframe, orient=tk.HORIZONTAL, command=tree.xview)
    scroll_x.grid(row=1, column=0, sticky="E, W")
    scroll_y = ttk.Scrollbar(mainframe, orient=tk.VERTICAL, command=tree.yview)
    scroll_y.grid(row=0, column=1, sticky="N, S")

    tree.configure(xscrollcommand=scroll_x.set, yscrollcommand=scroll_y.set)

    label = ttk.Label(root, text="more text")
    label.grid(row=1, column=0, sticky="W", padx=5, pady=5)

    button = ttk.Button(root, text="Click me")
    button.grid(row=2, column=0, sticky="W", padx=5, pady=5)
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