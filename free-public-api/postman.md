# Postman

## Sending a Request

https://learning.postman.com/docs/getting-started/sending-the-first-request/

### Request

    curl -sL https://api.github.com/

### Response

    {
      "args": {},
      "headers": {
        "x-forwarded-proto": "https",
        "x-forwarded-port": "443",
        "host": "postman-echo.com",
        "x-amzn-trace-id": "Root=1-63896323-2f2155707fe3affd2a54deff",
        "user-agent": "curl/7.84.0",
        "accept": "*/*"
      },
      "url": "https://postman-echo.com/get"
    }
