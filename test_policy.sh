#!/bin/bash

rm -rf policy_log
for ((DAY=301; DAY<600; DAY+=10))
do
  for ((N_COMP=4; N_COMP<=8; N_COMP++))
  do
    for NAME in ERIC-A ERIC-B ELUX-A ELUX-B CAT-B HM-B KLOV-A KLOV-B TEL2-A TEL2-B VOLV-B SAS SEB-A
    do
      echo "testing ${NAME} from day: $DAY"
      python3 ./hmm_policy_data.py ${NAME} $N_COMP $DAY  30 |  tee -a  policy_log
    done
  done
done
#cat tmp_$C | grep finish | awk -F: '{if ($NF!=10000.0) {tot += $NF; i+=1}} END{printf("avg result:%d, stocks:%d\n", tot/i, i)}' 
