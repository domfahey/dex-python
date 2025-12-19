# Authentication

This guide covers how to use specific headers for authentication and authorization.

## Base URL

```
https://api.getdex.com/api/rest
```

## Headers

These are included in all requests.

### Content-Type

```
Content-Type: application/json
```

### API Key

```
x-hasura-dex-api-key: your-api-key
```

The `x-hasura-dex-api-key` header should contain the user's API key. This key is used for identifying the user and further processing the request. To use it, include the `x-hasura-dex-api-key` header with the value being your personal API key in your API requests.

## Your Personal API Key

You can find your API Key on the API page within your Dex account.

**Do not share your API key!**
