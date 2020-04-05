import re
import argparse
from pathlib import Path

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Create a folder with symlinks to all fastq\'s and a SampleSheet.csv in a sequencing directory. Note the name of the new folder will be the same as the input.')
    parser.add_argument('in_dir',
                        type=str,
                        help='path to sequencing run (or stdin if none)')
    parser.add_argument('-o', '--out-dir',
                        dest='out_dir',
                        type=str,
                        help='where to drop the folder of symlinks (default = current directory)',
                        default=''
                        )
    args = parser.parse_args()

    # dump links in to a folder with the run id
    in_dir = Path(args.in_dir)
    out_dir = Path(args.out_dir) / in_dir.name
    out_dir.mkdir(parents=True, exist_ok=True)

    # grab the samplesheet
    path_to_samplesheet = in_dir.joinpath('SampleSheet.csv').resolve()
    out_dir.joinpath('SampleSheet.csv').symlink_to(path_to_samplesheet)

    # grab the fastqs
    fastqs = in_dir.glob('Data/Intensities/BaseCalls/*.fastq*')
    for fq in fastqs:
        out_name = Path(fq).name
        if 'Undetermined' not in out_name:
            out_dir.joinpath(out_name).symlink_to(fq.resolve())

