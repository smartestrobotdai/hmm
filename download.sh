#!/bin/bash

CSV_DIR="data-files"
TXT_DIR="txt-files"
# check if need to download files

if [ ! -d ${CSV_DIR} ]; then

  while IFS='' read -r line || [[ -n "$line" ]]; do
    #echo "Text read from file: $line"
    NAME=`echo $line | awk -F, '{print($1)}' | awk -f stock_name.awk`

    ISIN=`echo $line | awk -F, '{print($3)}'`
    echo "${NAME}:${ISIN}"

    # now downoad the data file.
    mkdir -p ${CSV_DIR}
    wget "https://www.nordnet.se/mux/laddaner/historikLaddaner.ctl?isin=${ISIN}&country=Sverige&currency=SEK" -O ${CSV_DIR}/${NAME}.csv


  done < stock_list.txt
else
  echo "${CSV_DIR} exists, ignoring downloading..."
fi

if [ ! -d ${TXT_DIR} ]; then
  for CSV in `ls ${CSV_DIR}`
  do
    # we need at least data for 800 days
    LINES=`wc -l ${CSV_DIR}/${CSV} | awk '{print $1}'`
    if [ ${LINES} -lt 800 ]; then
      echo "Data is less than 800 days, ignoring ${CSV}"
      continue
    fi
    FILENAME=`echo ${CSV} | sed 's/.csv//g'`
    echo "formatting ${CSV} to ${TXT_DIR}/${FILENAME}.txt - ${LINES} lines"
    mkdir -p ${TXT_DIR}

    sed  '1,2d;s/\([[:digit:]]\) \([[:digit:]]\)/\1\2/g; s/\([[:digit:]]\),\([[:digit:]]\)/\1\2/g; /^$/d' ${CSV_DIR}/${CSV} > ${TXT_DIR}/${FILENAME}.txt
  done
else
  echo "${TXT_DIR} exists, ignoring formatting..."
fi
