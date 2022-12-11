# UK National Archives

## Name Search


### Request

    curl -X GET --header 'Accept: application/json' 'https://discovery.nationalarchives.gov.uk/API/search/v1/records?sps.lastName=bradford&sps.dateOfBirthFrom=1800-01-01&sps.dateOfBirthTo=1810-01-01&sps.searchQuery=bradford' > bradford.1800.json

### Response

    {
      "records": [
        {
          "altName": "",
          "places": [
            "Frenchay Nr Bristol"
          ],
          "corpBodies": [
            "56th (West Essex) Regiment of Foot"
          ],
          "taxonomies": [],
          "formerReferenceDep": "",
          "formerReferencePro": "",
          "heldBy": [
            "The National Archives, Kew"
          ],
          "context": "War Office and predecessors: Secretary-at-War, Secretary of State for War, and Related Bodies, Registers. RETURNS OF OFFICERS' SERVICES. WO 25. 56-60 Foot.",
          "content": "",
          "urlParameters": "66/1/C259/C528/C14234/C77305/0/C4397546/C13323852",
          "department": "WO",
          "note": "",
          "adminHistory": "",
          "arrangement": "",
          "mapDesignation": "",
          "mapScale": "",
          "physicalCondition": "",
          "catalogueLevel": 7,
          "openingDate": "",
          "closureStatus": "O",
          "closureType": "N",
          "closureCode": "30",
          "documentType": "",
          "coveringDates": "[1829]",
          "description": "Folio 66. Name: Edward Joseph Bradford. Date of birth: 21 November 1801. Place of birth: Frenchay Nr Bristol. Regiment: 56th (West Essex) Regiment of Foot. Enlisted as rank: Hospital Assistant ; date: 5 December 1826. Last rank: Assistant Surgeon ; date: 20 March 1828. Married: Not stated.",
          "endDate": "31/12/1829",
          "numEndDate": 18291231,
          "numStartDate": 18290101,
          "startDate": "01/01/1829",
          "id": "C13323852",
          "reference": "WO 25/796/34",
          "score": 0.125107646,
          "source": "100",
          "title": "Folio 66. Name: Edward Joseph Bradford. Date of birth: 21 November 1801. Place of birth:..."
        },
        {
          "altName": "",
          "places": [
            "Canterbury, Kent"
          ],
          "corpBodies": [],
          "taxonomies": [],
          "formerReferenceDep": "",
          "formerReferencePro": "",
          ...
