SHELL := /bin/bash
.DELETE_ON_ERROR:

#===============================================================================
# VARIABLES

# sequencing run ids
RUNS := $(shell find data -maxdepth 1 -mindepth 1 -type d -exec basename {} \;)

#===============================================================================
# RECIPIES

all: conds star
conds: $(addprefix pipeline/, $(addsuffix /conditions.csv, $(RUNS)))
star: $(addprefix pipeline/, $(addsuffix /starcode.csv, $(RUNS)))
signif: $(addprefix results/, $(addsuffix /signif.tsv.gz, $(RUNS)))

# cleanup
clean:
	rm -f pipeline/*
deep_clean:
	rm -f pipeline/* results/*
.PRECIOUS: $(addprefix pipeline/, %/conditions.csv %/bc-counts.csv %/starcode.csv)
.SECONDARY:

#===============================================================================

# gnu parallel requires some extra escaping for ' and |
# recall parallel will sub in the full path at {} and basename at {/}
# {/} yields - SampleID_Sample_Lane_Read_001.fastq.gz
# bcl2fastq on the MiSeq appears to translate any "_" in SampleID to "-"
pipeline/%/starcode.csv: data/%
	@echo "Counting BCs for all fastq's in $<"
	@parallel \
	    zcat {} \
	    \| awk \''NR % 4 == 2{a[substr($$1, 1, 15)]++} END {for(bc in a) print bc, a[bc]}'\' \
	    \| starcode -d2 -t1 --sphere --print-clusters 2> /dev/null \
	    \| python src/tidy-star.py \
	    \| awk -v name="{/}" \''{split(name, a, "_"); print a[1], $$1, $$2, $$3}'\' OFS="," \
	::: $</*.fastq.gz > $(@:.csv=.tmp) \
	&& echo "Sample_ID,Centroid,Count,barcode" \
	| cat - $(@:.csv=.tmp) > $@ \
	&& rm $(@:.csv=.tmp)

# pipeline/%/starcode.csv: data/% pipeline/%/conditions.csv
# 	@echo "Counting BCs for all fastq's in $<"
# 	@parallel --header : --colsep "," \
# 	    zcat $</"{Sample_ID}"_S*_R1_001.fastq.gz \
# 	    \| awk -v bc_len="{bc_len}" -f src/count-bcs.awk \
# 	    \| starcode -d2 -t1 --sphere --print-clusters 2> /dev/null \
# 	    \| python src/tidy-star.py \
# 	    \| awk -v name="{Sample_ID}" \''{print name, $$1, $$2, $$3}'\' OFS="," \
# 	:::: $(word 2, $^) 2> $(@:.csv=.err) > $(@:.csv=.tmp) \
# 	&& echo "Sample_ID,Centroid,Count,barcode" \
# 	| cat - $(@:.csv=.tmp) > $@ \
# 	&& rm $(@:.csv=.tmp)
	

# grab relevant section of samplesheet (make sure to catch windows return)
pipeline/%/conditions.csv: data/%/SampleSheet.csv pipeline/%/bc-map.xlsx
	@echo "Parsing $<"
	@python src/strip-windows.py $< \
	    | awk '/Sample_ID/{seen=1} seen{print}' \
	    | Rscript src/bc-lengths.R $(word 2, $^) $@ \
	    2> $(@:.csv=.err)

#===============================================================================
# pull relevant db's from gdrive

pipeline/%/bc-map.xlsx:
	@echo "Grabbing $@"
	@mkdir -p $(dir $@)
	@rclone \
	    cat \
	    --config src/rclone.conf \
	    --drive-shared-with-me \
	    octant-gdrive:"SARS-CoV-2_assay_barcode_map.xlsx" \
	    > $@

