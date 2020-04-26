SHELL := /bin/bash
.DELETE_ON_ERROR:

#===============================================================================
# VARIABLES

# sequencing run ids
RUNS := $(shell find data/seq-runs -maxdepth 1 -mindepth 1 -type d -exec basename {} \;)

#===============================================================================
# RECIPIES

all: starcode kb
starcode: $(addprefix pipeline/, $(addsuffix /starcode.csv, $(RUNS)))
kb: $(addprefix pipeline/, $(addsuffix /kb.tsv, $(RUNS)))

# cleanup
clean:
	rm -rf pipeline/*

.PRECIOUS: $(addprefix pipeline/, %/conditions.csv %/starcode.csv %/output.bus %/kb.tsv)
.SECONDARY:

#===============================================================================
# STARCODE PIPELINE
# 1) demultiplex all i5/i7 pairs
# 2) run starcode on all resulting fastq's to collapse sequences lev=2 apart

# 0) Directory Prep:
# ------------------
# copy barcode map from data/ folder.
pipeline/%/bc-map.csv:
	@echo "Grabbing $@"
	@mkdir -p $(dir $@)
	@cp data/barcode-map.csv $@

# grab relevant section of samplesheet (make sure to catch windows return)
pipeline/%/conditions.csv: data/plate-maps/%/SampleSheet.csv pipeline/%/bc-map.csv
	@echo "Parsing $<"
	@python src/strip-windows.py $< \
		| awk '/Sample_ID/{seen=1} seen{print}' \
		| Rscript src/bc-lengths.R $(word 2, $^) $@ \
		2> $(@:.csv=.err)

# 1) Demultiplexing:
# ------------------
# starcode compatible demux
pipeline/%/demux-starcode/demux: data/seq-runs/% data/plate-maps/%/SampleSheet.csv
	@echo "Demultiplexing all i5/i7 combos in: $<"
	@mkdir -p $(@D)
	@bcl2fastq \
	    --runfolder-dir $< \
	    --output-dir $(@D) \
	    --sample-sheet $(lastword $^) \
	    --processing-threads 8 \
	    --no-lane-splitting \
	    2> $(@D)/bcl2fastq.out \
	    && touch $@

# 2) Starcode:
# ------------
# Run starcode on each fastq, using gnu parallel to parse the conditions for barcode length
pipeline/%/starcode.csv: pipeline/%/demux-starcode/demux pipeline/%/conditions.csv
	@echo "Counting BCs for all fastq's in $(<D)"
	@parallel --header : --colsep "," \
		zcat $(<D)/"{Sample_ID}"_S*_R1_001.fastq.gz \
		\| awk -v bc_len="{bc_len}" -f src/count-bcs.awk \
		\| starcode -d2 -t1 --sphere --print-clusters 2> /dev/null \
		\| python src/tidy-star.py \
		\| awk -v name="{Sample_ID}" \''{print name, $$1, $$2, $$3}'\' OFS="," \
	:::: $(word 2, $^) 2> $(@:.csv=.err) > $(@:.csv=.tmp) \
	&& echo "Sample_ID,Centroid,Count,barcode" \
	| cat - $(@:.csv=.tmp) > $@ \
	&& rm $(@:.csv=.tmp)

# a dummy recipe so we dont have to store the example fastqs
pipeline/example/starcode.csv: data/seq-runs/example/example-starcode.csv.gz pipeline/example/conditions.csv
	zcat $< > $@

#===============================================================================
# KALLISTO PIPELINE
# 1) Build Kallisto Index
# 2) Have bcl2fastq pool everything into a single fastq
# 3) Pseudo-align sequences to index
# 4) Demultiplex based in i5/i7 and count

# 1) Index:
# ---------
data/expected-amplicons.idx: data/expected-amplicons.fa
	@echo "Building kallisto index on - $<"
	@kallisto index --kmer-size 11 --index $@ $< 2> $(@:.idx=.err)

# 2) Pool into fastqs:
# --------------------
pipeline/%/demux-kallisto/demux: data/seq-runs/%
	@echo "Demultiplexing $< for kallisto"
	@mkdir -p $(@D)
	@python src/run-bcl2fastq.py --threads 8 $< $(@D) 2> $(@D)/bcl2fastq.out \
	    && touch $@

# 3) Pseudo-align:
# ----------------
# run-kallisto.py takes: kallisto index, out_dir
pipeline/%/output.bus: pipeline/%/demux-kallisto/demux data/expected-amplicons.idx
	@echo "Pseudo-aligning reads with kallisto in $(<D)"
	@mkdir -p $(@D)
	@python src/run-kallisto.py \
	    --index $(lastword $^) \
	    --out-dir $(@D) \
	    --threads 8 \
	    $(<D)/*.fastq.gz \
	    2> $(@D)/kallisto.err

# 4) Demux and count:
# -------------------
# bustools needs a whitelist of all barcodes
# we make them by cat'ing our indicies together
pipeline/%/whitelist.txt: pipeline/%/conditions.csv
	@echo "Building bustools whitelist from $<"
	@mlr --headerless-csv-output --csv \
	    put -e '$$barcode = $$index . $$index2' \
	    then cut -f barcode \
	    $< \
	    > $@

# bustools pipeline to demux and count
pipeline/%/kb.tsv: pipeline/%/output.bus pipeline/%/whitelist.txt
	@echo "Using bustools to demultiplex and count $<"
	@bustools sort --threads 2 --pipe --temp $(@D)/tmp $< \
	    | bustools correct --pipe --whitelist $(lastword $^) - \
	    | bustools sort --threads 2 --pipe --temp $(@D)/tmp2 - \
	    | bustools text --pipe - \
	    > $@

# dummy for example
pipeline/example/kb.tsv: data/seq-runs/example/example-kb.tsv pipeline/example/conditions.csv
	@cp $< $@
