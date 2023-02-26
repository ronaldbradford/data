#!/usr/bin/env bash

echo ""
echo "MySQL Curated Datasets from Ronald Bradford - https://github.com/ronaldbradford/data"
echo " * Employees - Source data from https://github.com/datacharmer/test_db. Distributed under the Attribution-ShareAlike 3.0 Unported (CC BY-SA 3.0) license"
echo ""
echo ""

SOURCE="test_db"
if [[ ! -d "${SOURCE}" ]]; then
  echo "Source '${SOURCE}' not found, downloading..."
  git clone https://github.com/datacharmer/${SOURCE}.git
else
  echo "Skipping download of '${SOURCE}' as it exists, remove to update"
fi

echo "Details of '${SOURCE}'"
du -sh ${SOURCE}

