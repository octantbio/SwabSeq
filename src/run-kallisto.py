import re
import gzip
import shlex
import shutil
import argparse
import itertools
import subprocess
from pathlib import Path
from xml.etree import ElementTree as ET

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Run Kallisto on Undetermined fastqs')
    parser.add_argument('fastqs',
                        nargs='+',
                        help="fastqs to parse"
                        )
    parser.add_argument('-i', '--index',
                        type=str,
                        required=True,
                        dest='index',
                        help='path to the kallisto index')
    parser.add_argument('-o', '--out-dir',
                        type=str,
                        required=True,
                        dest='out_dir',
                        help='path to output folder')
    parser.add_argument('-t', '--threads',
                        type=int,
                        default=1,
                        help='number of threads to use during demux')
    args = parser.parse_args()

    # make sure we have at most 4 fastqs
    if len(args.fastqs) > 4 or len(args.fastqs) < 3:
        raise ValueError(f'Must have between 2-4 fastqs')

    # will fail if fastqs aren't formatted correctly
    try:
        fastqs = {re.search(r'_[RI][12]_', x).group()[1:3]:x for x in args.fastqs}
    except AttributeError:
        print('fastqs must have _[RI][12]_ in them!')

    # check that we have 2 indices
    if sum('I' in x for x in fastqs.values()) != 2:
        raise ValueError(f'Must have 2 index fastqs. Found {idx_count}')

    # grab the index len and make sure they are the same for both files
    with gzip.open(fastqs['I1'], 'rt') as f:
        i1_len = len(list(itertools.islice(f, 1, 2))[0].rstrip())
    with gzip.open(fastqs['I2'], 'rt') as f:
        i2_len = len(list(itertools.islice(f, 1, 2))[0].rstrip())

    if i1_len != i2_len:
        raise(ValueError(f'Index 1 & 2 must be same length (either 8 or 10)\ni1 - {i1_len}\ni2 - {i2_len}'))
    elif i1_len not in [8,10] or i2_len not in [8,10]:
        raise(ValueError(f'Index 1 & 2 must be same length (either 8 or 10)\ni1 - {i1_len}\ni2 - {i2_len}'))

    # set swabseq flag depending on input
    if i1_len == 8:
        index_len = ''
    else:
        index_len = '10'

    # process out_dir
    out_dir = Path(args.out_dir)

    # generate kallisto call
    fastq_order = [fastqs['I1'], fastqs['I2'], fastqs['R1']]
    if len(fastqs) == 4:
        fastq_order.append(fastqs['R2'])

    kallisto = f'kallisto bus -x SwabSeq{index_len} --index {args.index} --threads {args.threads} --output-dir {out_dir}'
    p = subprocess.Popen(shlex.split(kallisto) + fastq_order)
    exit_code = p.wait()
