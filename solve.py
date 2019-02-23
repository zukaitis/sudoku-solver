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
            self.naked_triples()
            self.pointing_pairs_and_triples()
            self.claiming_pairs_and_triples()

    # technique names are taken from this video: https://youtu.be/b123EURtu3I?t=41
    def naked_singles( self ):
        for x in range( self.grid_length ):
            for y in range( self.grid_length ):
                candidates = self.candidates[x,y,:]
                if (1 == np.size(candidates[True == candidates])):
                    value = np.where( True == candidates )[0][0]
                    self.write_and_display_value( x, y, value )
                    return # for slower visual grid filling

    def find_hidden_singles( self, candidates:np.array ):
        for value in range( self.grid_length ):
            candidates_for_value = candidates[:,:,value]
            if (1 == np.size(candidates_for_value[True == candidates_for_value])):
                coordinates = np.where( True == candidates_for_value )
                return coordinates[0][0], coordinates[1][0], value
        return None, None, None

    def hidden_singles( self ):
        for x in range( self.grid_length ):
            _, y, value = self.find_hidden_singles( self.candidates[np.newaxis,x,:,:] )
            if (None != y):
                self.write_and_display_value( x, y, value )
                return # for slower visual grid filling

        for y in range( self.grid_length ):
            x, _, value = self.find_hidden_singles( self.candidates[:,np.newaxis,y,:] )
            if (None != x):
                self.write_and_display_value( x, y, value )
                return # for slower visual grid filling

        for x in range( 0, self.grid_length, self.subgrid_length ):
            for y in range( 0, self.grid_length, self.subgrid_length ):
                sl = self.subgrid_length
                x_in_subgrid, y_in_subgrid, value = self.find_hidden_singles( self.candidates[x:x+sl,y:y+sl,:] )
                if (None != x_in_subgrid):
                    self.write_and_display_value( x + x_in_subgrid, y + y_in_subgrid, value )
                    return # for slower visual grid filling

    def find_naked_pairs( self, candidates:np.array ):
        cell1_iterator = np.nditer( candidates[:,:,0], flags=['multi_index'])
        while not (cell1_iterator.finished):
            cell2_iterator = np.nditer( candidates[:,:,0], flags=['multi_index'])
            cell2_iterator.multi_index = cell1_iterator.multi_index
            cell2_iterator.iternext() # start at index one higher, than that of cell1
            while not (cell2_iterator.finished):
                if (np.array_equal( candidates[cell1_iterator.multi_index], candidates[cell2_iterator.multi_index] )): # check if candidates are the same
                    candidate_pair = np.copy( candidates[cell1_iterator.multi_index] )
                    if (2 == np.size( candidate_pair[True == candidate_pair] )): # check if it's a 'pair'
                        np.bitwise_and( candidates, np.invert( candidate_pair ), out=candidates )
                        candidates[cell1_iterator.multi_index] = candidates[cell2_iterator.multi_index] = candidate_pair # restore pair candidates
                cell2_iterator.iternext()
            cell1_iterator.iternext()

    def naked_pairs( self ):
        for x in range( self.grid_length ):
            self.find_naked_pairs( self.candidates[np.newaxis,x,:,:] )

        for y in range( self.grid_length ):
            self.find_naked_pairs( self.candidates[:,np.newaxis,y,:] )

        for x in range( 0, self.grid_length, self.subgrid_length ):
            for y in range( 0, self.grid_length, self.subgrid_length ):
                sl = self.subgrid_length
                self.find_naked_pairs( self.candidates[x:x+sl,y:y+sl,:] )

    def find_naked_triples( self, candidates:np.array ):
        cell1_iterator = np.nditer( candidates[:,:,0], flags=['multi_index'])
        while not (cell1_iterator.finished):
            cell1_candidates = np.copy( candidates[cell1_iterator.multi_index] )
            if not( 2 <= np.size( cell1_candidates[True == cell1_candidates]) <= 3):
                cell1_iterator.iternext()
                continue
            cell2_iterator = np.nditer( candidates[:,:,0], flags=['multi_index'])
            cell2_iterator.multi_index = cell1_iterator.multi_index
            cell2_iterator.iternext() # start at index one higher, than that of cell1
            while not (cell2_iterator.finished):
                cell2_candidates = np.copy( candidates[cell2_iterator.multi_index] )
                if not( 2 <= np.size( cell2_candidates[True == cell2_candidates]) <= 3):
                    cell2_iterator.iternext()
                    continue
                cell3_iterator = np.nditer( candidates[:,:,0], flags=['multi_index'])
                cell3_iterator.multi_index = cell2_iterator.multi_index
                cell3_iterator.iternext() # start at index one higher, than that of cell2
                while not (cell3_iterator.finished):
                    cell3_candidates = np.copy( candidates[cell3_iterator.multi_index] )
                    if not( 2 <= np.size( cell3_candidates[True == cell3_candidates]) <= 3):
                        cell3_iterator.iternext()
                        continue
                    all_candidates = np.full( self.grid_length, False )
                    np.bitwise_or( cell1_candidates, cell2_candidates, out=all_candidates )
                    np.bitwise_or( cell3_candidates, all_candidates, out=all_candidates )
                    if (3 == np.size( all_candidates[True == all_candidates] )):
                        np.bitwise_and( candidates, np.invert( all_candidates ), out=candidates )
                        candidates[cell1_iterator.multi_index] = cell1_candidates # restore candidates
                        candidates[cell2_iterator.multi_index] = cell2_candidates
                        candidates[cell3_iterator.multi_index] = cell3_candidates
                    cell3_iterator.iternext()
                cell2_iterator.iternext()
            cell1_iterator.iternext()

    def naked_triples( self ):
        for x in range( self.grid_length ):
            self.find_naked_triples( self.candidates[np.newaxis,x,:,:] )

        for y in range( self.grid_length ):
            self.find_naked_triples( self.candidates[:,np.newaxis,y,:] )

        for x in range( 0, self.grid_length, self.subgrid_length ):
            for y in range( 0, self.grid_length, self.subgrid_length ):
                sl = self.subgrid_length
                self.find_naked_triples( self.candidates[x:x+sl,y:y+sl,:] )

    def pointing_pairs_and_triples( self ):
        for x in range( 0, self.grid_length, self.subgrid_length ):
            for y in range( 0, self.grid_length, self.subgrid_length ):
                sl = self.subgrid_length
                subgrid = self.candidates[x:x+sl,y:y+sl,:]
                for value in range( self.grid_length ):
                    candidates_for_value = np.copy( subgrid[:,:,value] )
                    if ( 2 <= np.size( candidates_for_value[True == candidates_for_value]) <= 3):
                        coordinates = np.where( True == candidates_for_value )
                        if (np.all(coordinates[0][0] == coordinates[0])): # check if x coords are the same
                            self.candidates[x+coordinates[0][0],:,value] = False # remove candidates of value from whole column
                            subgrid[:,:,value] = candidates_for_value # restore candidates in subgrid
                        if (np.all(coordinates[1][0] == coordinates[1])): # check if y coords are the same
                            self.candidates[:,y+coordinates[1][0],value] = False # remove candidates of value from whole row
                            subgrid[:,:,value] = candidates_for_value # restore candidates in subgrid
                            
    def claiming_pairs_and_triples( self ):
        for x in range( self.grid_length ):
            for value in range( self.grid_length ):
                candidates_for_value = np.copy( self.candidates[x,:,value] )
                if ( 2 <= np.size( candidates_for_value[True == candidates_for_value]) <= 3):
                    coordinates = np.where( True == candidates_for_value )[0]
                    coordinates = coordinates // self.subgrid_length
                    if (np.all(coordinates[0] == coordinates)): # check if all candidates are in the same subgrid
                        sx = x - x % self.subgrid_length # subgrid edge x
                        sy = coordinates[0] * self.subgrid_length # subgrid edge y
                        sl = self.subgrid_length
                        self.candidates[sx:sx+sl,sy:sy+sl,value] = False # remove candidates of value from whole subgrid
                        self.candidates[x,:,value] = candidates_for_value # restore candidates in column

        for y in range( self.grid_length ):
            for value in range( self.grid_length ):
                candidates_for_value = np.copy( self.candidates[:,y,value] )
                if ( 2 <= np.size( candidates_for_value[True == candidates_for_value]) <= 3):
                    coordinates = np.where( True == candidates_for_value )[0]
                    coordinates = coordinates // self.subgrid_length
                    if (np.all(coordinates[0] == coordinates)): # check if all candidates are in the same subgrid
                        sx = coordinates[0] * self.subgrid_length  # subgrid edge x
                        sy = y - y % self.subgrid_length # subgrid edge y
                        sl = self.subgrid_length
                        self.candidates[sx:sx+sl,sy:sy+sl,value] = False # remove candidates of value from whole subgrid
                        self.candidates[:,y,value] = candidates_for_value # restore candidates in column

def main():

    with open('small_hard.csv', 'rU') as f:
        reader = csv.reader( f )
        cell_list = list( reader )

    cell_list = [[(int(y) if y else None) for y in x] for x in cell_list] # convert strings into ints and Nones

    grid = Grid( cell_list )
    grid.solve()

    input()

main()