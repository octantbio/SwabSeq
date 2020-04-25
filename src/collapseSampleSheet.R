#!/usr/bin/env Rscript

args = commandArgs(TRUE)

if (length(args) > 0) {
  stop('Usage: cat <*.conditions.csv> | Rscript collapseSampleSheet.R > <*.conditions.csv (updated)>')
}

library(magrittr)
suppressPackageStartupMessages(library(tidyverse))

f = file('stdin')
samples = read_csv(f, guess_max=1e6)

samples %>%
  mutate(Sample_ID = paste(Plate_ID, Sample_Well, sep='-')) %>% # Regenerate the Sample_ID to reflect just the plate and well
  group_by_at(vars(-index, -index2)) %>%
  summarize(index = paste(index, collapse=','), index2 = paste(index2, collapse=',')) %>% # Collapse the indices within each well
  format_csv() %>%
  writeLines(stdout()) # Write to stdout as csv

