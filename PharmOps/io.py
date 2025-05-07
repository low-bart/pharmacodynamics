import pickle
import h5py
import pandas as pd
import numpy as np
from PharmOps import WellData
from importlib.metadata import version
from platformdirs import user_data_dir
import os
import re
from datetime import datetime
import openpyxl as pxl

# Parses a text file containing raw well-plate data and makes WellData objects
def read_raw_well_txt(filepath):
    rawData = pd.read_csv(filepath)
    pattern = r"Plate \d+.*?(?=Plate \d+|Total count rate:|$)"
    datePattern = r"\b(\d{1,2}-[A-Za-z]{3}-\d{4})\b"    # for regex to find the date
    for i in range(min(len(rawData), 10)):              # limit to the first 10 rows
        for col in rawData.columns:  
            cell = str(rawData.iloc[i][col])
            match = re.search(datePattern, cell)
            if match:
                assayDate = match.group(0)              # return the first matched date
                break
    # parse text file with regex to separate plates
    matches = re.findall(pattern, rawData.to_string(), re.DOTALL)
    plateData = {}
    rowLabels = ["A", "B", "C", "D", "E", "F", "G", "H"]
    for match in matches:
        lines = re.split('\n', match)
        processedLines = []
        # clean escaped tabs
        for line in lines:
            line = line.replace('\\t', '\t')
            contents = line.split('\t')
            processedLines.append(contents)
        plateNumberMatch = re.search(r"plate (\d+)", match)
        if plateNumberMatch:
            plateNo = plateNumberMatch.group(1)
            plateData[f"Plate_{plateNo}"] = processedLines
    # make dataframe from cleaned text segments
    cleanedData = {}
    for plate, rows in plateData.items():
        numericRows = []
        for row in rows:
            rowLabel = row[0].strip()[-1]
            if rowLabel not in rowLabels:
                continue
            dataColumns = row[1:13]
            try:
                dataColumnsInt = [int(value) for value in dataColumns]
                numericRows.append(dataColumnsInt)
            except ValueError:
                continue
        df = pd.DataFrame(numericRows, columns=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12])
        df.index = [row[0].strip()[-1] for row in rows if row[0].strip()[-1] in rowLabels]
        cleanedData[plate] = df
    # make WellData array
    wellDataObjects = []
    for plate, df in cleanedData.items():
        wellDataObjects.append(WellData(df, plate))
        wellDataObjects[-1].set_date(assayDate)
    return wellDataObjects

# Deprecated method for making WellData from a csv
def read_raw_well_csv(filepath):
    rawData = pd.read_excel(filepath)
    rawWellValues = rawData.loc[rawData.index[0:8], range(1, 12)]    
    return rawWellValues

# uses os default data dir from installation to save h5 file
def get_default_h5_path(appName="PharmOps", fileName="data_store.h5"):
    # Determine the platform-specific data directory
    data_dir = user_data_dir(appName, appauthor=False)
    os.makedirs(data_dir, exist_ok=True)  # Ensure the directory exists
    return os.path.join(data_dir, fileName)

# turns date string into an appropriate format for h5 file
def convert_date_string(dateStr):
    parsedDate = datetime.strptime(dateStr, "%d-%b-%Y")
    parsedDate = parsedDate.strftime("%Y%m%d")
    return parsedDate

def prepare_binary(obj):
    serializedObj = pickle.dumps(obj)
    serializedArray = np.frombuffer(serializedObj, dtype='uint8')
    return serializedArray

# save WellData obj to h5
def save_new_WellData(wellData, filepath):
    serializedArray = prepare_binary(wellData)
    parsedDate = convert_date_string(wellData.metadata.date)
    plateNo = wellData.metadata.plate
    with h5py.File(filepath, "a") as h5file:
        group = h5file.require_group("assays/" + parsedDate)
        group.create_dataset(plateNo, data=serializedArray)
        group.attrs["version"] = version("PharmOps")

# save DrugReports obj to h5
def save_new_DrugReport(drugRep, filepath):
    serializedArray = prepare_binary(drugRep)
    drugName = drugRep.drug
    receptorName = drugRep.metadata.receptor
    parsedDate = convert_date_string(drugRep.metadata.date)
    with h5py.File(filepath, "a") as h5file:
        group = h5file.require_group("reports/" + drugName + "/" + receptorName)
        grp = group.create_dataset(parsedDate, data=serializedArray)
        group.attrs["version"] = version("PharmOps")

def save_new_triplicate_assay(triplet, filepath):
    serializedArray = prepare_binary(triplet)
    

# load existing DrugReports from h5 via unserializing 
def load_h5_DrugReports(drugName, receptorName, dateStr, filepath):
    with h5py.File(filepath, "r") as h5file:
        if drugName not in h5file["reports"]:
            raise KeyError(f"No drug '{drugName}' found in h5 file")
        if receptorName not in h5file["reports"][drugName]:
            raise KeyError(f"No receptor '{receptorName}' data found for '{drugName}'")
        if dateStr not in h5file["reports"][drugName][receptorName]:
            raise KeyError(f"No assay on '{dateStr}' for drug '{drugName}' and receptor '{receptorName}'")
        serializedArray = h5file["reports"][drugName][receptorName][dateStr][:]
    loadedRawData = pickle.loads(serializedArray.tobytes())
    return loadedRawData

# all of these methods below are deprecated and exist in bindMods.SummaryTable now
def find_excel_header(row, header):
    indices = [i for i, item in enumerate(row) if isinstance(item, str) and re.search(header, item, re.IGNORECASE)]
    return indices

def extract_mean_and_sem(row, identifier):
    averages = find_excel_header(row, "ave")
    sem = find_excel_header(row, "sem")
    idCol = find_excel_header(row, identifier)

#
def load_binding_summary_excel(filepath):
    allowedNames = ("5HT1A", "5HT2A", "5HT2B", "5HT2C", "D1", "D2", "D3", "D4.4")
    workbook = pxl.load_workbook(filepath, data_only=True)
    summaryDict = {}
    for name in workbook.sheetnames:
        matchingReceptor = [isinstance(item, str) and re.search(item, name, re.IGNORECASE) for item in allowedNames]
        print(name)
        if not any(matchingReceptor):
            print(name)
            continue
        summaryDict = parse_binding_summary_sheet(workbook, name, summaryDict)
    return summaryDict

def parse_binding_summary_sheet(workbook, receptor, summary):
    sheet = workbook[receptor]
    keyHeaders = ['ic50', 'ki', 'hill slope']
    valHeaders = ['ave', 'sem']
    matchStr = r"\b(" + "|".join(map(re.escape, valHeaders)) + r")\b"
    for idx, row in enumerate(sheet.iter_rows(values_only=True)):
        ic50 = find_excel_header(row, "ic50")
        ki = find_excel_header(row, "ki")
        hillSlope = find_excel_header(row, "hill slope")
        averages = find_excel_header(row, "ave")      # collected in case absolute refs are necessary
        sem = find_excel_header(row, "sem")           # collected in case absolute refs are necessary
        headerRow = find_excel_header(row, matchStr)
        if ic50 and ki and hillSlope:
            drugID = row[0]
            if not drugID:
                temp = idx
            while not drugID:
                temp = temp-1
                drugID = sheet.cell(row=temp+1, column=1).value
            # relative average and sem indexing to the cells with the datatype's header
            ic50Average = sheet.cell(row=idx+2, column=ic50[0]+2).value
            ic50SEM = sheet.cell(row=idx+2, column=ic50[0]+3).value
            kiAverage = sheet.cell(row=idx+2, column=ki[0]+2).value
            kiSEM = sheet.cell(row=idx+2, column=ki[0]+3).value
            hillAverage = sheet.cell(row=idx+2, column=hillSlope[0]+2).value
            hillSEM = sheet.cell(row=idx+2, column=hillSlope[0]+3).value
            summary[drugID][receptor]["mean"]["ic50"] = ic50Average
            summary[drugID][receptor]["sem"]["ic50"] = ic50SEM
            summary[drugID][receptor]["mean"]["ki"] = kiAverage
            summary[drugID][receptor]["sem"]["ki"] = kiSEM
            summary[drugID][receptor]["mean"]["hillSlope"] = hillAverage
            summary[drugID][receptor]["sem"]["hillSlope"] = hillSEM
    return summary

def make_function_table(srcDir):
    receptorNames = ("5HT1A", "5HT2A", "5HT2B", "5HTR", "5HT2C", "D1", "D2", "D3", "D4")
    dataIdentifiers =  ["FXN", "EC50"]
    localFiles = os.listdir(srcDir)
    fileId = {word: [file for file in localFiles if re.search(rf"\b{re.escape(word)}\b", file)] for word in receptorNames}
    print(fileId)
    for word in fileId:
        if not fileId[word]:
            continue
        for file in fileId[word]:
            fName, fExt = os.path.splitext(file)
            if fExt != ".xlsx":
                continue
            workbook = pxl.load_workbook(srcDir + "\\" + file, data_only=True)
            parse_wb_sheets(workbook)

def parse_wb_sheets(workbook, summary):
    summaryDict = {}
    for name in workbook.sheetnames:
        sheet = workbook[name]
        printNext = False
        for row in sheet.iter_rows(values_only=True):
            ec50 = find_excel_header(row, "ec50")
            if printNext:
                printNext = False
            if ec50:
                printNext = True