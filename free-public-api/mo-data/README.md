# State of Missouri Data Portal

## Financial Expenses

### Request

    curl -sL 'https://data.mo.gov/api/views/27js-tn42/rows.json?accessType=DOWNLOAD' > finance.json

### Response

    {
      "meta": {
        "view": {
          "id": "27js-tn42",
          "name": "2000 State Expenditures",
          "assetType": "dataset",
          "attribution": "Office of Administration",
          "averageRating": 0,
          "category": "Government Administration",
          "createdAt": 1594648891,
          "description": "Financial data relating to the purchases of goods and services by the state as well as financial disbursements through various state programs",
          "displayType": "table",
    ....
        [
          "row-c5tq.iwhp.gqkm",
          "00000000-0000-0000-F9C3-F01BCB2180F6",
          0,
          1594649505,
          null,
          1594649505,
          null,
          "{ }",
          "2000",
          "AGRICULTURE",
          "BUILDING LEASE PAYMENTS",
          "BLDG/STORAGE/STRUCTURE LEASES  CAPITAL",
          "WHATS UP DOCK",
          "214.18"
        ],
    

## Liquor Licenses

### Request
   
    curl -sL 'https://data.mo.gov/api/views/fkt2-8smh/rows.json?accessType=DOWNLOAD' > liqour-licenses.json
