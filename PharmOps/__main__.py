from guitools import *
from guitools_class import *
import numpy as np
def main():
     # load sample data
    # make GUI window appear
    sampleWellPlate = 'sample data\\Binding Template for RAW transformations.xlsx'
    sampleMultiplateTxt = 'sample data\\110824_raw data.txt'
    # read_MultiWell_txt(sampleMultiplateTxt)
    #initialize_GUI()
    # load directories of h5 or xlsx files
    # make new DrugReports
    root = tk.Tk()
    app = BindingGUI(root)
    root.mainloop()
    

if __name__ == "__main__":
    main()
       