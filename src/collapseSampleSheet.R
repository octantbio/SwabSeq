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
  # Regenerate the Sample_ID to reflect just the plate and well
  mutate(Sample_ID = paste(Plate_ID, Sample_Well, sep='-')) %>%
  # Collapse the indices within each well
  group_by_at(vars(-index, -index2)) %>%
  summarize(
    index = paste(index, collapse='-'), 
    index2 = paste(index2, collapse='-')
  ) %>%
  format_csv() %>%
  writeLines(stdout()) # Write to stdout as csv
