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
        if (self.value[position_x][position_y] != None):
            raise Exception('Overwriting an existing value, something is wrong')
        self.value[position_x][position_y] = value
        displayed_value = value + self.value_offset
        self.display.display_string( position_x, position_y, str( displayed_value ) )
        self.refresh_candidates()

    def solve( self ):
        while (np.size( self.value[None == self.value] ) > 0):
            self.naked_singles()
            self.hidden_singles()
            self.naked_pairs()

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

    def naked_pairs( self ):
        for x in range( self.grid_length ):
            column = self.candidates[x,:,:]
            for y1 in range( self.grid_length ):
                for y2 in range( y1 + 1, self.grid_length ):
                    if (np.array_equal( column[y1,:], column[y2,:] )): # check if candidates are the same
                        candidate_pair = np.copy( column[y1,:] )
                        if (2 == np.size( candidate_pair[True == candidate_pair] )): # check if it's a 'pair'
                            masked_column = np.delete( column, [y1, y2], 0 )
                            # invert
                            # AND with masked column

        for y in range( self.grid_length ):
            row = self.candidates[:,y,:]
            for x1 in range( self.grid_length ):
                for x2 in range( x1 + 1, self.grid_length ):
                    if (np.array_equal( row[x1,:], row[x2,:] )): # check if candidates are the same
                        candidate_pair = np.copy( row[x1,:] )
                        if (2 == np.size( candidate_pair[True == candidate_pair] )): # check if it's a 'pair'
                            masked_row = np.delete( row, [x1, x2], 0 )
                            # invert
                            # AND with masked row

def main():

    with open('sample.csv', 'rU') as f:
        reader = csv.reader( f )
        cell_list = list( reader )

    cell_list = [[(int(y) if y else None) for y in x] for x in cell_list] # convert strings into ints and Nones

    grid = Grid( cell_list )
    grid.solve()

    input()

main()