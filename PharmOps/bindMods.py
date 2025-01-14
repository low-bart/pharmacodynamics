import numpy as np

class AssayMetadata:
    date = []
    ctr = []
    plate = []
    receptor = []

    def __init__(self):
        pass

class WellData:
    metadata = AssayMetadata()
    drugs = []      # list of drugs on plate, one per two rows
    comments = []   # list
    data = []       # well plate data
    totals = []     # well plate totals with no drug
    nsb = []        # well plate non-specific binding

    def __init__(self, df):
        self.data = df.loc[df.index[0:8], [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]]
        self.drugs = ["Drug1", "Drug2", "Drug3", "Drug4"]
        plateTotals = self.data.loc[self.data.index[0:8], [1, 12]]
        self.totals = np.average(plateTotals)
        plateNSB = self.data.loc[self.data.index[0:8], 2]
        self.nsb = np.average(plateNSB) 

    def display(self):
        print(self.data)
        print(self.comments)
        print(self.drugs)

    def add_comment(self, comment):
        self.comments.append(comment)

    def make_drug_report(self, index):
        return DrugReports(self, index)
    
    def make_all_drug_reports(self):
        reports = []
        for i in range(4):
            reports.append(DrugReports(self, i))
        return reports


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

    def __init__(self, wellData, index):
        self.drug = wellData.drugs[index]
        self.metadata = wellData.metadata
        # isolate rows by index
        startRow = (index) * 2
        endRow = startRow + 2
        drugData = wellData.data.iloc[startRow:endRow]
        self.averageSpecific = np.average(wellData.totals)
        testData = drugData.loc[drugData.index[:], [3, 4, 5, 6, 7, 8, 9, 10, 11]]
        print(testData)
        self.average = [testData.mean(axis=0)]
        self.specific = [x - wellData.nsb for x in self.average]
        self.specificBound = wellData.totals - wellData.nsb
        self.pctTotal = [x * 100 / self.specificBound for x in self.specific]
        print(drugData)
        print(self.average)
        print(self.specific)
