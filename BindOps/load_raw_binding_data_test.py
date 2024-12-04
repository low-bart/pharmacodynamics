import pandas as pd

# import raw data spreadsheet
rawData = pd.read_excel('sample data\\Binding Template for RAW transformations.xlsx')
# identify row labels
print(rawData.loc[rawData.index[0:2]])
'''
for i in rawData.items():
    print(i)
# load 96 well data matrix
print(rawData.index)
print(rawData.columns)
'''