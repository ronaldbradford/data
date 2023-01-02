#!/usr/bin/env bash


echo ""
echo "MySQL Curated Datasets from Ronald Bradford - https://github.com/ronaldbradford/data"
echo " * Locations"
echo "   OpenStreetMap® is open data, licensed under the pen Data Commons Open Database License. See https://www.openstreetmap.org/copyright"
echo ""
echo ""

echo "This data is included in this repository as it is specifically generated."
echo ""
echo 'NOTE: While jq handles \", this is invalid with loading data into MySQL, it has to be \\\\". e.g.'
echo ""
grep 51639047 location.json

# sed -e 's/\\/\\\\\\/g' location.json.all > location.json
