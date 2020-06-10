## Checking for Cross-reactivity

According to the most recent [FDA guidance](https://www.fda.gov/medical-devices/emergency-situations-medical-devices/emergency-use-authorizations#covid19ivdTemplates) (as of May 13 2020 - [here](https://www.fda.gov/media/135658/download)) all primers must be assessed for any potential cross reactivity to the following organisms:

```
TAXID    NAME
11137    Human coronavirus 229E
31631    Human coronavirus OC43
290028   Human coronavirus HKU1
277944   Human coronavirus NL63
694009   Severe acute respiratory syndrome-related coronavirus
1335626  Middle East respiratory syndrome-related coronavirus
1643649  Human adenovirus 71
162145   Human metapneumovirus
188538   Human parainfluenza virus 1 strain Washington/1964
11217    Human parainfluenza 3 virus (strain NIH 47885)
11214    Human parainfluenza virus 2 (strain Toshiba)
11224    Human parainfluenza virus 4a
11226    Human parainfluenza virus 4b
11320    Influenza A virus
11520    Influenza B virus
42789    Enterovirus D68
12814    Respiratory syncytial virus
12059    Enterovirus
83558    Chlamydia pneumoniae
727      Haemophilus influenzae
446      Legionella pneumophila
1773     Mycobacterium tuberculosis
1313     Streptococcus pneumoniae
1314     Streptococcus pyogenes
520      Bordetella pertussis
2104     Mycoplasma pneumoniae
42068    Pneumocystis jirovecii
5476     Candida albicans
287      Pseudomonas aeruginosa
1282     Staphylococcus epidermidis
1304     Streptococcus salivarius
```

Any primer with >80% sequence identity must be flagged.

## BLAST Set up

Getting BLAST set up is a breeze thanks to the NCBI's [docker image](https://hub.docker.com/r/ncbi/blast) and their [documentation](https://github.com/ncbi/blast_plus_docs). Below is an abbreviated guide to getting everything running.

First pull the docker image

```
docker pull ncbi/blast
```

Next make a `blast` directory and pull the NCBI nucleotide database. (Much of this is cribbed directly from [](https://github.com/ncbi/blast_plus_docs#commands-to-run))

```
cd ~
mkdir -p mkdir -p blastdb queries fasta results blastdb_custom

# download the nucleotide database (~70 Gb) from google cloud
# this will take a while (~30 mins) depending on how fast your internet is
docker run --rm \
  -v ~/blast/blastdb:/blast/blastdb:rw \
  -w /blast/blastdb \
  ncbi/blast \
  update_blastdb.pl --source gcp nt
```

After this completes, set up your query by cat'ing all the primers together. NOTE THIS ASSUMES YOU ARE IN THE SWAB-SEQ DIRECTORY!

```
# GET TO THE SWABSEQ DIRECTORY FIRST!
cd analyses/primer-design-3
cat rpp30*.tsv s2*.tsv \
  | awk '{print ">"$1 ORS $2}' \
  > ~/blast/queries/swab-seq_primers.fa
```

Now we can BLAST our primers against the taxa of interest

```
docker run --rm \
  -v ~/blast/blastdb:/blast/blastdb:ro \
  -v ~/blast/blastdb_custom:/blast/blastdb_custom:ro \
  -v ~/blast/queries:/blast/queries:ro \
  -v ~/blast/results:/blast/results:rw \
  ncbi/blast \
  blastn -query /blast/queries/swab-seq_primers.fa \
  -db nt \
  -num_threads 60 \
  -outfmt 7 \
  -taxids 11137,31631,290028,277944,694009,1335626,1643649,162145,188538,11217,11214,11224,11226,11320,11520,42789,12814,12059,83558,727,446,1773,1313,1314,520,2104,42068,5476,287,1282,1304 \
  -out /blast/results/swab-seq_primers.out
```

There should be no significant hits!
