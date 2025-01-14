#!/bin/bash

zcat ../../_m/*.expression.bed.gz | cut -f 1-4 | egrep -v '^#' | \
    perl -ne 'chomp; @a=split /\t/; print(join("\t", $a[0],".","gene",$a[1],$a[2],".",".",".","gene_id \"$a[3]\"; gene_name \"$a[3]\";"),"\n")' > feature.gtf
