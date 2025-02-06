import numpy as np

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
    drugs=[]                # list of drugs on plate, one per two rows
    comments=[]             # list
    data=[]                 # well plate data
    totals=[]               # well plate totals with no drug
    nsb=[]                  # well plate non-specific binding
    highestConc=[]          # log [drug]
    plateNo=[]              
    specificActivityCi=[]   
    specificActivityCpm=[]  
    volMl=[]                

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
