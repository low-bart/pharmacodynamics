class BindData:

    date = []
    plate = []
    drug = []
    comments = []
    data = []

    def __init__(self, df):
        self.data = df.loc[df.index[0:8], [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]]

    def display(self):
        print(self.data)
