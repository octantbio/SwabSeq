#!/usr/bin/awk

BEGIN {
  print "Barcode length:", bc_len > "/dev/stderr"
} {
  if(NR % 4 == 2) {
    a[substr($1, 1, bc_len)]++
  }
} END {
  for(bc in a) {
    print bc, a[bc]
  }
}



