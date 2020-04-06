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
from collections import defaultdict

import plate_maps as pm

# easily change the required variables
# Plate_Primer = name of plate primer, not actual sequence
REQ_VARS = set([])


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

def flatten(listOfLists):
    "Flatten one level of nesting"
    return itertools.chain.from_iterable(listOfLists)

#-------------------------------------------------------------------------------

def check_req_vars(plate):
    """
    Ensure all required variables are named correctly and present in plates

    Input:
    ------
    plate_vars :: dict
        {var:[val, ...], var2:[val, ..]}

    Output:
    -------
    None only raises errors

    Depends:
    --------
    re
    REQ_VARS :: set
        all required variables
    """
    if not REQ_VARS.issubset(plate.keys()):
        raise ValueError('The following plate variables must be present: {}\n'.format(REQ_VARS) + \
                'Current plate variables:\n{}'.format(', '.join([*plate.keys()])))

    # check the chem_ID and ensure they conform to our standards, or that "Dummy" variable is set to true
    chem_id = re.compile(r'C-\d+')
    if False in [bool(chem_id.match(x)) | (y == 'TRUE') for x, y in zip(plate['chem_ID'], plate['Dummy'])]:
        raise ValueError('chem_ID must be C-X, where X is numeric!')

    # check the cell_library and ensure they conform to our standards, or that "Dummy" variable is set to true
    cell_library = re.compile(r'cb\d+|vl\d+')
    if False in [bool(cell_library.match(x)) | (y == 'TRUE') for x, y in zip(plate['cell_library'], plate['Dummy'])]:
        raise ValueError('cell_library must be cbX, where X is numeric!')

    # ensure the bc_promoter is in the acceptable set, or that "Dummy" variable is set to true
    if False in [(x in BC_PROMOTER) | (y == 'TRUE') for x, y in zip(plate['bc_promoter'], plate['Dummy'])]:
        raise ValueError('bc_promoter must be in {}\nYou have: {}'.format(BC_PROMOTER, set(plate['bc_promoter'])))

#-------------------------------------------------------------------------------

def check_well_bc(well_bc_df):
    """
    Ensure well barcode file is formatted properly

    Input:
    ------
    well_bc_df :: pandas df

    Output:
    -------
    None only checks df

    Depends:
    --------
    pandas as pd
    """
    if len(well_bc_df) != 384:
        raise ValueError('Must have 384 well barcodes!')
    elif 'Sample_Well' not in well_bc_df.columns:
        raise ValueError('Must have Sample_Well column in well barcodes!')
    elif 'Barcode' not in well_bc_df.columns:
        raise ValueError('Must have Barcode column in well barcodes!')

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
    instrument = input('Instrument (MiSeq,NextSeq,HiSeq): ')
    if instrument not in ['MiSeq', 'NextSeq', 'Hiseq']:
      while instrument not in ['MiSeq', 'NextSeq', 'Hiseq']:
        instrument = input('Instrument must be: MiSeq, NextSeq, or Hiseq.\nTry again: ')

    # set reverse compliment flag depending on instrument
    if instrument == 'NextSeq':
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
    # well barcode processing

    ## generate the 384 well index for joining barcodes
    #row_384 = 'A B C D E F G H I J K L M N O P'.split(' ')
    #col_384 = ['0' + str(x) for x in range(1,10)] + [str(x) for x in range(10,25)]
    #well_idx = [''.join(x) for x in itertools.product(row_384, col_384)]

    #if args.well_bc == 'BC_384_v2':
    #    well_bc = pd.DataFrame.from_dict({'Sample_Well':well_idx, 'Barcode':BC_384_v2})
    #elif args.well_bc == 'BC_384_v1':
    #    well_bc = pd.DataFrame.from_dict({'Sample_Well':well_idx, 'Barcode':BC_384_v1})
    #else:
    #    well_bc = pd.read_csv(args.well_bc)
    #check_well_bc(well_bc)

    #---------------------------------------------------------------------------
    # parse plates
    plate_maps = pm.read_plate_maps(args.sheet)
    plate_sizes = pm.get_plate_sizes(plate_maps)
    
    # ensure the plate level vars are acceptable
    pm.check_plates_x_vars(plate_maps)

    # Convert to a df
    out_df = pm.plate_maps_to_df(plate_maps)

    #---------------------------------------------------------------------------

    sample_header, rc = prompt_header()

    # reverse complement index1 - always reads the RC of the primer sequence
    out_df['index'] = out_df['index'].map(rev_comp)

    # reverse complement index2 if using on NextSeq (MiSeq reads the primer sequence)
    if rc:
        out_df.index2 = out_df.index2.map(rev_comp)

    # print header
    print(sample_header, file=args.out_file)

    # print the sample info
    (out_df.assign(Sample_ID = lambda df: df.Plate_ID + '-' + df.Sample_Well)
          .to_csv(args.out_file, index=False)
    )

