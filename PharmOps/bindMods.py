import numpy as np

class AssayMetadata:
    drug = []
    date = []
    ctr = []
    plate = []

    def __init__(self):
        pass

class WellData:

    ctr = []        # color to right
    plate = []      # plate number
    drugs = []      # list of drugs on plate, one per two rows
    comments = []   # list
    data = []       # well plate data
    totals = []     # well plate totals with no drug
    nsb = []        # well plate non-specific binding
    metadata = AssayMetadata()

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


class DrugReports:
    average = []
    specific = []
    concentration = []
    logConc = []
    pctTotal = []
    averageSpecific = []
    specificBound = []
    pctSpecificBinding = []
    metadata = AssayMetadata()

    def __init__(self, wellData, index):
        self.metadata.drug = wellData.drugs[index]
        self.metadata.date = wellData.date
        self.metadata.ctr = wellData.ctr
        self.metadata.plate = wellData.plate
        # isolate rows by index
        startRow = (index) * 2
        endRow = startRow + 2
        drugData = wellData.data.iloc[startRow:endRow]
        plateNSB = drugData.loc[drugData.index[0:8], 2]
        plateTotals = drugData.loc[drugData.index[0:8], [1, 12]]
        self.averageSpecific = np.average(plateTotals)
        print(plateTotals)
