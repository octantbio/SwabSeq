import shlex
import shutil
import argparse
import subprocess
from pathlib import Path
from xml.etree import ElementTree as ET

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Dump sequencing data to Undetermined*.fastq.gz')
    parser.add_argument('seq_folder',
                        type=str,
                        help='path to the sequencing data')
    parser.add_argument('out_folder',
                        type=str,
                        help='path to put demuxed fastqs')
    parser.add_argument('-t', '--threads',
                        type=int,
                        default=1,
                        help='number of threads to use during demux')
    args = parser.parse_args()

    # figure out bases mask
    input_path = Path(args.seq_folder)
    tree = ET.parse(input_path / 'RunInfo.xml')
    root = tree.find('./Run/Reads')

    mask = []
    for read in root:
        if read.attrib['IsIndexedRead'] == 'Y':
            mask.append(f'I{read.attrib["NumCycles"]}')
        else:
            mask.append(f'Y{read.attrib["NumCycles"]}')

    bcl2fastq = f'bcl2fastq --runfolder-dir {args.seq_folder} --output-dir {args.out_folder} --create-fastq-for-index-reads --use-bases-mask {",".join(mask)} --processing-threads {args.threads} --no-lane-splitting --sample-sheet /dev/null'

    # run bcl2fastq
    p = subprocess.Popen(shlex.split(bcl2fastq))
    exit_code = p.wait()
