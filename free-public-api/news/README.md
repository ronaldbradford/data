# News Headlines

Source: https://saurav.tech/NewsAPI/

## Sources

### Request
    curl -sL https://saurav.tech/NewsAPI/sources.json > sources.json

### Response
    {
      "status": "ok",
      "sources": [
        {
          "id": "abc-news",
          "name": "ABC News",
          "description": "Your trusted source for breaking news, analysis, exclusive interviews, headlines, and videos at ABCNews.com.",
          "url": "https://abcnews.go.com",
          "category": "general",
          "language": "en",
          "country": "us"
        },
        {
          "id": "abc-news-au",
          "name": "ABC News (AU)",
          "description": "Australia's most trusted source of local, national and world news. Comprehensive, independent, in-depth analysis, the latest business, sport, weather and more.",
          "url": "http://www.abc.net.au/news",
          "category": "general",
          "language": "en",
          "country": "au"
        },   
        ...

## Topics

### Request

    curl -sL -X GET 'https://saurav.tech/NewsAPI/top-headlines/category/sports/au.json' |jq . > sport.au.json
    curl -sL -X GET 'https://saurav.tech/NewsAPI/top-headlines/category/technology/us.json' |jq . > technology.us.json
    curl -sL -X GET 'https://saurav.tech/NewsAPI/top-headlines/category/science/gb.json' |jq . > science.gb.json
    curl -sL -X GET 'https://saurav.tech/NewsAPI/top-headlines/category/health/in.json'  | jq . > health.in.json health.json


### Response

    {
      "status": "ok",
      "totalResults": 67,
      "articles": [
        {
          "source": {
            "id": null,
            "name": "Fox Sports"
          },
          "author": "Alex Conrad",
          "title": "Glaring flaw ‘has never been right’; $82m elephant in room: Ten Hag’s Man U to-dos - Fox Sports",
          "description": "Glaring flaw ‘has never been right’; $82m elephant in room: Ten Hag’s Man U to-dos",
          "url": "https://www.foxsports.com.au/football/premier-league/glaring-flaw-that-has-never-been-right-82m-elephant-in-the-room-ten-hags-man-utd-todo-list/news-story/531d464fb46b64f056a29c5aea45f0dd",
          "urlToImage": "https://content.api.news/v3/images/bin/de6ef5b4aebb1254d9613b7b994b8458",
          "publishedAt": "2022-04-21T12:25:00Z",
          "content": "Footballs worst-kept secret has finally been confirmed: Erik ten Hag is the next manager of Manchester United.\r\nThe Dutchman, currently employed by Ajax, will also be eighth man in a decade (includin… [+11745 chars]"
        },
        {
          "source": {
            "id": null,
            "name": "Nine"
          },
          "author": "Chris De Silva",
