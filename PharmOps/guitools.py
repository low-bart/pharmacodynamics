import tkinter as tk
from tkinter import ttk
import pandas as pd
import PharmOps

def load_WellData(filepath):
    rawData = pd.read_excel(filepath)
    loadedData = PharmOps.WellData(rawData)
    return loadedData


def initialize_GUI(filepath):
    # root properties
    root = tk.Tk()
    root.title("Pharmacodynamics GUI")
    root.geometry("625x300")
    mainframe = ttk.Frame(root)
    mainframe['borderwidth'] = 10
    mainframe['relief'] = 'sunken'
    mainframe.grid(row=0, column=0, sticky="N, S, E, W", padx=5, pady=5)
    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(0, weight=1)
    # WellData
    currentObj = load_WellData('sample data\\Binding Template for RAW transformations.xlsx')
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