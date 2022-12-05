# Beer Styles

12/22 This API appears to be no longer available, however the source JSON can be found at https://github.com/drodil/rustybeer/tree/master/rustybeer/src/json

### Request

    curl -sL -X GET 'https://rustybeer.herokuapp.com/styles'

### Response

    [
      {
        "name": "Lite American Lager",
        "original_gravity_min": 1.028,
        "original_gravity_max": 1.04,
        "final_gravity_min": 0.998,
        "final_gravity_max": 1.008,
        "abv_min": 2.8,
        "abv_max": 4.2,
        "ibu_min": 8,
        "ibu_max": 12,
        "color_srm_min": 2,
        "color_srm_max": 3,
        "description": "Highly carbonated, very light-bodied, nearly flavorless lager designed to be consumed very cold. Very refreshing and thirst quenching."
      },


### Source JSON

    curl -sL https://raw.githubusercontent.com/drodil/rustybeer/master/rustybeer/src/json/beer_styles.json
    curl -sL https://raw.githubusercontent.com/drodil/rustybeer/master/rustybeer/src/json/hops.json
    curl -sL https://raw.githubusercontent.com/drodil/rustybeer/master/rustybeer/src/json/yeasts.json
    curl -sL https://raw.githubusercontent.com/drodil/rustybeer/master/rustybeer/src/json/abv_calories.json
