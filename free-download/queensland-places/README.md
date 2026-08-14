# Queensland List of Places

URL: https://www.data.qld.gov.au/dataset/place-names-gazetteer-queensland-txt-file

## Get Source Data

```
wget https://www.data.qld.gov.au/dataset/bd13d3a3-5470-437b-8d43-54d166907296/resource/7fd4a6dc-80d3-4d7d-aad0-60e7721f35da/download/placenames_gazeteer_data-dictionary.txt
wget https://www.data.qld.gov.au/dataset/bd13d3a3-5470-437b-8d43-54d166907296/resource/414391b9-7943-4fc3-a237-a1ac57b75aab/download/queensland_place_names_gazetteer.csv
```

## Cleanup Data for easier use

Produce easier to use headings
```
awk 'NR==1{gsub(/ /,"_"); print tolower($0); next} 1' queensland_place_names_gazetteer.csv > queensland.csv
```

## Generate Randomized Routes

Extract a number of locations, and create a GEOJSON file of routes, simulating a very poor example of a package delivery system.

```
for i in $(seq -w 1 100); do echo $i; python3 extract_locb_route.py --iterations 5 --seed $i --output geojson/routes.$i.geojson; done
```

