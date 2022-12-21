# Amadeus Airline Data


Register for a free Account https://developers.amadeus.com/

## Get an API Key

    API_KEY=********
    API_SECRET=*******

## Get an Authorization Token

    curl "https://test.api.amadeus.com/v1/security/oauth2/token" \
         -H "Content-Type: application/x-www-form-urlencoded" \
         -d "grant_type=client_credentials&client_id=${API_KEY}&client_secret=${API_SECRET}" > token.json

    BEARER_TOKEN=$(jq -r .access_token token.json)



## Airport destinations

### Request

    curl -X GET -H "Authorization: Bearer ${BEARER_TOKEN}" "https://test.api.amadeus.com/v1/airport/direct-destinations?departureAirportCode=BNE" > amadeus.bne.json

### Response
    {
     "meta": {
       "count": 74,
       "links": {
         "self": "https://test.api.amadeus.com/v1/airport/direct-destinations?departureAirportCode=BNE"
       }
     },
     "data": [
       {
         "type": "location",
         "subtype": "city",
         "name": "ALBURY",
         "iataCode": "ABX"
       },
       {
         "type": "location",
         "subtype": "city",
         "name": "ADELAIDE",
         "iataCode": "ADL"
       },
       {
         "type": "location",
         "subtype": "city",
         "name": "AUCKLAND",
         "iataCode": "AKL"
       },
       ...

## Airline Destinations

### Request
    curl -X GET -H "Authorization: Bearer ${BEARER_TOKEN}" "https://test.api.amadeus.com/v1/airline/destinations?airlineCode=QF&max=100" > amadeus.qf.json

### Response
    {
      "meta": {
        "count": 100,
        "links": {
          "self": "https://test.api.amadeus.com/v1/airline/destinations?airlineCode=QF&max=100"
        }
      },
      "data": [
        {
          "type": "location",
          "subtype": "city",
          "name": "ALBUQUERQUE",
          "iataCode": "ABQ"
        },
        {
          "type": "location",
          "subtype": "city",
          "name": "ALBURY",
          "iataCode": "ABX"
        },
        {
          "type": "location",
          "subtype": "city",
          "name": "ABERDEEN",
          "iataCode": "ABZ"
        },
        ..

## Flights

### Request

    curl -X GET -H "Authorization: Bearer ${BEARER_TOKEN}" "https://test.api.amadeus.com/v2/shopping/flight-offers?originLocationCode=BNE&destinationLocationCode=SIN&departureDate=2023-02-02&adults=1&nonStop=false&max=10" > amadeus.bne.sin.json

### Response
    {
    "meta": {
    "count": 10,
    "links": {
      "self": "https://test.api.amadeus.com/v2/shopping/flight-offers?originLocationCode=BNE&destinationLocationCode=SIN&departureDate=2023-02-02&adults=1&nonStop=false&max=10"
    }
    },
    "data": [
    {
      "type": "flight-offer",
      "id": "1",
      "source": "GDS",
      "instantTicketingRequired": false,
      "nonHomogeneous": false,
      "oneWay": false,
      "lastTicketingDate": "2022-12-16",
      "numberOfBookableSeats": 1,
      "itineraries": [
        {
          "duration": "PT28H20M",
          "segments": [
            {
              "departure": {
                "iataCode": "BNE",
                "terminal": "D",
                "at": "2023-02-02T17:50:00"
              },
              "arrival": {
                "iataCode": "MEL",
                "terminal": "4",
                "at": "2023-02-02T21:10:00"
              },
              "carrierCode": "JQ",
              "number": "571",
              "aircraft": {
                "code": "320"
              },
              "operating": {
                "carrierCode": "JQ"
              },
              "duration": "PT2H20M",
              "id": "7",
              "numberOfStops": 0,
              "blacklistedInEU": false
            },
            {
              "departure": {
                "iataCode": "MEL",
                "terminal": "2",
                "at": "2023-02-03T15:20:00"
              },
              "arrival": {
                "iataCode": "SIN",
                "terminal": "1",
                "at": "2023-02-03T20:10:00"
              },
              "carrierCode": "JQ",
              "number": "7",
              "aircraft": {
                "code": "788"
              },
              "operating": {
                "carrierCode": "JQ"
              },
              "duration": "PT7H50M",
              "id": "8",
              "numberOfStops": 0,
              "blacklistedInEU": false
            }
          ]
        }
      ],
      "price": {
        "currency": "EUR",
        "total": "366.78",
        "base": "250.00",
        "fees": [
          {
            "amount": "0.00",
            "type": "SUPPLIER"
          },
          {
            "amount": "0.00",
            "type": "TICKETING"
          }
        ],
        "grandTotal": "366.78"
      },
      "pricingOptions": {
        "fareType": [
          "PUBLISHED"
        ],
        "includedCheckedBagsOnly": true
      },
      "validatingAirlineCodes": [
        "HR"
      ],
      "travelerPricings": [
        {
          "travelerId": "1",
          "fareOption": "STANDARD",
          "travelerType": "ADULT",
          "price": {
            "currency": "EUR",
            "total": "366.78",
            "base": "250.00"
          },
          "fareDetailsBySegment": [
            {
              "segmentId": "7",
              "cabin": "ECONOMY",
              "fareBasis": "HLOW",
              "class": "H",
              "includedCheckedBags": {
                "weight": 20,
                "weightUnit": "KG"
              }
            },
            {
              "segmentId": "8",
              "cabin": "ECONOMY",
              "fareBasis": "CLOW2",
              "class": "C",
              "includedCheckedBags": {
                "weight": 20,
                "weightUnit": "KG"
              }
            }
          ]
        }
      ]
    },
