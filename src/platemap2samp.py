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
REQ_VARS = set(['assay', 'index', 'index2'])


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
    # parse plates
    plate_maps = pm.read_plate_maps(args.sheet)
    plate_sizes = pm.get_plate_sizes(plate_maps)
    
    # ensure the plate level vars are acceptable
    pm.check_plates_x_vars(plate_maps)
    
    # Ensure required columns are in the plate maps
    if not REQ_VARS.issubset(plate_maps.keys()):
        raise ValueError('The following plate required variables are not present: {}\n'.format(', '.join(REQ_VARS - plate_maps.keys())))

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

