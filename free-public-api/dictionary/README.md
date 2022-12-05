# Dictionary

##  Word Definition

### Request

    curl -sL https://api.dictionaryapi.dev/api/v2/entries/en/life

### Response

    [
      {
        "word": "life",
        "phonetic": "/laɪf/",
        "phonetics": [
          {
            "text": "/laɪf/",
            "audio": "https://api.dictionaryapi.dev/media/pronunciations/en/life-uk.mp3",
            "sourceUrl": "https://commons.wikimedia.org/w/index.php?curid=9023195",
            "license": {
              "name": "BY 3.0 US",
              "url": "https://creativecommons.org/licenses/by/3.0/us"
            }
          },
          {
            "text": "/laɪf/",
            "audio": "https://api.dictionaryapi.dev/media/pronunciations/en/life-us.mp3",
            "sourceUrl": "https://commons.wikimedia.org/w/index.php?curid=2423294",
            "license": {
              "name": "BY-SA 3.0",
              "url": "https://creativecommons.org/licenses/by-sa/3.0"
            }
          }
        ],
        "meanings": [
          {
            "partOfSpeech": "noun",
            "definitions": [
              {
                "definition": "The state of organisms preceding their death, characterized by biological processes such as metabolism and reproduction and distinguishing them from inanimate objects; the state of being alive and living.",
                "synonyms": [],
                "antonyms": [],
                "example": "Having experienced both, the vampire decided that he preferred (un)death to life.  He gave up on life."
              },
              ...
