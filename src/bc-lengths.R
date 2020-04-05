#!/usr/bin/env Rscript

args = commandArgs(TRUE)

if (length(args) != 2) {
  stop('Usage: cat <*.conditions.csv> | Rscript bc-lengths.R <*.bc-map.csv> <*.conditions.csv (updated)>')
}

library(magrittr)
suppressPackageStartupMessages(library(tidyverse))

f = file('stdin')
samples = read_csv(f, guess_max=1e6)
libs = read_csv(args[1])

bc_lengths = libs %>%
  mutate(bc_len = str_length(sequence)) %>%
  select(assay, bc_len) %>%
  group_by(assay) %>%
  distinct() %>%
  summarize(bc_len = paste(bc_len, collapse = ',')) %>%
  ungroup()

multi_bc_len_assay = bc_lengths %>%
  filter(grepl(',', bc_len))

if(nrow(multi_bc_len_assay) > 0) {
  err_str =
    sprintf('All barcodes in the same assay group in %s must have the same length. These assay groups are in violation: %s',
            args[1], multi_bc_len_assay %>% pull(assay) %>% paste(collapse = ', '))
  stop(err_str)
}

samples %>%
  left_join(bc_lengths, by = 'assay') %>%
  write_csv(path = args[2])

