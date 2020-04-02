#!/bin/bash

[[ $# -ne 2 ]] && echo 'Usage: starcode.sh <*.fastq.gz file> <*.csv condition table>'

fname=$1
fbase=${fname##*/}
sampid=${fbase%%_*}

conds=$2

#>&2 echo python src/extract-from-tab.py ${conds} ${sampid} bc_len 
BC_LEN="$( python src/extract-from-tab.py ${conds} ${sampid} bc_len )"

#>&2 echo "${BC_LEN}"

zcat ${fname} \
    | awk -v bc_len="${BC_LEN}" 'NR % 4 == 2{a[substr($1, 1, bc_len)]++} END {for(bc in a) print bc, a[bc]}' \
    | starcode -d2 -t1 --sphere --print-clusters 2> /dev/null \
    | python src/tidy-star.py \
    | awk -v name="${fbase}" '{split(name, a, "_"); print a[1], $1, $2, $3}' OFS=","
