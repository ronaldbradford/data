# Chess

https://www.chess.com/news/view/published-data-api

## Leaderboard

### Request

   curl -sL https://api.chess.com/pub/leaderboards > leaderboards.json

### Response

    {
      "daily": [
      {
        "player_id": 19872960,
        "@id": "https://api.chess.com/pub/player/igorkovalenko",
        "url": "https://www.chess.com/member/igorkovalenko",
        "username": "igorkovalenko",
        "score": 2715,
        "rank": 1,
        "country": "https://api.chess.com/pub/country/UA",
        "title": "GM",
        "name": "Igor Kovalenko",
        "status": "premium",
        "avatar": "https://images.chesscomfiles.com/uploads/v1/user/19872960.df6ef125.200x200o.f2651789b1f6.jpeg",
        "trend_score": {
          "direction": 0,
          "delta": 0
        },
        "trend_rank": {
          "direction": 0,
          "delta": 0
        },
        "flair_code": "diamond_traditional",
        "win_count": 105,
        "loss_count": 1,
        "draw_count": 7
      },
      ...

## Player

### Request
    curl -sL https://api.chess.com/pub/player/igorkovalenko > igorkovalenko.json

### Response

    {
      "avatar": "https://images.chesscomfiles.com/uploads/v1/user/19872960.df6ef125.200x200o.f2651789b1f6.jpeg",
      "player_id": 19872960,
      "@id": "https://api.chess.com/pub/player/igorkovalenko",
      "url": "https://www.chess.com/member/igorkovalenko",
      "name": "Igor Kovalenko",
      "username": "igorkovalenko",
      "title": "GM",
      "followers": 592,
      "country": "https://api.chess.com/pub/country/UA",
      "location": "Kyiv",
      "last_online": 1670578819,
      "joined": 1416817838,
      "status": "premium",
      "is_streamer": false,
      "verified": false
    }
