import numpy as np
from tkinter import messagebox, filedialog
import openpyxl as pxl
import re
import matplotlib.pyplot as plt
import pandas as pd

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
                 "1A", "2A", "2B", "2C"]
    bindingColumns = ["IC50", "Ki", "Hill Slope"]
    functionColumns = ["Agonist EC50", "Standard Agonist", "Percent Stimulation", 
                       "Antagonist IC50", "Standard Antagonist", "Percent Inhibition"]
    srcDir = []
    summary = {}

    def __init__(self, dir):
            self.srcDir = dir
            self.import_binding_data()
            self.import_function_data()

    def add_receptor(self, drugID, receptor):
        if drugID not in self.summary:
            self.summary[drugID] = {}
        if receptor not in self.summary[drugID]:
            self.summary[drugID][receptor] = {
                "mean": {
                    "binding":{"ic50": None, "ki": None, "hillSlope": None},
                    "function":{"ec50": None, "pctStim": None, "ic50": None, "pctInhib": None}
                    },
                "sem": {
                    "binding":{"ic50": None, "ki": None, "hillSlope": None},
                    "function":{"ec50": None, "pctStim": None, "ic50": None, "pctInhib": None}
                    }
            }

    def find_excel_header(self, row, header):
        indices = [i for i, item in enumerate(row) if isinstance(item, str) and re.search(header, item, re.IGNORECASE)]
        return indices
    
    def find_drug_name(self, sheet, idx):
        drugID = sheet.cell(row = idx+1, column=1).value
        if not drugID:
            temp = idx
        while not drugID:
            temp = temp-1
            drugID = sheet.cell(row = temp+1, column=1).value
        
        drugID = str(drugID).splitlines()
        return drugID[0]

    def round_sig(self, x, sigFigs):
        print(x)
        if not x or x=="#DIV/0!" or x=='#VALUE!':
            return '0'
        rounded = '{:g}'.format(float('{:.{p}g}'.format(x, p=sigFigs)))
        if len(rounded) < sigFigs and '.' not in rounded:
            rounded = rounded + '.'
        while len(rounded) <= sigFigs and '.' in rounded:
            rounded = rounded + '0'
        return rounded
    
    def import_binding_data(self):
        loadMorePrompt = True
        while loadMorePrompt:
            fileName = filedialog.askopenfilename(initialdir=self.srcDir)
            workbook = pxl.load_workbook(fileName, data_only=True)
            self.parse_binding_table(workbook)
            loadMorePrompt = messagebox.askyesno("Load more binding data?")

    def parse_binding_table(self, workbook):
        for name in workbook.sheetnames:
            matchingReceptor = [isinstance(item, str) and re.search(item, name, re.IGNORECASE) for item in self.receptors]
            if not any(matchingReceptor):
                print(f"No matching receptor found for workbook page {name}")
                continue
            receptorName = [self.receptors[i] for i, match in enumerate(matchingReceptor) if match]
            sheet = workbook[name]
            receptorName = receptorName[0]
            if type(receptorName) is not str:
                receptorName = str(receptorName)
            self.parse_binding_summary_sheet(sheet, receptorName)
        
    def parse_binding_summary_sheet(self, sheet, receptor):
        for idx, row in enumerate(sheet.iter_rows(values_only=True)):
            ic50 = self.find_excel_header(row, "ic50")
            ki = self.find_excel_header(row, "ki")
            hillSlope = self.find_excel_header(row, "hill slope")
            if ic50 and ki and hillSlope:
                drugID = self.find_drug_name(sheet, idx)
                self.add_receptor(drugID, receptor)
                # relative average and sem indexing to the cells with the datatype's header
                ic50Average = sheet.cell(row=idx+2, column=ic50[0]+2).value
                ic50SEM = sheet.cell(row=idx+2, column=ic50[0]+3).value
                kiAverage = sheet.cell(row=idx+2, column=ki[0]+2).value
                kiSEM = sheet.cell(row=idx+2, column=ki[0]+3).value
                hillAverage = sheet.cell(row=idx+2, column=hillSlope[0]+2).value
                hillSEM = sheet.cell(row=idx+2, column=hillSlope[0]+3).value
                self.summary[drugID][receptor]["mean"]["binding"]["ic50"] = ic50Average
                self.summary[drugID][receptor]["sem"]["binding"]["ic50"] = ic50SEM
                self.summary[drugID][receptor]["mean"]["binding"]["ki"] = kiAverage
                self.summary[drugID][receptor]["sem"]["binding"]["ki"] = kiSEM
                self.summary[drugID][receptor]["mean"]["binding"]["hillSlope"] = hillAverage
                self.summary[drugID][receptor]["sem"]["binding"]["hillSlope"] = hillSEM

    def make_binding_summary_tables(self):
        meanPrecision = 3
        semPrecision = 2
        for drug, nestedDict in self.summary.items():
            print(f"Drug: {drug}")
            df = pd.DataFrame()
            df['Receptor'] = list(self.summary[drug].keys())
            ic50 = []
            ki = []
            hillSlope = []
            for subKey, values in nestedDict.items():
                if isinstance(values, dict):
                    meanVals = values['mean']['binding']
                    semVals = values['sem']['binding']
                    combinedVals = {}
                    for meanKey, semKey in zip(meanVals.keys(), semVals.keys()):
                        outputStr = f"{self.round_sig(meanVals[meanKey], meanPrecision)} ± {self.round_sig(semVals[semKey], semPrecision)}"
                        match(meanKey):
                            case('ic50'):
                                ic50.append(outputStr)
                            case('ki'):
                                ki.append(outputStr)
                            case('hillSlope'):
                                hillSlope.append(outputStr)
            df['IC₅₀ (nM) ± SEM'] = ic50
            df['Ki (nM) ± SEM'] = ki
            df['Hill Slope ± SEM'] = hillSlope
            fig, ax = plt.subplots()
            table = ax.table(cellText=df.values,
                        colLabels=df.columns,
                        loc='center',
                        cellLoc='center')
            table.auto_set_font_size(False)
            table.set_fontsize(12)
            ax.set_axis_off()
            plt.tight_layout()
            plt.savefig(f'..\sample data\{drug}_binding_table.png', bbox_inches='tight')

    def import_function_data(self):
        loadMorePrompt = True
        while loadMorePrompt:
            fileName = filedialog.askopenfilename(initialdir=self.srcDir)
            workbook = pxl.load_workbook(fileName, data_only=True)
            workbook.name = fileName
            self.parse_function_table(workbook)
            loadMorePrompt = messagebox.askyesno("Load more function data?")


    def parse_function_table(self, workbook):
        matchingFilename = [isinstance(item, str) and re.search(item, workbook.name, re.IGNORECASE) for item in self.receptors]
        for name in workbook.sheetnames:
            print(name)
            matchingReceptor = [isinstance(item, str) and re.search(item, name, re.IGNORECASE) for item in self.receptors]
            if not any(matchingReceptor) and not any(matchingFilename):
                print(f"No matching receptor found for workbook page {name}")
                continue
            if any(matchingFilename) and sum(1 for item in matchingFilename if item is not None):
                receptorName = [self.receptors[i] for i, match in enumerate(matchingFilename) if match]
            elif any(matchingReceptor):
                receptorName = [self.receptors[i] for i, match in enumerate(matchingReceptor) if match]
            sheet = workbook[name]
            receptorName = receptorName[0]
            if type(receptorName) is not str:
                receptorName = str(receptorName)
            self.parse_function_summary_sheet(sheet, receptorName)

    def parse_function_summary_sheet(self, sheet, receptor):
        print(receptor)
        for idx, row in enumerate(sheet.iter_rows(values_only=True)):
            ec50 = self.find_excel_header(row, "ec50")
            ic50 = self.find_excel_header(row, "ic50")
            pctVal = self.find_excel_header(row, "%")
            ave = self.find_excel_header(row, "ave")
            sem = self.find_excel_header(row, "sem")
            if (ec50 or ic50) and ave and sem:
                drugID = self.find_drug_name(sheet, idx)
                self.add_receptor(drugID, receptor)
            if ec50 and ave and sem:
                # relative average and sem indexing to the cells with the datatype's header
                ec50Average = sheet.cell(row=idx+2, column=ec50[0]+2).value
                ec50SEM = sheet.cell(row=idx+2, column=ec50[0]+3).value
                pctStimAverage = sheet.cell(row=idx+2, column=pctVal[0]+2).value
                pctStimSEM = sheet.cell(row=idx+2, column=pctVal[0]+3).value
                self.summary[drugID][receptor]["mean"]["function"]["ec50"] = ec50Average
                self.summary[drugID][receptor]["sem"]["function"]["ec50"] = ec50SEM
                self.summary[drugID][receptor]["mean"]["function"]["pctStim"] = pctStimAverage
                self.summary[drugID][receptor]["sem"]["function"]["pctStim"] = pctStimSEM
            elif ic50 and ave and sem:
                # relative average and sem indexing to the cells with the datatype's header
                ic50Average = sheet.cell(row=idx+2, column=ic50[0]+2).value
                ic50SEM = sheet.cell(row=idx+2, column=ic50[0]+3).value
                pctInhibAverage = sheet.cell(row=idx+2, column=pctVal[0]+2).value
                pctInhibSEM = sheet.cell(row=idx+2, column=pctVal[0]+3).value
                self.summary[drugID][receptor]["mean"]["function"]["ic50"] = ic50Average
                self.summary[drugID][receptor]["sem"]["function"]["ic50"] = ic50SEM
                self.summary[drugID][receptor]["mean"]["function"]["pctInhib"] = pctInhibAverage
                self.summary[drugID][receptor]["sem"]["function"]["pctInhib"] = pctInhibSEM

    def make_function_summary_tables(self):
        meanPrecision = 3
        semPrecision = 2
        for drug, nestedDict in self.summary.items():
            print(f"Drug: {drug}")
            df = pd.DataFrame()
            df['Receptor'] = list(self.summary[drug].keys())
            ec50 = []
            pctStim = []
            ic50 = []
            pctInhib = []
            for subKey, values in nestedDict.items():
                if isinstance(values, dict):
                    meanVals = values['mean']['function']
                    semVals = values['sem']['function']
                    combinedVals = {}
                    for meanKey, semKey in zip(meanVals.keys(), semVals.keys()):
                        outputStr = f"{self.round_sig(meanVals[meanKey], meanPrecision)} ± {self.round_sig(semVals[semKey], semPrecision)}"
                        match(meanKey):
                            case('ec50'):
                                ec50.append(outputStr)
                            case('pctStim'):
                                pctStim.append(outputStr)
                            case('ic50'):
                                ic50.append(outputStr)
                            case('pctInhib'):
                                pctInhib.append(outputStr)
            df['Agonist EC₅₀ (nM) ± SEM'] = ec50
            df['% Stimulation'] = pctStim
            df['Antagonist IC₅₀ (nM) ± SEM'] = ic50
            df['% Inhibition'] = pctInhib
            fig, ax = plt.subplots()
            table = ax.table(cellText=df.values,
                        colLabels=df.columns,
                        loc='center',
                        cellLoc='center')
            table.auto_set_font_size(False)
            table.set_fontsize(12)
            ax.set_axis_off()
            plt.tight_layout()
            plt.savefig(f'..\sample data\{drug}_function_table.png', bbox_inches='tight')

