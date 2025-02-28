import numpy as np
from tkinter import messagebox, filedialog
import openpyxl as pxl
import re

class AssayMetadata:
    date = []
    ctr = []
    plate = []
    receptor = []
    h5Path = []
    rawDataPath = []

    def __init__(self):
        pass

    def display(self):
        print(self.date)
        print(self.ctr)
        print(self.receptor)
        print(self.h5Path)
        print(self.rawDataPath)

class WellData:
    metadata = AssayMetadata()
    drugs = []                  # list of drugs on plate, one per two rows
    comments = []               # list
    data = []                   # well plate data
    totals = []                 # well plate totals with no drug
    nsb = []                    # well plate non-specific binding
    highestConc = []            # log [drug]
    plateNo = []                # plate number from original assay
    specificActivityCi = []     # concentration entered by user
    specificActivityCpm = []    # concentration converted  
    volMl = []                  # volume of radioactive ligand added
    omittedVals = []            # list of values from original well data that are omitted by user selection
    def __init__(self, df, plate=1):
        if df.size == 96:
            self.data = df
        else:
            self.data = df.loc[df.index[0:8], [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]]
        self.drugs = ["Drug1", "Drug2", "Drug3", "Drug4"]
        self.highestConc = [None, None, None, None]
        plateTotals = self.data.loc[self.data.index[0:8], [1, 12]]
        self.totals = np.average(plateTotals)
        plateNSB = self.data.loc[self.data.index[0:8], 2]
        self.nsb = np.average(plateNSB) 
        self.plateNo = plate

    def display(self):
        print(self.data)
        for c in self.comments:
            print(c)
        for d in self.drugs:
            print(d)

    def add_comment(self, comment):
        self.comments.append(comment)

    def make_drug_report(self, index):
        return DrugReports(self, index)
    
    def make_all_drug_reports(self):
        reports = []
        for i in range(4):
            reports.append(DrugReports(self, i))
        return reports

    def update_drugs(self, drugName, idx):
        self.drugs[idx] = drugName

    def update_conc(self, highestConc, idx):
        self.highestConc[idx] = highestConc

    def update_receptor(self, receptorName):
        self.metadata.receptor = receptorName

    def set_date(self, dateStr):
        self.metadata.date = dateStr



class DrugReports:
    metadata = AssayMetadata()
    drug = []
    average = []
    specific = []
    concentration = []
    logConc = []
    pctTotal = []
    averageSpecific = []
    specificBound = []
    pctSpecificBinding = []
    omittedVals = []

    def __init__(self, wellData, index):
        self.drug = wellData.drugs[index]
        self.metadata = wellData.metadata
        startRow = (index) * 2
        endRow = startRow + 2
        drugData = wellData.data.iloc[startRow:endRow]
        self.averageSpecific = np.average(wellData.totals)
        testData = drugData.loc[drugData.index[:], [3, 4, 5, 6, 7, 8, 9, 10, 11]].values
        self.average = [testData.mean(axis=0)]
        self.specific = [x - wellData.nsb for x in self.average]
        self.specificBound = wellData.totals - wellData.nsb
        self.pctTotal = [x * 100 / self.specificBound for x in self.specific]
        concentrationSteps = np.linspace(0, -4, num=9, endpoint=True)
        self.logConc = concentrationSteps + wellData.highestConc[index]
        concCalc = lambda x: 10 ** x
        self.concentration = concCalc(self.logConc)
        self.average = self.average[0].tolist()
        self.specific = self.specific[0].tolist()
        self.pctTotal = self.pctTotal[0].tolist()

class SummaryTable:
    receptors = ["D1", "D2", "D3", "D4", 
                 "5HT1A", "5HT2A", "5HT2B", "5HT2C"]
    bindingColumns = ["IC50", "Ki", "Hill Slope"]
    functionColumns = ["Agonist EC50", "Standard Agonist", "Percent Stimulation", 
                       "Antagonist IC50", "Standard Antagonist", "Percent Inhibition"]
    srcDir = []
    summary = {}

    def __init__(self, dir):
            self.srcDir = dir
            self.import_binding_data()
            self.import_function_data()

    def find_excel_header(self, row, header):
        indices = [i for i, item in enumerate(row) if isinstance(item, str) and re.search(header, item, re.IGNORECASE)]
        return indices

    def import_binding_data(self):
        loadMorePrompt = True
        while loadMorePrompt:
            fileName = filedialog.askopenfilename(initialdir=r"e:/pharmacodynamics/sample data")
            workbook = pxl.load_workbook(fileName, data_only=True)
            self.parse_binding_table(workbook)
            loadMorePrompt = messagebox.askyesno("Load more binding data?")

    def parse_binding_table(self, workbook):
        for name in workbook.sheetnames:
            matchingReceptor = [isinstance(item, str) and re.search(item, name, re.IGNORECASE) for item in self.receptors]
            if not any(matchingReceptor):
                print(f"No matching receptor found for workbook page {name}")
                continue
            self.parse_binding_summary_sheet(workbook, name)
        
    def parse_binding_summary_sheet(self, workbook, receptor):
        sheet = workbook[receptor]
        for idx, row in enumerate(sheet.iter_rows(values_only=True)):
            ic50 = self.find_excel_header(row, "ic50")
            ki = self.find_excel_header(row, "ki")
            hillSlope = self.find_excel_header(row, "hill slope")
            if ic50 and ki and hillSlope:
                drugID = row[0]
                if not drugID:
                    temp = idx
                while not drugID:
                    temp = temp-1
                    drugID = sheet.cell(row = temp+1, column=1).value
                if drugID not in self.summary:
                    self.summary[drugID] = {}
                self.summary[drugID][receptor] = {
                    "mean": {"ic50": None, "ki": None, "hillSlope": None},
                    "sem": {"ic50": None, "ki": None, "hillSlope": None}
                }
                # relative average and sem indexing to the cells with the datatype's header
                ic50Average = sheet.cell(row=idx+2, column=ic50[0]+2).value
                ic50SEM = sheet.cell(row=idx+2, column=ic50[0]+3).value
                kiAverage = sheet.cell(row=idx+2, column=ki[0]+2).value
                kiSEM = sheet.cell(row=idx+2, column=ki[0]+3).value
                hillAverage = sheet.cell(row=idx+2, column=hillSlope[0]+2).value
                hillSEM = sheet.cell(row=idx+2, column=hillSlope[0]+3).value
                self.summary[drugID][receptor]["mean"]["ic50"] = ic50Average
                self.summary[drugID][receptor]["sem"]["ic50"] = ic50SEM
                self.summary[drugID][receptor]["mean"]["ki"] = kiAverage
                self.summary[drugID][receptor]["sem"]["ki"] = kiSEM
                self.summary[drugID][receptor]["mean"]["hillSlope"] = hillAverage
                self.summary[drugID][receptor]["sem"]["hillSlope"] = hillSEM

    def import_function_data(self):
        loadMorePrompt = True
        while loadMorePrompt:
            fileName = filedialog.askopenfilename(initialdir=r"e:/pharmacodynamics/sample data")
            workbook = pxl.load_workbook(fileName, data_only=True)
            self.parse_function_table(workbook)
            loadMorePrompt = messagebox.askyesno("Load more binding data?")


    def parse_function_table(self, workbook):
        for name in workbook.sheetnames:
            matchingReceptor = [isinstance(item, str) and re.search(item, name, re.IGNORECASE) for item in self.receptors]
            if not any(matchingReceptor):
                print(f"No matching receptor found for workbook page {name}")
                continue
            self.parse_function_summary_sheet(workbook, name)

    def parse_function_summary_sheet(self, workbook, receptor):
        sheet = workbook[receptor]
        for idx, row in enumerate(sheet.iter_rows(values_only=True)):
            ec50 = self.find_excel_header(row, "ec50")
            if ec50:
                drugID = row[0]
                if not drugID:
                    temp = idx
                while not drugID:
                    temp = temp-1
                    drugID = sheet.cell(row=temp+1, column=1).value