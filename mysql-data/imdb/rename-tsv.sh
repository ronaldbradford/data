#!/usr/bin/env bash

for FILE in $(ls *.tsv.all); do
  echo ${FILE}
  mv ${FILE} $(echo ${FILE} | sed -e "s/.all//")
done
