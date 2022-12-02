# OpenStreetMap

## search

Search for a place by a city/state/country

### Request

    curl 'https://nominatim.openstreetmap.org/search?city=Trumbull&state=CT&country=USA&format=geojson'
### Response

    {
      "type": "FeatureCollection",
      "licence": "Data © OpenStreetMap contributors, ODbL 1.0. https://osm.org/copyright",
      "features": [
        {
          "type": "Feature",
          "properties": {
            "place_id": 299481643,
            "osm_type": "relation",
            "osm_id": 11049560,
            "display_name": "Trumbull, Fairfield County, Connecticut, 06611, United States",
            "place_rank": 16,
            "category": "boundary",
            "type": "administrative",
            "importance": 0.634622043029699,
            "icon": "https://nominatim.openstreetmap.org/ui/mapicons/poi_boundary_administrative.p.20.png"
          },
          "bbox": [
            -73.275248,
            41.2205313,
            -73.140531,
            41.2991435
          ],
          "geometry": {
            "type": "Point",
            "coordinates": [
              -73.2006687,
              41.2428742
            ]
          }
        }
      ]
    }

## Get the coordinates of a place

Get the polygon map for a given OpenStreetMap id location. This is Geo JSON format using `.geojson` extension.

Bonus, github gists will render this GeoJSON as a map. For example:  https://gist.github.com/ronaldbradford/6dc146f85750f6dfd19ffc271d4a4cef

### Request

    curl -sl 'http://polygons.openstreetmap.fr/get_geojson.py?id=11049560&params=0'

### Response

    {
      "type": "GeometryCollection",
      "geometries": [
        {
          "type": "MultiPolygon",
          "coordinates": [
            [
              [
                [
                  -73.2743721,
                  41.2938144
                ],
                [
                  -73.27397,
                  41.293863
                ],
                [
                  -73.272834,
                  41.294028
                ],
                ...
