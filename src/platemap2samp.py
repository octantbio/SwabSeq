#!/usr/bin/env python3
"""
plate2samp.py -- CLI for generating samplesheets
Nathan Lubock and Scott Simpkins
"""
import re
import csv
import sys
import argparse
import itertools
import pandas as pd
import numpy as np
from collections import defaultdict

import plate_maps as pm

# easily change the required variables
# Plate_Primer = name of plate primer, not actual sequence
REQ_VARS = set(['bc_set', 'i5', 'i7'])


# silly over optimization to make a fast reverse compliment
# see: https://bioinformatics.stackexchange.com/q/3583
COMP = str.maketrans("ACTGacgt", "TGACtgca")
def rev_comp(seq):
    return seq.translate(COMP)[::-1]

#===============================================================================

def grouper(iterable, n, fillvalue=None):
    "Collect data into fixed-length chunks or blocks"
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return itertools.zip_longest(*args, fillvalue=fillvalue)

#-------------------------------------------------------------------------------

def prompt_header():
    """
    Prompt user for relevant sample sheet variables.

    Input:
    ------
    None

    Output:
    -------
    header :: str
        The header section of Illumina's sample sheet
    rc :: bool
        Do we need to reverse compliment

    Depends:
    --------
    re
    """
    name = input('\n\nName: ')
    experiment = input('Experiment Name: ')
    date = input('Date: ')
    instrument_types_i5_fwd = ['MiSeq', 'HiSeq 2X00', 'NovaSeq']
    instrument_types_i5_rev = ['iSeq', 'MiniSeq', 'NextSeq', 'HiSeq >3000']
    instrument = input(f'Instrument ({",".join(instrument_types_i5_fwd+instrument_types_i5_rev)}): ')
    while instrument not in instrument_types_i5_fwd+instrument_types_i5_rev:
        instrument = input(f'Instrument must be in {instrument_types_i5_fwd+instrument_types_i5_rev}.\nTry again: ')

    # set reverse compliment flag depending on instrument
    if instrument in instrument_types_i5_rev:
        rc = True
    else:
        rc = False

    reads = input('Cycles (enter values separated by "," for paired end e.g. 151,151): ')
    se = re.compile(r'^\d+$')
    pe = re.compile(r'^(\d+),(\d+)$')
    single = re.match(se, reads)
    paired = re.match(pe, reads)
    # recall ^ = xor
    if bool(single) ^ bool(paired) == False:
        while bool(single) ^ bool(paired) == False:
            reads = input('Reads must be separated by comma for paired end.\nTry again: ')
            single = re.match(se, reads)
            paired = re.match(pe, reads)

    # generate reads string based on match
    if paired:
        out_reads = '\n'.join(paired.groups())
    else:
        out_reads = reads

    # generate sample sheet header
    header = "[Header]\nIEMFileVersion,5\n" + \
    "Investigator Name," + name + "\n" + \
    "Experiment Name," + experiment  + "\n" + \
    "Date," + date + "\n" + \
    "Workflow,GenerateFASTQ\nApplication,FASTQ Only\n" + \
    "Instrument Type," + instrument + "\n" + \
    "Chemistry,Amplicon\n" + \
    "[Reads]\n" + out_reads + "\n" + \
    "[Settings]\n\n[Data]"

    return (header, rc)


#-------------------------------------------------------------------------------

def check_i5_i7_vars(plate_maps):
    i5_indices = set()
    i5_suffixes = set()
    n_i5 = 0
    for x in plate_maps.keys():
        if x.startswith('i5'):
            i5_indices.add(x)
            n_i5 += 1
            x_split = x.split('_', 1)
            if len(x_split) == 2:
                i5_suffixes.add(x_split[1])

    if len(i5_indices) == 0:
        raise ValueError('No i5 indices were specified!')

    if i5_indices != set(['i5']):
        if len(i5_suffixes) != n_i5:
            raise ValueError(f'i5 index variable(s) should be specified as either "i5" or "i5_<suffix>," but not both.\nCurrent i5 index variables: {i5_indices}')

    i7_indices = set()
    i7_suffixes = set()
    n_i7 = 0
    for x in plate_maps.keys():
        if x.startswith('i7'):
            i7_indices.add(x)
            n_i7 += 1
            x_split = x.split('_', 1)
            if len(x_split) == 2:
                i7_suffixes.add(x_split[1])

    if len(i7_indices) == 0:
        raise ValueError('No i7 indices were specified!')

    if i7_indices != set(['i7']):
        if len(i7_suffixes) != n_i7:
            raise ValueError(f'i7 index variable(s) should be specified as either "i7" or "i7_<suffix>," but not both.\nCurrent i7 index variables: {i7_indices}')

    if i5_suffixes != i7_suffixes:
        raise ValueError(f"i5 and i7 index suffixes must be the same. Currently they are {i5_suffixes} for the i5's and {i7_suffixes} for the i7's")

    # Create new plate map variable list that replaces all i5 and i7 variables
    # with just 'i5' and 'i7', for required variable checking downstream
    new_vars = [x for x in plate_maps.keys() if not (x.startswith('i5') or x.startswith('i7'))] + ['i5', 'i7']

    return new_vars, sorted(list(i5_suffixes))


#-------------------------------------------------------------------------------

def expand_samplesheet(df, idx_suff):

    i5_cols = [f'i5_{x}' for x in idx_suff]
    i7_cols = [f'i7_{x}' for x in idx_suff]

    i5_expanded_df = df.melt(id_vars = ['Sample_ID', 'Plate_ID', 'Sample_Well'], value_vars = i5_cols, value_name = 'i5', var_name = '__idx_id__')
    i5_expanded_df['__idx_id__'] = [x.split('_')[1] for x in i5_expanded_df['__idx_id__']]

    i7_expanded_df = df.melt(id_vars = ['Sample_ID', 'Plate_ID', 'Sample_Well'], value_vars = i7_cols, value_name = 'i7', var_name = '__idx_id__')
    i7_expanded_df['__idx_id__'] = [x.split('_')[1] for x in i7_expanded_df['__idx_id__']]

    # If there is a mixture of wells with single and multiple i5/i7 pairs,
    # remove any duplicated pairs within a well.  (Somewhere else throw an
    # error if the indices do not define a unique row in the SampleSheet)
    i5_i7_expanded_df = pd.merge(i5_expanded_df, i7_expanded_df)
    i5_i7_expanded_df = i5_i7_expanded_df[~i5_i7_expanded_df.duplicated(['Plate_ID', 'Sample_Well', 'i5', 'i7'])]

    df_exp = df.drop(i5_cols + i7_cols, axis = 'columns').merge(i5_i7_expanded_df)

    df_exp['Sample_ID'] = df_exp['Sample_ID'] + '-' + df_exp['__idx_id__']
    df_exp.drop('__idx_id__', axis = 'columns', inplace = True)

    return df_exp


#===============================================================================

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='')
    parser.add_argument('sheet',
                        type=str,
                        help='path to the plate map *.xlsx')
    parser.add_argument('-o',
                        '--out-file',
                        dest='out_file',
                        type=argparse.FileType('w'),
                        default='SampleSheet.csv',
                        help='sample sheet output')
    args = parser.parse_args()

    #---------------------------------------------------------------------------
    # parse plates
    plate_maps = pm.read_plate_maps(args.sheet)
    plate_sizes = pm.get_plate_sizes(plate_maps)

    # ensure the plate level vars are acceptable
    pm.check_plates_x_vars(plate_maps)

    # Check that i5/i7 variables are specified properly
    new_req_vars, index_suffixes = check_i5_i7_vars(plate_maps)

    # Ensure required columns are in the plate maps
    if not REQ_VARS.issubset(new_req_vars):
        raise ValueError('The following plate required variables are not present: {}\n'.format(', '.join(REQ_VARS - plate_maps.keys())))

    # Convert to a df
    out_df = pm.plate_maps_to_df(plate_maps)

    #---------------------------------------------------------------------------
    # Format the output samplesheet
    out_df['Sample_ID'] = out_df.Plate_ID + '-' + out_df.Sample_Well

    # Expand the df to accommodate multiple i5/i7 pairs per well, if necessary
    if len(index_suffixes) > 0:
        out_df = expand_samplesheet(out_df, index_suffixes)

    # Check to make sure each i5/i7 combination uniquely defines a row
    duplicated_index_rows = np.where(out_df.duplicated(['i5', 'i7'])).tolist()
    if len(duplicated_index_rows) > 0:
        dup_idx_err_str = 'i5/i7 pairs do not define unique rows in the SampleSheet! Offending duplicated rows:\n{}'.format(', '.join(duplicated_index_rows))
        raise ValueError(dup_idx_err_str)

    sample_header, rc = prompt_header()

    # reverse complement i7 - always reads the RC of the primer sequence
    out_df['i7'] = out_df.i7.map(rev_comp)

    # reverse complement i5 if using on NextSeq (MiSeq reads the primer sequence)
    if rc:
        out_df['i5'] = out_df.i5.map(rev_comp)

    # print header
    print(sample_header, file=args.out_file)

    # print the sample info
    (out_df.assign(index = out_df.i7, index2 = out_df.i5)
            .drop(['i5', 'i7'], axis = 'columns')
            .to_csv(args.out_file, index=False)
    )

