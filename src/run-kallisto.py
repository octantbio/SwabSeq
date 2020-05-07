import re
import shlex
import shutil
import argparse
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
    parser.add_argument('-l', '--index-len',
                        type=int,
                        dest='index_len',
                        choices=[8,10],
                        default=10,
                        help='length of i7/i5 index (10 default)')
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

    # set swabseq flag depending on input
    if args.index_len == 8:
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
