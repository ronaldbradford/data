# Earthquakes

List of earthquakes for a given date. This returns a GeoJSON format, which can be rendered in a Github gist -- https://gist.github.com/ronaldbradford/ecf2951bd34c5bf8e1127ffbb6b99fad

## Request

    curl -sL 'https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime=2022-02-22&endtime=2022-02-23'

## Response

    {
      "type": "FeatureCollection",
      "metadata": {
        "generated": 1669950845000,
        "url": "https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime=2022-02-22&endtime=2022-02-23",
        "title": "USGS Earthquakes",
        "status": 200,
        "api": "1.13.6",
        "count": 407
      },
      "features": [
        {
          "type": "Feature",
          "properties": {
            "mag": 0.68,
            "place": "2km W of San Juan Bautista, CA",
            "time": 1645573579610,
            "updated": 1645654454766,
            "tz": null,
            "url": "https://earthquake.usgs.gov/earthquakes/eventpage/nc73696541",
            "detail": "https://earthquake.usgs.gov/fdsnws/event/1/query?eventid=nc73696541&format=geojson",
            "felt": null,
            "cdi": null,
            "mmi": null,
            "alert": null,
            "status": "reviewed",
            "tsunami": 0,
            "sig": 7,
            "net": "nc",
            "code": "73696541",
            "ids": ",nc73696541,",
            "sources": ",nc,",
            "types": ",nearby-cities,origin,phase-data,scitech-link,",
            "nst": 11,
            "dmin": 0.02862,
            "rms": 0.08,
            "gap": 93,
            "magType": "md",
            "type": "earthquake",
            "title": "M 0.7 - 2km W of San Juan Bautista, CA"
          },
          "geometry": {
            "type": "Point",
            "coordinates": [
              -121.5595,
              36.846,
              9.25
            ]
          },
          "id": "nc73696541"
        },
        ...
