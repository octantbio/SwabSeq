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
import pygsheets
from collections import defaultdict

import plate_maps as pm

# easily change the required variables
# Plate_Primer = name of plate primer, not actual sequence
REQ_VARS = set(['cell_library', 'bc_promoter', 'chem_ID', 'molarity', 'Sample_Plate', 'Dummy'])
BC_PROMOTER = set(['cag', 'cre', 'gal4uas', 'mixed'])

# hardcode in 384 barcodes
BC_384_v1 = [
    'GAAGACTC','GCCTAATG','TTGGCCCA','CCAACAAT','CAACGGGA','AAGTGTGT','TGGAATGG','CCCGTTAG',
    'TCCTATGG','CTACACTG','TGAGAATC','TAAGAAGG','GTCTTAGA','TATGCCGC','TCGTCAAT','TCAGGAGC',
    'AGGATTGC','AACGACAT','GCCGAGAA','TAGCCCTG','GCTTGGCT','TCAGGCTT','CTCTGTAG','CGACTACG',
    'GAGCAGAA','GTGTGCAC','TGAGCTTT','CTGAGGTC','TTGGAAAG','AGCCAAGA','TAGACGCG','TAGCGCGA',
    'GAATGGAT','TACTGGGC','CGTCGGTA','CGTATGGA','GACATGTT','TATAGTCG','CTTTGGGT','CGATCGAT',
    'CATCCAAC','GCACTAAG','GCGAAATA','ATACATGG','AACGTGGC','TACACGAC','CGACTTTA','GTGATCGC',
    'GAGAGTGC','GTATCTGA','AGGGACTG','GTTAGGGC','TGATGCAG','CGATACCG','CCATACTT','GCGCGAAT',
    'ACCTTGAT','ATGCACAA','CAGCACAG','CTACGGAC','TCTTGAAC','GAACGGTG','TCAACTCG','TCGTGCTC',
    'CACGAACT','AGTTGATG','AGATCTCG','TCTGGCCA','ATGGTGAA','ATGCATTC','AGGGTCCA','GTGCTATC',
    'GTCGTCGT','ATACTGAG','TAGCTAAG','GTAAACAG','GTGGGACA','CCTCAGGA','TGGAACTA','GAGTCATG',
    'GCGCTTAC','ACTGGGTT','CCCTCAAA','TGTCGGCT','GCGGGTTT','AGCCCTAC','AATCGTCT','ATCATCCT',
    'GCCATTAT','ACGCCAAG','GCACAGCT','TTGGACTC','TGGTATTC','AAGCTCCT','TAAGTCAC','GTTCCAAA',
    'TATGGAAG','ACTTCTGG','GTCCTGTG','CCGCTAGA','ACAACCTC','AGTGGCAG','TAACTAGC','TGCGTGAC',
    'CGACACAC','GAGTGGGA','GTAACACT','ATCGCAAG','TTCATCGG','CCTGTTGC','CCCATATT','GAGAGATT',
    'GAACATCA','ACTGTGGG','CACTTAAC','AGTCTCGG','GTTTCGAT','TGAGTTAG','CGTGACGA','CTATCATG',
    'TCAGGGAA','GCACTCTT','CGGAAGCA','TACGCCAG','TCTTCTCA','ACGGAGGA','ATGCGGGA','ATCGAGGG',
    'CCGTCTAG','CGTGAGAG','AATCGGAA','TGGCAACT','GATCTAGG','AACCACGC','CGCCTAAA','CAAACTTG',
    'ACTCCCGA','CTTCCTCG','AAACGTAC','CCTACATA','TCCTGATT','CCCTACGA','ATGGGCCT','TGATCGGG',
    'GTCTATCA','GTATAGTG','AGCCTATG','CCTACCAG','TTCAGGGA','CTTTATGG','TGTTCCAT','ACTTGAGT',
    'TCACTTTC','CCGTAAGC','TTCGGCAC','GCTAAGGG','CAGAGGGT','TGTGTGTG','AGTCTGAC','ACTAGATC',
    'GAGCTGGT','ACCATTTG','ACGTCGCA','TGACTCGA','TATGACCT','CACGGAGA','AAGTGACA','CTTGCTAT',
    'AACTCGTG','CGTGCATG','ATCTCATC','TGCGGGTA','AGGTCCGA','TGAAGGGC','CCCAGTTC','ATGAGTCA',
    'ACCTGAAG','AGAACGGA','TCAGTTCT','TGGGTAGG','CATGATAC','AGAGCGTG','CTAGTAGT','ACGATTCT',
    'TCACCAGA','ACCACAAC','CAGGTATG','ATCCCTTG','AGTACCCA','GACGGTAA','CTTATAGC','CTCTGACT',
    'AGGACTTG','AAGATGTC','CTGGTTCT','TTCCAAGG','ATGATAGG','TTTCTCGT','GACGAATA','GTTTGCGG',
    'CCAATTGT','GTGGTCAG','TTCCTGGC','TCGACACA','CCCTAGTC','CTCTTCAA','ATTAGCGT','CAAGCGAC',
    'CTAACGGT','TGCCTTGT','AGCTAGAC','CAATTGCG','TCTGATGA','GTGTTCTT','TCGATGAA','TCCATTGC',
    'AATGCTAG','TTGCCTGG','GTGCGCTA','ACAGATTC','GCAAGGTC','GTGTACGA','ACTCTGCT','ACTAGGCA',
    'CCAATGAC','GTAAGTTG','AAAGCCAA','AGCACGTC','GTACTTGT','AGGCTGTT','CTCATTGA','CATTACGT',
    'TCCTTCTA','AAGCGCTC','TAGTACGG','CGAGATAT','CAGGACTA','TATTCGAG','TTACCTCA','TCATCGCT',
    'AGTGTACG','CAGACTCT','ACGTCCTT','ACGTGTAA','TGCAGAAC','ATCCCAGT','GTTCATGA','GACATCAG',
    'CTAGGATA','TTCTGTTC','CACCCGTA','CAAGTCGA','TAACTCCG','TAAATGGG','GACTCCGA','TACAGAGG',
    'TTTCGCTG','CACCAGAC','ACACCGAA','GATGTCCA','TGCTAAAG','CTAGAGAA','CTGCTGTA','ATCACGAT',
    'GACCGTGT','GCAATACA','AGCAGTCT','GCTGCAAT','GAAACCGT','GTTCGATT','TTACGGTA','TTATCGTC',
    'GACTTTGC','ACCAAGGC','ATAACTGC','CGTTTCAG','GACCCATC','ACATTCCT','TACCGACA','ACACACAT',
    'CCTACGCT','CGGTGGAA','AAGGCTGC','AAGTCAAC','CTCTCCTT','TACACTGA','GTCTTCCG','AATAGCTG',
    'TTCTTGAG','CGTTACTC','CATTCTGA','CGCATGAT','AGAAGAAG','CATGTGTA','ATGCCGAC','AGGCCTCA',
    'CGAAGATC','GTACGCCT','TGGACTAC','TACCGGAG','TGCTATCT','GATGTGAC','TGGCTATA','GACGTAAT',
    'TTGAGTAG','CCTAAAGT','GTCAGCAT','TCGCGGTT','ATGTCCAG','CAGAAAGA','ATGACGTA','CTTTCCAC',
    'GCTCCATG','CATTGATC','AACGGACG','CGTCCAGA','CACAATGC','TCTTGGGA','TAACCGGT','CACCTCGT',
    'GCCTACAT','GTACAGGC','CCCTTTCT','GTGGCAGT','AACAAGAG','TTCACATG','ACGGCATC','ATTGACAC',
    'GTTGAATC','TCTAGTGT','TGGATCAT','TGTACGTA','TGCATCTC','CTGCCAAT','CGTTCTCT','AGACCAGC',
    'CAAAGGAG','CATTGCAA','TGCCGCAA','TACATGCA','TCTGAGAT','GTGGATTA','GAGCCACT','TGTCGAGC',
    'GATGCGCT','GTTCAGAG','CAGCTTCA','TTGGCGAT','CGGCATGA','GATTCGTC','CTGAACCG','TGCTCGTT',
    'GCAGTGTG','CCAAGCTA','CCAGCTCA','ACTGAATG','TGTGCAAC','AGGGCTAT','TTTGCGGA','CTCCATAA',
    'CGCGCAAT','CGGTCATA','CCAGATGG','TACTGCCG','CAGTTGGC','GAGGAAGC','TCCAGTAA','CGTAGCCT',
    'TGGTTTGA','TATCCCAA','CAACCCTT','TAACGCAT','CCTAATTG','CAGCGATA','TGACGTCG','TGTGGCTC',
    'CAGTCCCA','TGAGACGT','CGAACTAA','GAGCCTTA','TTGTAGGC','CCGTTCAC','CCGAATAA','GCTACGAC'
]

BC_384_v2 = [
    'GAAGACTC','GATAGAAC','TTGGCCCA','CCAACAAT','CAACGGGA','AAGTGTGT','TGGAATGG','CCCGTTAG',
    'TCCTATGG','CTACACTG','TGAGAATC','TAAGAAGG','GTCTTAGA','TATGCCGC','TCGTCAAT','TCAGGAGC',
    'AGGATTGC','AACGACAT','GCCGAGAA','TAGCCCTG','GCTTGGCT','TCAGGCTT','CTCTGTAG','CGACTACG',
    'GAGCAGAA','GTGTGCAC','TGAGCTTT','CTGAGGTC','TTGGAAAG','AGCCAAGA','TAGACGCG','TAGCGCGA',
    'GAATGGAT','TACTGGGC','CGTCGGTA','CGTATGGA','GACATGTT','TATAGTCG','CTTTGGGT','CGATCGAT',
    'CATCCAAC','TCACATAG','GCGAAATA','ATACATGG','AACGTGGC','TACACGAC','CGACTTTA','GTCCGAAG',
    'GAGAGTGC','GTATCTGA','AGGGACTG','GTTAGGGC','TGATGCAG','CGATACCG','CCATACTT','GCGCGAAT',
    'ACCTTGAT','ATGCACAA','CAGCACAG','CTACGGAC','TCTTGAAC','GAACGGTG','TCAACTCG','TCGTGCTC',
    'CACGAACT','AGTTGATG','AGATCTCG','TCTGGCCA','ATGGTGAA','ATGCATTC','AGGGTCCA','GTGCTATC',
    'GTCGTCGT','ATACTGAG','TAGCTAAG','GTAAACAG','GTGGGACA','CCTCAGGA','TGGAACTA','GAGTCATG',
    'GCGCTTAC','ACTGGGTT','CCCTCAAA','TGTCGGCT','GCGGGTTT','AGCCCTAC','AATCGTCT','ATCATCCT',
    'GCCATTAT','ACGCCAAG','GCACAGCT','TTGGACTC','TGGTATTC','AAGCTCCT','TAAGTCAC','GTTCCAAA',
    'TATGGAAG','ACTTCTGG','GTCCTGTG','CCGCTAGA','ACAACCTC','AGTGGCAG','TAACTAGC','TGCGTGAC',
    'CGACACAC','GAGTGGGA','GTAACACT','ATCGCAAG','TTCATCGG','CCTGTTGC','CCCATATT','GAGAGATT',
    'GAACATCA','ACTGTGGG','CACTTAAC','AGTCTCGG','GTTTCGAT','TGAGTTAG','CGTGACGA','CTATCATG',
    'TCAGGGAA','GCACTCTT','CGGAAGCA','TACGCCAG','TCTTCTCA','ACGGAGGA','ATGCGGGA','ATCGAGGG',
    'CCGTCTAG','CGTGAGAG','AATCGGAA','TGGCAACT','GATCTAGG','AACCACGC','TTCGATCG','CAAACTTG',
    'ACTCCCGA','CTTCCTCG','AAACGTAC','CCTACATA','TCCTGATT','CCCTACGA','ATGGGCCT','TGATCGGG',
    'GTCTATCA','GTATAGTG','AGCCTATG','CCTACCAG','TTCAGGGA','CTTTATGG','TGTTCCAT','ACTTGAGT',
    'TCACTTTC','GCAGAAAC','TCCAGCCT','AGCTTAGT','CAGAGGGT','TGTGTGTG','AGTCTGAC','ACTAGATC',
    'GAGCTGGT','ACCATTTG','ACGTCGCA','TGACTCGA','TATGACCT','CACGGAGA','AAGTGACA','CTTGCTAT',
    'AACTCGTG','CGTGCATG','ATCTCATC','TGCGGGTA','AGGTCCGA','TGAAGGGC','CCCAGTTC','ATGAGTCA',
    'ACCTGAAG','AGAACGGA','TCAGTTCT','TGGGTAGG','CATGATAC','AGAGCGTG','CTAGTAGT','ACGATTCT',
    'TCACCAGA','ACCACAAC','CAGGTATG','ATCCCTTG','AGTACCCA','CCTTGGTG','CTTATAGC','CTCTGACT',
    'AGGACTTG','AAGATGTC','CTGGTTCT','TTCCAAGG','ATGATAGG','TTTCTCGT','GACGAATA','GTTTGCGG',
    'CCAATTGT','GTGGTCAG','TTCCTGGC','TCGACACA','CCCTAGTC','CTCTTCAA','ATTAGCGT','CAAGCGAC',
    'CTAACGGT','TGCCTTGT','AGCTAGAC','CAATTGCG','TCTGATGA','CGTCTATT','TCGATGAA','TCCATTGC',
    'AATGCTAG','TTGCCTGG','GTGCGCTA','ACAGATTC','GCAAGGTC','ATGTTTCG','ACTCTGCT','ACTAGGCA',
    'CCAATGAC','GTAAGTTG','AAAGCCAA','AGCACGTC','GTACTTGT','AGGCTGTT','CTCATTGA','CATTACGT',
    'TCCTTCTA','AAGCGCTC','TAGTACGG','CGAGATAT','CAGGACTA','TATTCGAG','TTACCTCA','TCATCGCT',
    'AGTGTACG','CAGACTCT','ACGTCCTT','CTATTGGA','TGCAGAAC','ATCCCAGT','GTTCATGA','GACATCAG',
    'CTAGGATA','TTCTGTTC','CACCCGTA','CAAGTCGA','TAACTCCG','TAAATGGG','GACTCCGA','TACAGAGG',
    'TTTCGCTG','CACCAGAC','ACACCGAA','GATGTCCA','TGCTAAAG','CTAGAGAA','CTGCTGTA','ATCACGAT',
    'GACCGTGT','GCAATACA','AGCAGTCT','GCTGCAAT','GAAACCGT','GTTCGATT','TTACGGTA','TTATCGTC',
    'GACTTTGC','ACCAAGGC','ATAACTGC','CGTTTCAG','GACCCATC','ACATTCCT','TACCGACA','ACACACAT',
    'CCTACGCT','CGGTGGAA','AAGGCTGC','AAGTCAAC','CTCTCCTT','TACACTGA','GTCTTCCG','AATAGCTG',
    'TTCTTGAG','CGTTACTC','CATTCTGA','CGCATGAT','AGAAGAAG','ATGTCACT','ATGCCGAC','AGGCCTCA',
    'CGAAGATC','GTACGCCT','TGGACTAC','TACCGGAG','TGCTATCT','GATGTGAC','TGGCTATA','GACTGCTT',
    'TTGAGTAG','CCTAAAGT','GTCAGCAT','TCGCGGTT','ATGTCCAG','CAGAAAGA','ATGACGTA','CTTTCCAC',
    'GCTCCATG','CATTGATC','AACGGACG','CGTCCAGA','CACAATGC','TCTTGGGA','TAACCGGT','CACCTCGT',
    'GCCTACAT','GTACAGGC','CTTTCGTA','CTGCTTAG','AACAAGAG','TTCACATG','ACGGCATC','ATTGACAC',
    'GTTGAATC','TCTAGTGT','TGGATCAT','TGTACGTA','TGCATCTC','CTGCCAAT','CGTTCTCT','AGACCAGC',
    'CAAAGGAG','CATTGCAA','TGCCGCAA','TACATGCA','TCTGAGAT','GTGGATTA','GAGCCACT','TGTCGAGC',
    'GATGCGCT','GTTCAGAG','CAGCTTCA','TTGGCGAT','CGGCATGA','GATTCGTC','CTGAACCG','TGCTCGTT',
    'GCAGTGTG','CCAAGCTA','CCAGCTCA','ACTGAATG','TGTGCAAC','AGGGCTAT','TTTGCGGA','CTCCATAA',
    'CGCGCAAT','CGGTCATA','CCAGATGG','TACTGCCG','CAGTTGGC','GCTGACTT','TCCAGTAA','CGTAGCCT',
    'TGGTTTGA','TATCCCAA','CAACCCTT','TAACGCAT','CCTAATTG','CAGCGATA','TGACGTCG','TGTGGCTC',
    'CAGTCCCA','TGAGACGT','CGAACTAA','GAGCCTTA','TTGTAGGC','CCGTTCAC','TCGGTCGT','GCTACGAC'
]


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
    parser.add_argument('url',
                        type=str,
                        help='url to to sheet')
    parser.add_argument('-d',
                        '--credentials-dir',
                        dest='cred',
                        type=str,
                        default='./',
                        help='directory of gsheet credentials')
    parser.add_argument('-x',
                        '--secret',
                        dest='secret',
                        type=str,
                        default='pygsheets.json',
                        help='path to pygsheets secret')
    parser.add_argument('-w',
                        '--well-barcodes',
                        dest='well_bc',
                        type=str,
                        default='BC_384_v2',
                        help='csv of well barcodes')
    parser.add_argument('-o',
                        '--out-file',
                        dest='out_file',
                        type=argparse.FileType('w'),
                        default='SampleSheet.csv',
                        help='sample sheet output')
    parser.add_argument('-s',
                        '--stamp',
                        dest='stamp',
                        action='store_true',
                        help='input is 96 well plate that will be stamped')
    args = parser.parse_args()

    #---------------------------------------------------------------------------
    # well barcode processing

    # generate the 384 well index for joining barcodes
    row_384 = 'A B C D E F G H I J K L M N O P'.split(' ')
    col_384 = ['0' + str(x) for x in range(1,10)] + [str(x) for x in range(10,25)]
    well_idx = [''.join(x) for x in itertools.product(row_384, col_384)]

    if args.well_bc == 'BC_384_v2':
        well_bc = pd.DataFrame.from_dict({'Sample_Well':well_idx, 'Barcode':BC_384_v2})
    elif args.well_bc == 'BC_384_v1':
        well_bc = pd.DataFrame.from_dict({'Sample_Well':well_idx, 'Barcode':BC_384_v1})
    else:
        well_bc = pd.read_csv(args.well_bc)
    check_well_bc(well_bc)

    #---------------------------------------------------------------------------
    # parse plates
    gsheet = pygsheets.authorize(client_secret=args.secret, credentials_directory=args.cred)
    in_sheets = gsheet.open_by_url(args.url)

    # UPDATE: now ignores worksheets that start with "_", to enable adding sheets that are
    # either required or not required for other functions, one example being fluid and plate
    # info for the D300 config file writer
    plate_maps = pm.read_plate_maps(in_sheets)
    plate_sizes = pm.get_plate_sizes(plate_maps)
    
    # ensure the plate level vars are acceptable
    pm.check_plates_x_vars(plate_maps)

    #---------------------------------------------------------------------------
    # 96-well stamping

    # This needs to be revisited - will fail if we try to use the --stamp argument
    if args.stamp:
        # generate 384 well plate in our standard stamp from 96-well index
        double_idx = [(x,x) for x in range(96)]
        long_row = [list(flatten(x)) for x in grouper(double_idx, 12)]
        plate_384 = list(flatten((x,x) for x in long_row))

        # build a dataframe from all plate csv's
        # should throw error if cols are not identical
        df_list = []
        for plate, val_dict in plate_dict.items():
            if any(len(x) != 96 for x in iter(val_dict.values())):
                raise ValueError('Must have 96 well input with --stamp option!')
            plate_df = pd.DataFrame(
                    {key:[val[x] for x in flatten(plate_384)] for key, val in val_dict.items()})
            plate_df['Sample_Well'] = well_idx
            df_list.append(plate_df)
    else:
        #df_list = []
        #for plate, val_dict in plate_dict.items():
        #    plate_df = pd.DataFrame(val_dict)
        #    plate_df['Sample_Well'] = well_idx
        #    df_list.append(plate_df)
        out_df = pm.plate_maps_to_df(plate_maps)

    #---------------------------------------------------------------------------
    # reverse compliment index if miseq

    sample_header, rc = prompt_header()
    plate_bcs = pd.read_csv('https://docs.google.com/spreadsheets/d/1uo9gy4V8UIce_SqZL0jQQlsk-RdDx4w87VaH3xDu5ec/export?gid=0&format=csv')
    if rc:
        plate_bcs['seq'] = plate_bcs[['index_on_primer']].applymap(rev_comp)
    else:
        plate_bcs['seq'] = plate_bcs[['index_on_primer']]

    # print data section
    # rename plate primer DB cols to match samplesheet
    print(sample_header, file=args.out_file)
    (plate_bcs[['seq', 'primer_name']]
            .rename(columns = {'primer_name':'Sample_Plate', 'seq':'index2'})
            .merge(out_df.drop('Plate_ID', axis=1), how='inner')
            .merge(well_bc, how='inner')
            .assign(Sample_ID = lambda df: df.Sample_Plate + "-" + df.Sample_Well)
            .rename(columns = {'Barcode':'index'})
            .sort_values(by=['Sample_Plate','Sample_Well'])
            .to_csv(args.out_file, index=False)
    )

