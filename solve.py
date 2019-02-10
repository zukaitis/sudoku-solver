import curses
import math
import csv

cell = list(list())
edge_size = int()
subcell_edge_size = int()
min_value = int()
max_value = int()

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
    for x in cell:
        for y in x:
            if (None == y):
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
        for x in range( edge_size ):
            if (value == cell[x][position_y]):
                value_found = True
        for y in range( edge_size ):
            if (value == cell[position_x][y]):
                value_found = True
        subcell_start_x = int(position_x / subcell_edge_size) * subcell_edge_size
        subcell_start_y = int(position_y / subcell_edge_size) * subcell_edge_size
        for x in range(subcell_start_x, subcell_start_x + subcell_edge_size):
            for y in range(subcell_start_y, subcell_start_y + subcell_edge_size):
                if (value == cell[x][y]):
                    value_found = True
        if (not value_found):
            possible_values.append(value)

    return possible_values

def look_for_only_possible_value():
    global cell
    for x in range( 0, edge_size):
        for y in range( 0, edge_size):
            if None == cell[x][y]:
                possible_values = get_possible_values( x, y )
                if 1 == len(possible_values):
                    cell[x][y] = possible_values[0]
                    display.display_string( x, y, str(cell[x][y]) )

def mask_by_value():
    global cell
    for value in range( min_value, max_value + 1 ):
        mask = [[True] * edge_size] * edge_size
        for x in range( edge_size ):
            for y in range( edge_size ):
                mask[x][y] = True if (None == cell[x][y]) else False

        for x in range( edge_size ):
            


def main():
    global cell
    global edge_size
    global subcell_edge_size
    global min_value
    global max_value
    global display

    with open('sample.csv', 'rU') as f:
        reader = csv.reader( f )
        cell = list(reader)
    cell = list(map(list, zip(*cell))) # transpose
    cell = [[(int(y) if y else None) for y in x] for x in cell] # convert strings into ints and Nones

    edge_size = len( cell[0] )
    subcell_edge_size = int(math.sqrt(edge_size))
    cell_length_ch = 1
    min_value = 1
    max_value = edge_size

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