#!/usr/bin/env Rscript

args = commandArgs(TRUE)

if (length(args) != 2) {
  stop('Usage: cat <*.conditions.csv> | Rscript bc-lengths.R <*.bc-map.xlsx> <*.conditions.csv (updated)>')
}


library(readxl)
library(magrittr)
suppressPackageStartupMessages(library(tidyverse))


#samples = read_csv('pipeline/scott_test.conditions.csv') # Eventually this is stdin
f = file('stdin')
samples = read_csv(f, guess_max=1e6)
libs = read_xlsx(args[1], sheet='assay_seqs')

bc_lengths = libs %>%
  mutate(bc_len = str_length(sequence)) %>%
  select(assay, bc_len) %>%
  group_by(assay) %>%
  distinct() %>%
  summarize(bc_len = paste(bc_len, collapse = ','))

new_samples = samples %>%
  left_join(bc_lengths, by = 'assay') %>%
  write_csv(path = args[2])

