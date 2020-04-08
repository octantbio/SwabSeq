SARS-CoV-2 platform run 4 analysis
================
Aaron
04/03/2020

  - [TLDR](#tldr)

# TLDR

Here, we assayed inactivated viral lysate (ATCC), purified CoV genomic
RNA (ATCC), and synthetic Twist CoV RNA in the background of human cell
line lysate and human NP swab lysate with the N1 and S2 primers. We
included the RPP3 primers at 100 nM naked primer and 50 nM primer with
adaptor. We also included a synthetic RNA spike-in with CoV priming
sites to normalize to. This analysis file is incomplete (and wrong in
some sections). For a detailed analysis of this run in the human cell
line lysate please look at the example file. The synthetic spike-in
cleaned up the data a lot. The NP swab lysate failed for some reason, we
suspect the lysate was inactivated incorrectly as NP swab lysate has
worked for RT-QPCR in our hands reliabely.

Let’s first just look at reads per well across our plates:

![](Figs/unnamed-chunk-4-1.png)<!-- -->

N1 has more even coverage this time. Pretty, pretty, pretty even. S2
looks more variable, but about the same as run3. No row I dropouts this
time\! What the hell happened in run01?

Let’s look at distribution of well totals to possibly set a cutoff:

![](Figs/unnamed-chunk-5-1.png)<!-- -->

If we had to do a cutoff, 1e4 might be slightly better than a shot in
the dark.

Regarding the N1 to S2 difference in depth, let’s sum across the plates:

![](Figs/unnamed-chunk-6-1.png)<!-- -->

We are close to 1:1 this time, unlike run01.

Let’s look at RPP30 reads between the plates/wells:

![](Figs/unnamed-chunk-7-1.png)<!-- -->

Very low coverage on RPP30 in this run for some reason.

Let’s move on to look at spike reads now that we have spikes for both
samples:

![](Figs/unnamed-chunk-8-1.png)<!-- -->

![](Figs/unnamed-chunk-9-1.png)<!-- -->

There is some amount of assay crossover, which can only be due to index
switching on the sequencer. Master mixes for these two plates were
prepped separately, and spike was only put into the matched plate
(i.e. N1 spike on N1 plate, S2 on S2 plate). Libraries were pooled per
plate, purified, and only then mixed. Could be something during bridge
amplification or something optical.

Let’s norm COVID to spike and plot it out across the range of RNA copies
we added in:

![](Figs/unnamed-chunk-10-1.png)<!-- -->

Looks cool\! Let’s plot this across the nCoV range.

![](Figs/unnamed-chunk-11-1.png)<!-- -->

Looks promising, but not in NP?

![](Figs/unnamed-chunk-12-1.png)<!-- -->
