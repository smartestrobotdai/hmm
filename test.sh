#!/bin/bash

for NAME in ERIC-A ERIC-B ELUX-A ELUX-B CAT-B HM-B KLOV-A KLOV-B TEL2-A TEL2-B VOLV-B SAS SEB-A
do
  python3 ./hmm_stock.py ${NAME} | grep finish
done

