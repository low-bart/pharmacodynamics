
from abc import ABC, abstractmethod
from dataclasses import dataclass

# abstract base class to inherit modes of cell selection from
class SelectionStrategy(ABC):
    @abstractmethod
    def on_click(self, row, col, event):
        pass

    def on_drag(self, row, col, event, currentSelection):
        return currentSelection
    
    def on_release(self, row, col, event, currentSelection):
        return currentSelection
    
    def on_up_arrow(self, row, col, event, currentSelection):
        pass

    def on_down_arrow(self, row, col, event, currentSelection):
        pass

    def on_left_arrow(self, row, col, event, currentSelection):
        pass

    def on_right_arrow(self, row, col, event, currentSelection):
        pass
    
    def add_selection(self, row, col):
        pass

    def get_selected_cells(self):
        pass

    def get_locked_cells(self):
        return {}
    
# select/deselect the cell that was clicked
class SingleCellSelector(SelectionStrategy):
    def __init__(self, selectedCell, lockedCells):
        self.selectedCell = selectedCell
        self.lockedCells = lockedCells

    def on_click(self, row, col):
        if (row, col) in self.lockedCells:
            return
        if (row, col) == self.selectedCell:
            self.selectedCell.clear()
        else:
            self.selectedCell.clear()
            self.selectedCell.add((row, col))

    def get_selected_cells(self):
        return self.selectedCell

# allow multiple cells to be selected at once
class MultiCellSelector(SelectionStrategy):
    def __init__(self, selectedCells, lockedCells):
        self.selectedCells = selectedCells
        self.lockedCells = lockedCells

    def on_click(self, row, col):
        if (row, col) in self.lockedCells:
            return
        if (row, col) in self.selectedCells:
            self.selectedCells.remove((row, col))
        else:
            self.selectedCells.add((row, col))

    def get_selected_cells(self):
        return self.selectedCells

# select/deselect the triplet containing the cell that was clicked
class SingleTripletSelector(SelectionStrategy):
    def __init__(self, selectedTriplets, lockedTriplets):
        self.selectedTriplets = selectedTriplets
        self.lockedTriplets = lockedTriplets
        self.clickX = None
        self.clickY = None
        self.rowClicked = None
        self.colClicked = None

    def on_click(self, row, col, event):
        self.clickX = event.x
        self.clickY = event.y
        self.rowClicked = row
        self.colClicked = col
        triplet = col // 3
    
    def on_drag(self, row, col, event):
        latestX = event.x
        latestY = event.y
        return([self.clickX, self.clickY, latestX, latestY])
    
    def on_release(self, row, col, event):
        triplet = self.colClicked // 3
        if (self.rowClicked, triplet) in self.lockedTriplets:
            return
        if (self.rowClicked, triplet) in self.selectedTriplets:
            self.selectedTriplets.remove((self.rowClicked, triplet))
            return
        self.add_selection(self.rowClicked, triplet)

    def add_selection(self, row, triplet):
        self.selectedTriplets.clear()
        self.selectedTriplets.add((row, triplet))

    def on_up_arrow(self, row, col):
        triplet = col // 3
        if row == 0:
            row = 7
        else:
            row -= 1
        self.add_selection(row, triplet)

    def on_down_arrow(self, row, col):
        triplet = col // 3
        if row == 7:
            row = 0
        else:
            row += 1
        self.add_selection(row, triplet)

    def on_left_arrow(self, row, col):
        triplet = col // 3
        if triplet == 0:
            triplet = 3
        else:
            triplet -= 1
        self.add_selection(row, triplet)

    def on_right_arrow(self, row, col):
        triplet = col // 3
        if triplet == 3:
            triplet = 0
        else:
            triplet += 1
        self.add_selection(row, triplet)

    def get_selected_cells(self):
        return{(row, col) 
               for (row, startCol) in self.selectedTriplets 
               for col in range(startCol*3, startCol*3 + 3)}
    
    def get_locked_cells(self):
        return{(row, col) 
               for (row, startCol) in self.lockedTriplets 
               for col in range(startCol*3, startCol*3 + 3)}

# allow multiple triplets to be selected
class MultiTripletSelector(SingleTripletSelector):
    def on_release(self, row, col, event):
        if row < 0:
            row = 0
        if row > 7:
            row = 7
        if col < 0:
            col = 0
        if col > 11:
            col = 11
        rows = [row, self.rowClicked]
        cols = [col, self.colClicked]
        rowRange = range(min(rows), max(rows) + 1)
        colRange = range(min(cols), max(cols) + 1)
        tripletsIncluded = np.unique([x // 3 for x in colRange])
        for row in rowRange:
            for triplet in tripletsIncluded:
                if (row, triplet) in self.lockedTriplets:
                    continue
                elif (row, triplet) in self.selectedTriplets:
                    self.selectedTriplets.remove((row, triplet))
                else:
                    self.selectedTriplets.add((row, triplet))  

# select cells by row (no single selector yet)
class RowSelector(SelectionStrategy):
    def __init__(self, selectedRows, lockedRows):
        self.selectedRows = selectedRows
        self.lockedRows = lockedRows
        self.clickX = None
        self.clickY = None
        self.rowClicked = None
        self.colClicked = None

    def on_click(self, row, col, event):
        if col not in range(0, 12):
            return
        #if row in self.lockedRows:
        #    return
        self.clickX = event.x
        self.clickY = event.y
        self.rowClicked = row
        self.colClicked = col
        #if row in self.selectedRows:
        #    self.selectedRows.remove(row)
        #    return
        #self.selectedRows.clear() #commented out while i figure out how to divide multiselect
        #self.selectedRows.add(row)

    def on_drag(self, row, col, event):
        latestX = event.x
        latestY = event.y
        return([self.clickX, self.clickY, latestX, latestY])
    
    def on_release(self, row, col, event):
        if row < 0:
            row = 0
        if row > 7:
            row = 7
        rows = [row, self.rowClicked]
        rowRange = range(min(rows), max(rows) + 1)
        for row in rowRange:
            if row in self.lockedRows:
                continue
            if row in self.selectedRows:
                self.selectedRows.remove(row)
            else:
                self.selectedRows.add(row)

    def get_selected_cells(self):
        return {(row, col)
                for row in self.selectedRows
                for col in range(0, 12)}
    
    def get_locked_cells(self):
        return{(row, col)
               for row in self.lockedRows
               for col in range(0, 12)}
    
# contains default cell styling params to pass to CustomTable
@dataclass
class CellStyle:
    fill: str = "white"
    outline: str = "black"
    text: str = ""
    font: str = "TkDefaultFont"
    width: int = 2
    stipple: str = None

# abstract base class for different stylings, returning a CellStyle object
class CellStyleResolver(ABC):
    @abstractmethod
    def get_cell_style(self, row, col) -> CellStyle:
        # returns drawing properties for different contexts
        pass

class HighlightSelection(CellStyleResolver):
    def __init__(self, selectionSet, selectionStrategy):
        self.selectionSet = selectionSet
        self.strategy = selectionStrategy

    def get_cell_style(self, row, col):
        parentSelection = self.strategy.get_selected_cells()
        if (row, col) in parentSelection:
            return CellStyle(fill="firebrick1", outline="black", width=2)
        return CellStyle
        
class HighlightAndLockSelection(CellStyleResolver):
    def __init__(self, selectionStrategy):
        self.strategy = selectionStrategy

    def get_cell_style(self, row, col):
        parentSelection = self.strategy.get_selected_cells() or {}
        parentLock = self.strategy.get_locked_cells() or {}
        if (row, col) in parentSelection:
            return CellStyle(fill="firebrick1")
        elif (row, col) in parentLock:
            return CellStyle(fill="dodger blue")
        return CellStyle
        
class HighlightAndBlockSelection(CellStyleResolver):
    def __init__(self, blockedCells, selectionStrategy):
        self.blockedCells = blockedCells
        self.strategy = selectionStrategy

    def get_cell_style(self, row, col):
        parentSelection = self.strategy.get_selected_cells() or {}
        parentLock = self.strategy.get_locked_cells() or {}
        if (row, col) in self.blockedCells:
            return CellStyle(fill="gray", stipple='gray50')
        if (row, col) in parentSelection:
            return CellStyle(fill="firebrick1")
        if (row, col) in parentLock:
            return CellStyle(fill="dodger blue")
        return CellStyle
    
class BlueWeighingSelection(HighlightAndBlockSelection):
    def get_cell_style(self, row, col):
        parentSelection = self.strategy.get_selected_cells() or {}
        parentLock = self.strategy.get_locked_cells() or {}     
        if (row, col) in self.blockedCells:
            return CellStyle(fill="gray", stipple='gray50')
        if (row, col) in parentSelection:
            return CellStyle(fill="Blue")
        if (row, col) in parentLock:
            return CellStyle(fill="Blue", outline="dark slate gray")
        return CellStyle(fill="firebrick1")
        
class BlackWeighingSelection(HighlightAndBlockSelection):
    def get_cell_style(self, row, col):
        parentSelection = self.strategy.get_selected_cells() or {}
        parentLock = self.strategy.get_locked_cells() or {}
        if (row, col) in self.blockedCells:
            return CellStyle(fill="gray", stipple='gray50')
        if (row, col) in parentSelection:
            return CellStyle(fill="gray10")
        if (row, col) in parentLock:
            return CellStyle(fill="black", outline="dark slate gray")
        return CellStyle(fill="firebrick1")
