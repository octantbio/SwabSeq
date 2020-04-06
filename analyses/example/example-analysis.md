Example Analysis
================
Nate
04/03/2020

  - [Setup](#setup)
      - [Getting Oriented](#getting-oriented)
      - [Explicit Zeros](#explicit-zeros)
  - [QC](#qc)
      - [Spike-in Cross-over](#spike-in-cross-over)
  - [Expression Relative to
    Spike-in’s](#expression-relative-to-spike-ins)
      - [Tidying](#tidying)
      - [Detection Plots](#detection-plots)

# Setup

Import and load everything

``` r
# plotting
library(ggbeeswarm) # <- geom_quasirandom

# tidyverse
library(furrr) # <- parallel map (future_map, plan) (devtools for walk)
library(readxl) # <- read_xlsx
library(magrittr)
library(tidyverse)

# ------------------------------------------------------------------------------------
# style plots

theme_pub <- function(base_size = 11, base_family = "") {
  # based on https://github.com/noamross/noamtools/blob/master/R/theme_nr.R
  # start with theme_bw and modify from there!
  theme_bw(base_size = base_size, base_family = base_family) +# %+replace%
    theme(
      # grid lines
      panel.grid.major.x = element_line(colour="#ECECEC", size=0.5, linetype=1),
      panel.grid.minor.x = element_blank(),
      panel.grid.minor.y = element_blank(),
      panel.grid.major.y = element_line(colour="#ECECEC", size=0.5, linetype=1),
      panel.background   = element_blank(),
      
      # axis options
      axis.ticks.y   = element_blank(),
      axis.title.x   = element_text(size=rel(2), vjust=0.25),
      axis.title.y   = element_text(size=rel(2), vjust=0.35),
      axis.text      = element_text(color="black", size=rel(1)),
      
      # legend options
      legend.title    = element_text(size=rel(1.5)),
      legend.key      = element_rect(fill="white"),
      legend.key.size = unit(1, "cm"),
      legend.text     = element_text(size=rel(1.5)),
      
      # facet options
      strip.text = element_text(size=rel(2)),
      strip.background = element_blank(),
      
      # title options
      plot.title = element_text(size=rel(2.25), vjust=0.25, hjust=0.5)
    )
}
theme_set(theme_pub(base_size=8))

# ------------------------------------------------------------------------------------

# workaround to enable multicore with new rstudio versions
options(future.fork.enable = TRUE)
plan(multicore)
set.seed(42)

# ------------------------------------------------------------------------------------
# load data

guess_max <- 100000
run_id = '200402_NB552046_0038_AHLHM2BGXF'

# barcode counts
counts <- read_csv(paste0('../../pipeline/', run_id, '/starcode.csv'))
well.total <- counts %>%
  filter(Sample_ID != 'Undetermined') %>%
  distinct(Sample_ID, Centroid, Count)  %>%
  count(Sample_ID, wt=Count, name = 'Well_Total') 


# drop some dummy variables that aren't needed
cond <- read_csv(paste0('../../pipeline/', run_id, '/conditions.csv'), guess_max=guess_max) %>% 
  select(-cell_library, -bc_promoter, -chem_ID, -molarity)



##### NOTE
### THIS HARD-CODED TRIMMING WILL HAVE TO BE FIXED!!!
bc.map <- read_xlsx(paste0('../../pipeline/', run_id, '/bc-map.xlsx'), sheet='assay_seqs', guess_max=guess_max) %>%
  mutate(sequence=substr(toupper(sequence), 1, 15))
```

## Getting Oriented

Let’s make sense of the relevant parameters here. In each well, we are
trying to quantify the counts of 5 different barcodes:

``` r
bc.map %>%
  distinct(sequence, target, amplicon) %>%
  arrange(target)
```

    ## # A tibble: 5 x 3
    ##   sequence        target     amplicon
    ##   <chr>           <chr>      <chr>   
    ## 1 CGCAGAGCCTTCAGG RPP30      RPP30   
    ## 2 TATCTTCAACCTAGG SARS-CoV-2 S2      
    ## 3 ACCAAACGTAATGCG SARS-CoV-2 N1      
    ## 4 ATAGAACAACCTAGG spike      S2_spike
    ## 5 TGGTTTCGTAATGCG spike      N1_spike

one representing the housekeeping gene RPP30, two representing different
amplicons from the COVID-19, and two different spike in controls (one
for each amplicon).

In reality, we measure more than the 5 barcodes barcodes in each well.
Let’s print the top 10 most common barcodes (denoted here as centroid as
we collapse barcodes at a Levenshtein distance of 2) and their counts in
an example well

``` r
counts %>%
  filter(Sample_ID == 'o129-A01') %>%
  distinct(Sample_ID, Centroid, Count) %>%
  left_join(bc.map %>% filter(assay == 'N1_RPP30') %>% rename(Centroid = sequence)) %>%
  head(n=10)
```

    ## Joining, by = "Centroid"

    ## # A tibble: 10 x 6
    ##    Sample_ID Centroid        Count target     amplicon assay   
    ##    <chr>     <chr>           <dbl> <chr>      <chr>    <chr>   
    ##  1 o129-A01  TGGTTTCGTAATGCG 12290 spike      N1_spike N1_RPP30
    ##  2 o129-A01  ACCAAACGTAATGCG   734 SARS-CoV-2 N1       N1_RPP30
    ##  3 o129-A01  TTGGTTTCGTGATGC    67 <NA>       <NA>     <NA>    
    ##  4 o129-A01  TGGCTTCGTTAATGC    62 <NA>       <NA>     <NA>    
    ##  5 o129-A01  GGTTCGTAATGCGGG    33 <NA>       <NA>     <NA>    
    ##  6 o129-A01  CGCAGAGCCTTCAGG    15 RPP30      RPP30    N1_RPP30
    ##  7 o129-A01  AGCATACCAAAAACG    12 <NA>       <NA>     <NA>    
    ##  8 o129-A01  ATTCATCTAGCTGTG     8 <NA>       <NA>     <NA>    
    ##  9 o129-A01  AGGATACGTAATGCG     3 <NA>       <NA>     <NA>    
    ## 10 o129-A01  TGGCTTGTAATGCGG     3 <NA>       <NA>     <NA>

We can see that fortunately majority of reads in any well will
correspond to sequences associated with our barcodes. Other sequences
are likely PCR errors or contaminants.

### Reads per Well

Let’s get a sense for how even our sampling per well is. To do this,
we’ll simply add up all of the counts for all of the barcodes in each
well.

``` r
# recall this is equivalent to well.total above
counts %>%
  filter(Sample_ID != 'Undetermined') %>%
  distinct(Sample_ID, Centroid, Count)  %>%
  count(Sample_ID, wt=Count, name = 'Well_Total') %>%
  separate(Sample_ID, into = c('Sample_Plate', 'Well'), sep = '-', remove=F) %>%
  mutate(
    Row = factor(str_sub(Well, 1, 1), levels = rev(LETTERS[1:16])),
    Col = str_sub(Well, 2)
  ) %>%
  ggplot(aes(x=Col, y=Row, fill=log10(Well_Total))) +
  geom_raster() +
  coord_equal() +
  facet_wrap(~Sample_Plate) +
  scale_fill_viridis_c(option = 'plasma')
```

![](figs/unnamed-chunk-3-1.png)<!-- -->

We can see a bifurcation in total reads between the top and bottom halfs
of the plate. If we go back to our `cond` dataframe (which recall has
all of the relevant metadata for each well)

``` r
well.total %>%
  separate(Sample_ID, into = c('Sample_Plate', 'Well'), sep = '-', remove=F) %>%
  mutate(
    Row = factor(str_sub(Well, 1, 1), levels = rev(LETTERS[1:16])),
    Col = str_sub(Well, 2)
  ) %>%
  inner_join(cond) %>%
  ggplot(aes(x=Col, y=Row, fill=lysate)) +
  geom_raster() +
  coord_equal() +
  facet_wrap(~Sample_Plate)
```

![](figs/unnamed-chunk-4-1.png)<!-- -->

we can see that the difference in reads comes from the sample prep -
lysate from either nasopharyngeal (NP) swabs or HEK293 (NA are no HEK293
lysate controls).

## Explicit Zeros

Since we know what barcodes to expect in each well, we can add explicit
zeros to barcodes that drop out.

``` r
explicit.zeros <- function(df, bc.map) {
  # take only assays and targets from the current run
  # assumes df has been joined with condition sheet
  bc.map %>%
    filter(
      assay %in% unique(df$assay),
    ) %>%
    left_join(df, by = c('sequence', 'assay')) %>%
    replace_na(list(Count = 0))
}

# select the variables in the barcode map that vary
# (and any additional info you want to include)
bc.map.var <- bc.map %>%
  select('sequence', 'target', 'amplicon', 'assay')

# drop the centroid column as it's not needed
# coerce Count to integer to avoid weird scientic notation behavior in format_csv
df <- counts %>%
  select(-Centroid) %>%
  rename(sequence=barcode) %>% 
  inner_join(select(cond, Sample_ID, assay), by = 'Sample_ID') %>% 
  group_by(Sample_ID) %>%
  group_nest() %>%
  mutate(foo = future_map(data, ~explicit.zeros(.x, bc.map.var))) %>%
  select(-data) %>%
  unnest(foo) %>%
  inner_join(cond) %>%
  mutate(
    Row = factor(str_sub(Sample_Well, 1, 1), levels = rev(LETTERS)),
    Col = str_sub(Sample_Well, 2)
  ) %>%
  select(Sample_ID, Sample_Plate, Row, Col, amplicon, assay, Count, Twist_RNA_copies:lysate)
```

We’ll also join on the relevant experimental metadata.

# QC

## Spike-in Cross-over

In this particular experiment, we separated our two different spike-in
across the two different plates. Let’s see how much cross-over we had

``` r
df %>%
  filter(str_detect(amplicon, "spike")) %>%
  mutate(assay = if_else(str_detect(assay, "N1"), "N1 Expected", "S2 Expected")) %>%
  ggplot(aes(x=Col, y=Row, fill=log10(Count+1))) +
  geom_raster() +
  coord_equal() +
  facet_grid(assay ~ amplicon) +
  scale_fill_viridis_c(option = 'plasma')
```

![](figs/unnamed-chunk-6-1.png)<!-- -->

We can see that although there is some cross-over present, it is to a
very limited extent\!

# Expression Relative to Spike-in’s

## Tidying

In addition to different sample preps, we used three different sources
of COVID-19 RNA - heat inactivated virus from ATCC, COVID-19 RNA from
ATCC, and COVID-19 RNA from Twist. We spiked these samples over a large
concentration range to test the sensitivity of our method.

``` r
df %>%
  select(assay, Row, Col, Twist_RNA_copies:ATCC_virus_copies)  %>%
  distinct() %>%
  gather(metric, value, Twist_RNA_copies:ATCC_virus_copies) %>%
  ggplot(aes(x=Col, y=Row, fill=log10(value+0.1))) +
  geom_raster() +
  coord_equal() +
  facet_wrap(~metric, ncol=2) +
  scale_fill_viridis_c()
```

![](figs/unnamed-chunk-7-1.png)<!-- -->

From this we can make a key. We’ll also make a normalization data frame
so we can normalize relative to the proper control

``` r
expr <- list(
  ATCC_Virus= LETTERS[1:4], 
  ATCC_RNA = LETTERS[5:12], 
  NP_Control = LETTERS[13:14], 
  Twist_RNA = LETTERS[15:16]
) %>%
  enframe(name = 'Expr', value = 'Row') %>%
  unnest(cols = 'Row') %>%
  # mutate(Col = rep(list(c(paste0('0', 1:9), 10:24)), 16)) %>%
  # unnest(cols='Col') %>%
  mutate(Row = factor(Row, levels = rev(LETTERS)))

tmp <- df %>%
  # filter out the expected spike for a given assay
  filter(
    str_detect(amplicon, "spike"),
    str_sub(amplicon, end=2) == str_sub(assay, end=2)
  ) %>%
  select(Sample_ID,  Spike_Count = Count) %>%
  inner_join(df) %>%
  # filter out amplicons from the wrong experiment
  filter(
    str_detect(amplicon, "spike", negate=T),
    str_detect(assay, amplicon)
  ) %>%
  # recast amplicon as RNA in general so everything will work
  mutate(amplicon = if_else(amplicon == 'RPP30', 'RPP30', 'RNA')) %>%
  spread(amplicon, Count)


no.rna.control <- expr %>%
  filter(Expr == 'NP_Control') %>%
  inner_join(tmp) %>%
  select(-contains("ATCC"), -contains("Twist")) %>%
  mutate(
    Expr = 'NP_Control',
    copies = 0
  )

df.tidy <- tmp %>%
  rename(ATCC_Virus = ATCC_virus_copies) %>%
  gather(Expr, copies, Twist_RNA_copies:ATCC_Virus) %>%
  mutate(Expr = str_remove(Expr, '_copies')) %>%
  inner_join(expr)  %>%
  bind_rows(no.rna.control)
```

Let’s plot the new dataframe to make sure everything is tidied properly

``` r
df.tidy %>%
  ggplot(aes(x=Col, y=Row, fill=log10(copies+0.1))) +
  geom_raster() +
  coord_equal() +
  facet_wrap(~Sample_Plate) +
  scale_fill_viridis_c()
```

![](figs/unnamed-chunk-9-1.png)<!-- -->

## Detection Plots

Let’s norm COVID to spike and plot it out across the range of RNA copies
we added in:

``` r
df.tidy %>%
  filter(Expr != 'NP_Control', !is.na(lysate)) %>%
  ggplot(aes(x=copies+0.1, y=(RNA+1)/(Spike_Count+1), group=copies)) +
  geom_boxplot() +
  scale_x_log10() +
  scale_y_log10() +
  facet_wrap(~paste(lysate, Expr, assay, sep='\n'))
```

![](figs/unnamed-chunk-10-1.png)<!-- -->

We can see that indeed, we are getting detection from the various RNA
samples in HEK293 lysate. NP samples are much harder to detect, although
we can detect heat inactivated virus.

### HEK293 LYSATE + ATCC RNA

This seems to be one of our best assays. Let’s zoom in.

``` r
df.tidy %>%
  filter(
    lysate == 'HEK293',
    Expr == 'ATCC_RNA'
  ) %>%
  mutate(copies = if_else(copies == 0, 0.1, copies)) %>%
  ggplot(aes(x=copies, y=(RNA+1)/(Spike_Count+1), group=copies)) +
  geom_boxplot(outlier.shape = NA) +
  geom_quasirandom(alpha=0.4) +
  scale_x_log10(breaks = c(10^(-1:4)), labels = c(0,10^(0:4))) +
  scale_y_log10() +
  annotation_logticks() +
  facet_wrap(~assay)
```

![](figs/unnamed-chunk-11-1.png)<!-- -->