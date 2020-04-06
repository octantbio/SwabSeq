#!/usr/bin/env python

import itertools
import pandas as pd
from copy import deepcopy
from collections import defaultdict
from math import sqrt
import string

from openpyxl import load_workbook
from xlrd import XLRDError

# Suite of functions for new plate maps
def add_plate_map_constants(plate_maps, constants_df):
    
    plate_maps_full = defaultdict(dict, deepcopy(plate_maps))
    
    # Get plate sizes (also gets plate worksheet variable names)
    plate_sizes = get_plate_sizes(plate_maps)
    
    # Check that all plates in the constants tab are in
    # the existing plate maps dict, and vice versa
    if not all(plate in constants_df['Plate'].tolist() for plate in plate_sizes.keys()):
        raise RuntimeError('The following plates are in the individual plate maps but not in the "_constants" tab: {}'.format(list(plate_sizes.keys() - set(constants_df['Plate'].tolist()))))
    if not all(plate in plate_sizes.keys() for plate in constants_df['Plate'].tolist()):
        raise RuntimeError('The following plates are in the "_constants" tab but not in the individual plate maps: {}'.format(list(set(constants_df['Plate'].tolist()) - plate_sizes.keys())))    

    # Ensure that a variable is not specifed both as its own tab and as a column in the _constants tab
    dup_columns = set(constants_df.columns.tolist()) & plate_maps.keys()
    if len(dup_columns) > 0:
        raise RuntimeError('The following variables are defined in both the individual plate maps and the "_constants" tab: {}'.format(list(dup_columns)))

    # Add constants into the plate dictionary
    constants_df = constants_df.set_index('Plate')
    for plate_id in plate_sizes.keys():
        for var_name in constants_df.columns:
            plate_maps_full[var_name][plate_id] = [constants_df.loc[plate_id, var_name]] * plate_sizes[plate_id]
            
    return dict(plate_maps_full)

def expand_plate_maps(plate_maps):
    plate_maps_expanded = defaultdict(dict)
    for var, plate_dict in plate_maps.items():
        for plate, val in plate_dict.items():
            plates = enum_plates(plate)
            for enum_plate in plates:
                plate_maps_expanded[var][enum_plate] = val
    return dict(plate_maps_expanded)

def get_stripped_values(sheet):
    # Get the values as a list of tuples
    vals = list(sheet.values)

    # Determine last row
    nrows = len(vals)
    for i in range(nrows-1, 0, -1):
        if all(x is None for x in vals[i]):
            nrows = i
        else:
            break

    # Strip off extra rows
    vals = vals[:nrows]

    # Determine last column
    ncols = len(vals[0])
    for i in range(ncols-1, 0, -1):
        if all(x is None for x in [vals[j][i] for j in range(nrows)]):
            ncols = i
        else:
            break

    # Strip off extra columns
    vals = [row[:ncols] for row in vals]

    return vals

def read_plate_map_sheets(sheets):
    # This needs to error out in an informative way - I had a tab named "test"
    # with nothing in the right format and the error was not intuitive.
    plate_maps = {}
    #var_names = set()
    #plate_ids = set()
    for sheet in sheets.worksheets:
        var_name = sheet.title
        #var_names.add(var_name)
        if not var_name.startswith('_'):
            strip = get_stripped_values(sheet)
            plates = [list(x[1]) for x in itertools.groupby(strip, lambda line: all(y is None for y in line)) if not x[0]]
            try:
                plate_by_var = split_plate(plates)
            except ValueError as e:
                raise ValueError(f'\n\nError in sheet "{var_name}":\n\n{e}')
            plate_maps[var_name] = plate_by_var
    
    return plate_maps

def read_plate_maps(fname):

    sheets = load_workbook(fname, data_only = True)
    
    # Read in the sheet-formatted maps and expand them
    plate_maps = read_plate_map_sheets(sheets)
    plate_maps = expand_plate_maps(plate_maps)
    
    # Ensure all observed plates exist for all variables
    check_plates_x_vars(plate_maps)
    
    # Read in constants and add them into the full-format plate map
    constants_df = get_constants_tab(fname)
    plate_maps = add_plate_map_constants(plate_maps, constants_df)
    
    return plate_maps
    
def get_constants_tab(fname):
    # Get the tab
    try:
        constants_df = pd.read_excel(fname, sheet_name = '_constants')
    except XLRDError as e:
        raise RuntimeError('A sheet named "_constants" must be specified in the workbook.')
    
    # Ensure it has a column named "Plate"
    if not 'Plate' in constants_df:
        raise RuntimeError('A column named "Plate" must be present in "_constants" tab')
    
    return constants_df

def split_plate(plate_combo):
    # define valid plate dimensions
    ROWS = [2, 3, 4, 6, 8, 16, 32]
    COLS = [3, 4, 6, 8, 12, 24, 48]

    plate_dict = {}
    plates_observed = []
    # plate_str rows still need to be split on ","
    for plate in plate_combo:
        row_len = len(plate) - 1
        col_len = set(len(col) - 1 for col in plate)
        if len(col_len) > 1:
            raise ValueError('Columns must be equal length')
        # next(iter(set)) converts set to numeric (we know this is ok from above)
        if (row_len, next(iter(col_len))) not in zip(ROWS, COLS):
            raise ValueError('Plate not valid dimension!\n' + \
                    'Must be: 6, 12, 24, 48, 96, 384, 1536\n' + \
                    'Dims: {}, {}'.format(row_len, col_len))
        plate_id = plate[0][0]
        plates_observed.append(plate_id)
        val = list(flatten(x[1:] for x in plate[1:]))
        plate_dict[plate_id] = val

    # ensure given plate names are unique (does not check for overlaps within the
    # multi-plate format - other code will do that during the enumeration process)
    if len(plate_dict.keys()) != len(plates_observed):
        raise ValueError('Plate Variables must be unique\n{}'.format(';'.join(plate_dict.keys())))

    return plate_dict
            

def check_plates_x_vars(plate_maps):
    """
    Ensure plates are the same across all variables

    Input:
    ------
    plate_maps :: dict
        {var1:{plate1:[val, ...], plate2:[val, ...],} var2:{plate1:[val, ...], ...}}

    Output:
    -------
    None (only raises an error)
    """
    plate_ids = set()
    for x in plate_maps.values():
        plate_ids.update(x.keys())
    
    missing_vars = {}
    for var_name in plate_maps.keys():
        for plate_id in plate_ids:
            if plate_maps[var_name].get(plate_id) is None:
                missing_vars.update({var_name : plate_id})
    if len(missing_vars) > 0:
        missing_plate_str = 'Variable\tPlate\n' + \
                '\n'.join('\t'.join(str(y) for y in x) for x in missing_vars.items())
        raise RuntimeError('The following plates are missing from their respective variables:\n{}'.format(missing_plate_str))


def get_plate_sizes(plate_maps):
    plate_sizes = defaultdict(set)
    
    #var_names = set()
    for var_name, plates in plate_maps.items():
        for plate_id, val in plates.items():
            #var_names.add(var_name)
            plate_sizes[plate_id].add(len(plate_maps[var_name][plate_id]))

    bad_size_plates = [plate for plate,sizes in plate_sizes.items() if len(sizes) > 1]
    if len(bad_size_plates) > 0:
        raise RuntimeError('The following plates have different sizes across the variables:\n{}'.format("\n".join(bad_size_plates)))
    plate_sizes = {plate_id: list(size)[0] for plate_id, size in plate_sizes.items()}

    return plate_sizes

def add_plate_wells(plate_maps):
    plate_maps = deepcopy(plate_maps)
    
    plate_sizes = get_plate_sizes(plate_maps)
    
    wells_dict = {plate_id:[f'{row}{col:02}' for row in row_letters(plate_size) for col in range(1, ncol_pl(plate_size) + 1)] for plate_id, plate_size in plate_sizes.items()}
    
    plate_maps['Sample_Well'] = wells_dict
    
    return(plate_maps)

def plate_maps_to_df(plate_maps):
    check_plates_x_vars(plate_maps)
    
    plate_maps = add_plate_wells(plate_maps)

    # Temporarily rename "index" column
    rename_index = False
    if 'index' in plate_maps:
        rename_index = True
        plate_maps['__index__'] = deepcopy(plate_maps['index'])
        del plate_maps['index']
    
    df = pd.concat([pd.DataFrame(x).reset_index().melt(id_vars = 'index', var_name = "Plate_ID", value_name = var_name).set_index(['index', 'Plate_ID']) for var_name, x in plate_maps.items()], axis=1, sort=True)
    
    df = df.reset_index().drop('index', axis=1).assign(foo = lambda df: df['Plate_ID'].map(lambda x: int(x.replace('Plate', '')))).sort_values(['foo', 'Sample_Well']).reset_index(drop=True).drop('foo', axis = 1)

    if rename_index:
        df.rename({'__index__':'index'}, axis = 'columns', inplace = True)
    
    return(df)


#-----------------------------------------------------------------------------


def nrow_pl(n):
    "Get number of rows in a plate of size n"
    res = sqrt(2 * n // 3)
    if not int(res) == res:
        res = sqrt(3 * n // 4)
        if not int(res) == res:
            raise ValueError(f'{n} is not a valid plate size!')
    return(int(res))

def ncol_pl(n):
    "Get number of columns in a plate of size n"
    res = sqrt(3 * n // 2)
    if not int(res) == res:
        res = sqrt(4 * n // 3)
        if not int(res) == res:
            raise ValueError(f'{n} is not a valid plate size!')
    return(int(res))

def row_letters(n):
    "Get letter names for each row of a plate of size n"
    def row_letter_gen():
        letters = string.ascii_uppercase
        for pre in [''] + list(letters):
            for x in letters:
                yield pre + x

    letters = row_letter_gen()
    nrow = nrow_pl(n)
    i = 0
    res = []
    while i < nrow:
        res.append(next(letters))
        i+=1

    return(res)

#-------------------------------------------------------------------------------

def flatten(listOfLists):
    "Flatten one level of nesting"
    return itertools.chain.from_iterable(listOfLists)

#-------------------------------------------------------------------------------

def enum_plates(plate_id):
    """
    Split a plate defined as "Plate1-3,5-7" into the 6 member plates.

    Input:
    ------
    plate_id :: str
        single or multi-plate specification

    Output:
    -------
    plate_ids :: list
        [plate_id_1, plate_id_2, ..., plate_id_n]
    """

    if not plate_id.startswith('Plate'):
        raise ValueError(f'"{plate_id}" is not a valid plate id (must start with "Plate").')
    plate_ids = []
    for x in plate_id.replace('Plate', '').split(','):
        try:
            split_x = [int(y) for y in x.split('-')]
        except ValueError as e:
            raise ValueError(f'"{plate_id}" not formatted correctly. The proper format is "PlateX-Y,W-Z", where X, Y, W, & Z are integers.')
        if len(split_x) > 2:
            raise ValueError(f'"{plate_id}" not formatted correctly. The proper format is "PlateX-Y,W-Z", where X, Y, W, & Z are integers.')
        if len(split_x) == 1:
            split_x = split_x * 2
        for z in range(*[y+i for i,y in enumerate(split_x)]):
            plate_ids.append(f'Plate{z}')
    return(plate_ids)

