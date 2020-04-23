Primer Order Postmortem + Fix
================
Nate
04/23/2020

  - [Intro](#intro)
      - [What Went Wrong…](#what-went-wrong)
      - [The Fix](#the-fix)
  - [Checking Purchased Primers](#checking-purchased-primers)
      - [Internal Consistency](#internal-consistency)
      - [Generated vs Purchased
        Agreement](#generated-vs-purchased-agreement)
      - [Sequence Checks](#sequence-checks)
  - [Standardizing on S2](#standardizing-on-s2)
      - [Checking RPP30](#checking-rpp30)
      - [Output](#output)

# Intro

We were trying to choose 384 index pairs for S2 and Rpp30 from the 1536
we generated with `./index-design.ipynb` (saved at
`./frozen-data/frozen-primer-set.tsv`). To avoid any hidden biases
caused by the particular ordering (originally sorted by min well dG) we
selected 384 pairs at random.

## What Went Wrong…

We indeed sampled 384 index pairs keeping N1, S2, and Rpp30.
Unfortunately we made 3 separate sets. THIS WAS A MISTAKE\! Rpp30 is
present in the N1 and S2 wells, and thus must have the same index pairs.
Explicitly, we would need two sets: N1+Rpp30 and S2+Rpp30.

## The Fix

To rectify this mistake, we are going to standardize on the S2 index
pairs, and order the corresponding 384 RPP30 primers. We are also
ignoring the N1 set which we never ordered.

### Original Code - Included for Posterity

``` r
library(readxl)
library(writexl)
library(magrittr)
library(tidyverse)

wide.primers <- read_tsv(
  './frozen-data/frozen-primer-set.tsv', 
  col_names = c('f_idx', 'f_primer', 'set', 'r_idx', 'r_primer')
) %>% 
  group_by(set) %>%
  mutate(pair_num = seq(1536)) %>%
  ungroup()
```

``` r
# randomly sample 384 pairs per group
# save them for future experiments
# also add the pair number so we can track them post split
set.seed(3308004)
sample.set <- wide.primers %>%
  group_by(set) %>%
  sample_n(384) %>%
  ungroup() 

# save 384 well index
well.idx <- expand_grid(col=LETTERS[1:16], row=seq(24)) %>%
  mutate(well = paste0(col, row)) %$%
  well

# tidy them up and output into an excel file
out.384 <- sample.set %>%
  group_by(set) %>%
  mutate(`Well Position` = well.idx) %>%
  pivot_longer(
    cols = c(-set, -`Well Position`, -pair_num),
    names_to = c('orientation', '.value'),
    names_sep = "_"
  ) %>%
  ungroup() %>%
  unite(Name, set, pair_num, orientation, idx, sep="_", remove = FALSE) %>%
  unite(out_name, set, orientation, sep = "_") %>%
  select(out_name, Name, `Well Position`, Sequence = primer) 

# do the actual writing (foo is a dummy var)
# foo <- out.384 %>%
#   nest(data = c(-out_name))  %>%
#   mutate(foo = walk2(out_name, data, ~write_csv(.y, path=paste0(.x, '.csv'))))
```

We also ordered a smaller subset of 24 back-up primers that we will
ignore. Also included for posterity.

``` r
# remember drop the N1 set here.
set.seed(42)
small.samp <- wide.primers %>%
  filter(set != 'N1') %>%
  anti_join(sample.set) %>%
  group_by(set) %>%
  sample_n(24) %>%
  ungroup()

# make the 96 well index
well.idx.96 <- expand_grid(col=LETTERS[1:8], row=seq(12)) %>%
  mutate(well = paste0(col, row)) %$%
  well

out.24 <- small.samp %>%
  pivot_longer(
    cols = c(-set, -pair_num),
    names_to = c('orientation', '.value'),
    names_sep = "_"
  ) %>%
  arrange(set, orientation) %>%
  mutate(`Well Position` = well.idx.96) %>%
  unite(Name, set, pair_num, orientation, idx, sep="_", remove = FALSE) %>%
  unite(out_name, set, orientation, sep = "_") %>%
  mutate(out_name = paste0(out_name, '_24')) %>%
  select(out_name, Name, `Well Position`, Sequence = primer) 

# foo <- out.24 %>%
#   nest(data = c(-out_name))  %>%
#   mutate(foo = walk2(out_name, data, ~write_csv(.y, path=paste0(.x, '.csv'))))
```

# Checking Purchased Primers

First, let’s triple check the S2 primers we already ordered.

``` r
# load the order
order.path <- './frozen-data/Octant_Order_17-96-well_041920.xlsx'
octant.order <- tibble(sheet = excel_sheets(order.path)) %>%
  mutate(data = map(sheet, ~read_xlsx(order.path, sheet=.x))) %>%
  unnest(cols=data) %>%
  rename(idx = ...4)

s2.order <- octant.order %>%
  filter(str_detect(sheet, 'S2')) %>%
  separate(Name, into=c('set', 'pair_num', 'orientation', 'name_idx')) 
```

## Internal Consistency

Do we have 768 distinct indices? This ensures that no i5/i7 index is
repeated.

``` r
s2.order %>%
  distinct(name_idx) %>%
  nrow()
```

    ## [1] 768

Yes - we have 768 rows. Similarly do we have 384 unique pairs?

``` r
s2.order %>%
  distinct(pair_num) %>%
  nrow()
```

    ## [1] 384

Looks good. Next, does the index in the sheet match the index in the
name?

``` r
s2.order %>%
  filter(idx != name_idx) %>%
  nrow()
```

    ## [1] 0

Yes - there are no deviations. Seems like our order is internally
consistent.

## Generated vs Purchased Agreement

Does it agree with the set of barcodes I produced earlier?

``` r
out.384 %>%
  filter(str_detect(Name, 'S2')) %>%
  select(-`Well Position`, -out_name) %>%
  inner_join(s2.order) %>%
  nrow()
```

    ## Joining, by = "Sequence"

    ## [1] 768

Yes. If there were any disagreements on either the name or the actual
sequence, we would have `<768` rows after the join.

## Sequence Checks

Let’s make sure nothing about the actual primer sequences is amiss. I’m
pulling the relevant oligo sequences from [our primer
sheet](https://docs.google.com/spreadsheets/d/1UZYbk8R9pALNrA7kIOl3AeZpu4fSeAH2T1JNBhKbORU/edit?usp=sharing).

We can test to make sure everything is working by building the primer
sequence from scratch. That is:

    illumina + idx + binding == sequence

``` r
# note how rpp30 flips the illumina sequences!
expected.seqs <- tribble(
  ~set, ~orientation, ~illumina, ~binding,
  'S2',    'f', 'AATGATACGGCGACCACCGAGATCTACAC', 'GCTGGTGCTGCAGCTTATTA',
  'S2',    'r', 'CAAGCAGAAGACGGCATACGAGAT',      'AGGGTCAAGTGCACAGTCTA',
  'RPP30', 'f', 'CAAGCAGAAGACGGCATACGAGAT',      'AGATTTGGACCTGCGAGCG',
  'RPP30', 'r', 'AATGATACGGCGACCACCGAGATCTACAC', 'GAGCGGCTGTCTCCACAAGT'
)

s2.order %>%
  inner_join(expected.seqs) %>%
  mutate(test_seq = str_c(illumina, name_idx, binding)) %>%
  filter(test_seq != Sequence) %>%
  nrow()
```

    ## Joining, by = c("set", "orientation")

    ## [1] 0

Excellent. All generated sequences match the ones we’ve ordered.

# Standardizing on S2

Take the index pair from our S2 set and grab the corresponding Rpp30
primers.

``` r
s2.pairs <- s2.order %>%
  distinct(pair_num) %>%
  mutate(
    pair_num = as.integer(pair_num),
    purchased.order = seq(nrow(.))
  )

# arrange primers in the same order that we purchased them
rpp30.set <- wide.primers %>%
  filter(set == 'RPP30') %>%
  inner_join(s2.pairs) %>%
  arrange(purchased.order)
```

## Checking RPP30

Let’s make sure the RPP30 primers are good as well. First, we’ll make
sure the output primer is valid by building it from scratch again.

``` r
rpp30.tidy <- rpp30.set %>%
  select(-purchased.order) %>%
  pivot_longer(
    cols = c(-set, -pair_num),
    names_to = c('orientation', '.value'),
    names_sep = "_"
  )

rpp30.tidy %>%
  inner_join(expected.seqs) %>%
  mutate(test_seq = str_c(illumina, idx, binding)) %>%
  filter(test_seq != primer) %>%
  nrow()
```

    ## [1] 0

Again, no differences. We can be sure that our index pairs are OK
because we they are the S2 set that we just validated.

## Output

``` r
# rpp30.tidy %>%
#     arrange(orientation) %>%
#     unite(Name, set, pair_num, orientation, idx) %>%
#     write_tsv('./frozen-data/RPP30_new_384.tsv')
```
