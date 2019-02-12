import curses
import math
import csv
import numpy

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

def is_solved():
    global cell
    is_solved = True
    if (numpy.size(cell[None == cell]) > 0):
        is_solved = False
    return is_solved

def get_possible_values( position_x, position_y ):
    global cell
    global edge_size
    global subcell_edge_size
    global min_value
    global max_value

    possible_values = list()

    for value in range( min_value, max_value + 1 ):
        value_found = False
        
        row = cell[:, position_y]
        if (numpy.size(row[row == value]) > 0):
            value_found = True
        
        column = cell[position_x, :]
        if (numpy.size(column[column == value]) > 0):
            value_found = True

        subcell_start_x = int(position_x / subcell_edge_size) * subcell_edge_size
        subcell_start_y = int(position_y / subcell_edge_size) * subcell_edge_size
        subcell = cell[subcell_start_x:subcell_start_x+subcell_edge_size, subcell_start_y:subcell_start_y+subcell_edge_size]
        if (numpy.size(subcell[subcell == value]) > 0):
            value_found = True

        if (not value_found):
            possible_values.append( value )

    return possible_values

def look_for_only_possible_value():
    global cell
    for x in range( edge_size ):
        for y in range( edge_size ):
            if (None == cell[x][y]):
                possible_values = get_possible_values( x, y )
                if (1 == len(possible_values)):
                    write_value_and_display( x, y, possible_values[0] )

def mask_by_value():
    global cell
    for value in range( min_value, max_value + 1 ):
        mask = numpy.copy( cell )
        # mask all non-empty cells
        mask[None == mask] = True
        mask[True != mask] = False

        for x in range( edge_size ):
            column = cell[x, :]
            if (numpy.size(column[column == value]) > 0):
                # mask columns, containing value
                mask[x, :] = False

        for y in range( edge_size ):
            row = cell[:, y]
            if (numpy.size(row[row == value]) > 0):
                # mask rows, containing value
                mask[:, y] = False

        for x in range(0, edge_size, subcell_edge_size):
            for y in range(0, edge_size, subcell_edge_size):
                subcell = cell[x:x+subcell_edge_size, y:y+subcell_edge_size]
                if (numpy.size(subcell[subcell == value]) > 0):
                    # mask subcells, containing value
                    mask[x:x+subcell_edge_size, y:y+subcell_edge_size] = False

        # search for single unmasked fields in columns, rows, and subcells
        for x in range( edge_size ):
            column = mask[x, :]
            if (1 == numpy.size( column[column == True]) ):
                write_value_and_display( x, numpy.where(column == True)[0][0], value )
                return # return after first found value

        for y in range( edge_size ):
            row = mask[:, y]
            if (1 == numpy.size( row[row == True]) ):
                write_value_and_display( numpy.where(row == True)[0][0], y, value )
                return # return after first found value

        for x in range(0, edge_size, subcell_edge_size):
            for y in range(0, edge_size, subcell_edge_size):
                subcell = mask[x:x+subcell_edge_size, y:y+subcell_edge_size]
                if (1 == numpy.size( subcell[subcell == True]) ):
                    x_in_subcell, y_in_subcell = numpy.where(subcell == True)
                    write_value_and_display( x + x_in_subcell[0], y + y_in_subcell[0], value )
                    return # return after first found value

def write_value_and_display( position_x : int, position_y : int, value : int ):
    global display
    global cell

    cell[position_x][position_y] = value
    display.display_string( position_x, position_y, str(value) )

def main():
    global cell
    global edge_size
    global subcell_edge_size
    global min_value
    global max_value
    global display

    with open('sample.csv', 'rU') as f:
        reader = csv.reader( f )
        cell_list = list(reader)

    cell_list = [[(int(y) if y else None) for y in x] for x in cell_list] # convert strings into ints and Nones
    cell = numpy.array( cell_list )
    cell = cell.transpose()

    # value_x, value_y = numpy.where(cell == 1)
    # print(value_x)
    # print(value_y)

    edge_size = numpy.size( cell[0] )
    subcell_edge_size = int(math.sqrt(edge_size))
    min_value = numpy.amin( cell[None != cell] )
    max_value = numpy.amax( cell[None != cell] )
    cell_length_ch = 1 if (max_value < 10) else 2

    display = Display( edge_size, cell_length_ch )

    for x in range( 0, edge_size):
        for y in range( 0, edge_size):
            if None != cell[x][y]:
                display.display_string( x, y, str(cell[x][y]) )

    while (not is_solved()):
        look_for_only_possible_value()
        mask_by_value()

    input()

main()