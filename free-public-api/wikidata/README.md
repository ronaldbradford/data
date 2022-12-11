# WikiData

### Request

    curl -sL https://www.wikidata.org/wiki/Special:EntityData/Q850.json > Q850.mysql.json

### Response


    {
      "entities": {
        "Q850": {
          "pageid": 1170,
          "ns": 0,
          "title": "Q850",
          "lastrevid": 1787881754,
          "modified": "2022-12-11T08:43:28Z",
          "type": "item",
          "id": "Q850",
          "labels": {
            "en": {
              "language": "en",
              "value": "MySQL"
            },
            "fr": {
              "language": "fr",
              "value": "MySQL"
            },
            ...
            "claims": {
      "P138": [
        {
          "mainsnak": {
            "snaktype": "value",
            "property": "P138",
            "hash": "209c9b8926a49cb121f132a170cf019165d48ecd",
            "datavalue": {
              "value": {
                "entity-type": "item",
                "numeric-id": 18615979,
                "id": "Q18615979"
              },
              "type": "wikibase-entityid"
            },
            "datatype": "wikibase-item"
          },
          "type": "statement",
          "id": "Q850$4193a320-4d83-2c8d-88be-b4ecb61986f7",
          "rank": "normal"
        }
      ],
      "P1401": [
        {
          "mainsnak": {
            "snaktype": "value",
            "property": "P1401",
            "hash": "29a58dac67229081a344b8a07c99ee980c8a26fd",
            "datavalue": {
              "value": "https://bugs.mysql.com/",
              "type": "string"
            },
            "datatype": "url"
          },
          "type": "statement",
          "id": "Q850$3b49d143-47c8-79c0-e738-1f4a40280952",
          "rank": "normal"
        }
      ],
