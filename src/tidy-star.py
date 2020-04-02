"""
tidy-star.py - a quick and dirty starcode tidy'er
Nathan Lubock
"""

import argparse
import sys
from signal import signal, SIGPIPE, SIG_DFL

# catch broken pipe errors to allow ex) python pyParse.py foo bar | head
# see: https://stackoverflow.com/a/30091579
signal(SIGPIPE, SIG_DFL)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Tidy up starcode\'s --print-cluster column')
    parser.add_argument('infile',
                        type=argparse.FileType('r'),
                        default=sys.stdin,
                        nargs='?',
                        help='path to a file of the reads (or stdin if none)')
    args = parser.parse_args()

    # starcode always outputs a tsv with the third column split by ,'s
    for raw_line in args.infile:
        line = raw_line.rstrip().split('\t')
        for bc in line[2].split(','):
            print('{}\t{}\t{}'.format(line[0], line[1], bc), file=sys.stdout)
