import curses
import math
import csv
import numpy as np
import numpy.ma as ma

class Display:

    def __init__(self, grid_edge_size, cell_length_ch ):
        self.cell_length_ch = cell_length_ch
        self.subgrid_edge_size = int(math.sqrt( grid_edge_size ))
        self.subgrid_count_on_edge = self.subgrid_edge_size
        self.subgrid_length_ch = self.subgrid_edge_size * (cell_length_ch + 1) - 1
        self.subgrid_height_ch = self.subgrid_edge_size
        self.grid_length_ch = (self.subgrid_length_ch + 1) * self.subgrid_edge_size - 1
        self.grid_height_ch = (self.subgrid_height_ch + 1) * self.subgrid_edge_size - 1

        curses.initscr()
        self.window = curses.newwin( self.grid_height_ch + 1, self.grid_length_ch + 1 )
        self._display_grid()
        self.window.refresh()

    def _display_grid( self ):
        for column_number in range( 1, self.subgrid_edge_size ):
            for y in range( 0, self.grid_height_ch):
                x = (column_number * (self.subgrid_length_ch + 1)) - 1
                self.window.addch( y, x, '|' )

        for row_number in range( 1, self.subgrid_edge_size ):
            for x in range( 0, self.grid_length_ch):
                y = (row_number * (self.subgrid_height_ch + 1)) - 1
                on_intersection = (ord('|') == (self.window.inch( y, x ) & curses.A_CHARTEXT))
                self.window.addch( y, x, '+' if on_intersection else '-' )

    def display_string( self, position_x, position_y, string ):
        position_x = position_x * (self.cell_length_ch + 1)
        position_y = position_y + int(position_y / self.subgrid_count_on_edge)
        self.window.addstr( position_y, position_x, string )
        self.window.refresh()

# def is_solved():
#     global cell
#     is_solved = True
#     if (np.size(cell[None == cell]) > 0):
#         is_solved = False
#     return is_solved

# def get_possible_values( position_x, position_y ):
#     global cell
#     global edge_size
#     global subcell_edge_size
#     global min_value
#     global max_value

#     possible_values = list()

#     for value in range( min_value, max_value + 1 ):
#         value_found = False
        
#         row = cell[:, position_y]
#         if (np.size(row[row == value]) > 0):
#             value_found = True
        
#         column = cell[position_x, :]
#         if (np.size(column[column == value]) > 0):
#             value_found = True

#         subcell_start_x = int(position_x / subcell_edge_size) * subcell_edge_size
#         subcell_start_y = int(position_y / subcell_edge_size) * subcell_edge_size
#         subcell = cell[subcell_start_x:subcell_start_x+subcell_edge_size, subcell_start_y:subcell_start_y+subcell_edge_size]
#         if (np.size(subcell[subcell == value]) > 0):
#             value_found = True

#         if (not value_found):
#             possible_values.append( value )

#     return possible_values

# def look_for_only_possible_value():
#     global cell
#     for x in range( edge_size ):
#         for y in range( edge_size ):
#             if (None == cell[x][y]):
#                 possible_values = get_possible_values( x, y )
#                 if (1 == len(possible_values)):
#                     write_value_and_display( x, y, possible_values[0] )

# def mask_by_value():
#     global cell
#     for value in range( min_value, max_value + 1 ):
#         mask = np.copy( cell )
#         # mask all non-empty cells
#         mask[None == mask] = True
#         mask[True != mask] = False

#         for x in range( edge_size ):
#             column = cell[x, :]
#             if (np.size(column[column == value]) > 0):
#                 # mask columns, containing value
#                 mask[x, :] = False

#         for y in range( edge_size ):
#             row = cell[:, y]
#             if (np.size(row[row == value]) > 0):
#                 # mask rows, containing value
#                 mask[:, y] = False

#         for x in range(0, edge_size, subcell_edge_size):
#             for y in range(0, edge_size, subcell_edge_size):
#                 subcell = cell[x:x+subcell_edge_size, y:y+subcell_edge_size]
#                 if (np.size(subcell[subcell == value]) > 0):
#                     # mask subcells, containing value
#                     mask[x:x+subcell_edge_size, y:y+subcell_edge_size] = False

#         # search for single unmasked fields in columns, rows, and subcells
#         for x in range( edge_size ):
#             column = mask[x, :]
#             if (1 == np.size( column[column == True]) ):
#                 write_value_and_display( x, np.where(column == True)[0][0], value )
#                 return # return after first found value

#         for y in range( edge_size ):
#             row = mask[:, y]
#             if (1 == np.size( row[row == True]) ):
#                 write_value_and_display( np.where(row == True)[0][0], y, value )
#                 return # return after first found value

#         for x in range(0, edge_size, subcell_edge_size):
#             for y in range(0, edge_size, subcell_edge_size):
#                 subcell = mask[x:x+subcell_edge_size, y:y+subcell_edge_size]
#                 if (1 == np.size( subcell[subcell == True]) ):
#                     x_in_subcell, y_in_subcell = np.where(subcell == True)
#                     write_value_and_display( x + x_in_subcell[0], y + y_in_subcell[0], value )
#                     return # return after first found value

class Grid:
    def __init__( self, value : list ):
        self.value = np.array( value )
        self.value = self.value.transpose()

        self.grid_length = np.size( value[0] )
        self.subgrid_length = int(math.sqrt(self.grid_length))
        self.min_value = int(np.amin( self.value[None != self.value] ))
        self.max_value = int(np.amax( self.value[None != self.value] ))
        self.cell_length_ch = 1 if (self.max_value < 10) else 2

        self.value_offset = self.min_value
        self.value[None != self.value] = self.value[None != self.value] - self.value_offset

        self.candidates = np.full( [self.grid_length, self.grid_length, self.grid_length], True )
        self.refresh_candidates()

        self.display = Display( self.grid_length, self.cell_length_ch )
        for x in range( self.grid_length ):
            for y in range( self.grid_length ):
                if (None != self.value[x][y]):
                    self.display.display_string( x, y, str(self.value[x][y] + self.value_offset) )

    def refresh_candidates( self ):
        iteration = np.nditer( self.value, flags=['multi_index', 'refs_ok'] )
        while (not iteration.finished):
            x = iteration.multi_index[0]
            y = iteration.multi_index[1]
            value = self.value[x][y]
            if (None != value):
                # disable all possible values for cell, if value is already defined
                self.candidates[x,y,:] = False

                # disable candidates of value in column, row, and subcell
                column = self.candidates[x,:,:]
                row = self.candidates[:,y,:]
                sl = self.subgrid_length
                subgrid = self.candidates[x-x%sl:x-x%sl+sl,y-y%sl:y-y%sl+sl,:]

                column[:,value] = False
                row[:,value] = False
                subgrid[:,:,value] = False
            iteration.iternext()

    def write_and_display_value( self, position_x : int, position_y : int, value : int ):
        self.value[position_x][position_y] = value
        displayed_value = value + self.value_offset
        self.display.display_string( position_x, position_y, str( displayed_value ) )
        self.refresh_candidates()

    def solve( self ):
        while (np.size( self.value[None == self.value] ) > 0):
            self.naked_singles()
            self.hidden_singles()

    # technique names are taken from this video: https://youtu.be/b123EURtu3I?t=41
    def naked_singles( self ):
        for x in range( self.grid_length ):
            for y in range( self.grid_length ):
                candidates = self.candidates[x,y,:]
                if (1 == np.size(candidates[True == candidates])):
                    value = np.where( True == candidates )[0][0]
                    self.write_and_display_value( x, y, value )
                    return

    def hidden_singles( self ):
        for value in range( self.grid_length ):
            for x in range( self.grid_length ):
                column = self.candidates[x,:,value]
                if (1 == np.size(column[True == column])):
                    y = np.where( True == column )[0][0]
                    self.write_and_display_value( x, y, value )
                    return

            for y in range( self.grid_length ):
                row = self.candidates[:,y,value]
                if (1 == np.size(row[True == row])):
                    x = np.where( True == row )[0][0]
                    self.write_and_display_value( x, y, value )
                    return

            sl = self.subgrid_length
            for x in range( 0, self.grid_length, self.subgrid_length ):
                for y in range(0, self.grid_length, self.subgrid_length ):
                    subgrid = self.candidates[x:x+sl,y:y+sl,:]
                    if (1 == np.size( subgrid[subgrid == True]) ):
                        subgrid_coordinates = np.where(subgrid == True)
                        self.write_and_display_value( x + subgrid_coordinates[0], y + subgrid_coordinates[1], value )
                        return

def main():

    with open('sample.csv', 'rU') as f:
        reader = csv.reader( f )
        cell_list = list(reader)

    cell_list = [[(int(y) if y else None) for y in x] for x in cell_list] # convert strings into ints and Nones

    grid = Grid( cell_list )
    grid.solve()

    input()

main()