"""
strip-windows.py - strip the pesky ^M's from any file
Nathan Lubock
"""

import sys
import argparse
from signal import signal, SIGPIPE, SIG_DFL

# catch broken pipe errors to allow ex) python pyParse.py foo bar | head
# see: https://stackoverflow.com/a/30091579
signal(SIGPIPE, SIG_DFL)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Strip any ^M and leave normal \n in place')
    parser.add_argument('infile',
                        type=argparse.FileType('r'),
                        default=sys.stdin,
                        nargs='?',
                        help='path to file (or stdin if none)')
    args = parser.parse_args()
    slurp = args.infile.read()

    # remove weird unicode garbage
    if slurp[0] == '\ufeff':
        slurp = slurp[1:]

    # test the three lind ending cases
    if '\r\n' in slurp:
        delim = '\r\n'
    elif '\r' in slurp:
        delim = '\r'
    else:
        delim = '\n'
    for line in slurp.split(delim):
        print(line, file=sys.stdout)
