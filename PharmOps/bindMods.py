class WellData:

    date = []       # assay date
    ctr = []        # color to right
    plate = []      # plate number
    drugs = []      # list of drugs on plate, one per row
    comments = []   # list
    data = []

    def __init__(self, df):
        self.data = df.loc[df.index[0:8], [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]]

    def display(self):
        print(self.data)
        print(self.comments)

    def add_comment(self, comment):
        self.comments.append(comment)

    def make_drug_report(self, row):
        return DrugReports([], [])

class DrugReports:
    drug = []
    concentration = []
    pctSpecificBinding = []
    receptor = []

    def __init__(self, wellRow, info):
        pass
