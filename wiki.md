# MemeLord REST API

## Authentication

All API endpoints require a Bearer token sent in the `Authorization` header.

```
Authorization: Bearer <your_token>
```

Tokens are managed at **Account → API Tokens** (`/accounts/api-tokens/`).  
A token grants the same read access as the account it belongs to.  
Tokens are shown **once** at creation — store them securely.

---

## Endpoints

### `GET /api/memes/`

Returns a paginated list of memes the authenticated user has access to.

#### Query Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `username` | string | Filter by uploader username (exact, case-insensitive) | `?username=alice` |
| `title` | string | Partial title search (case-insensitive) | `?title=cat` |
| `tag` | string | Filter by tag slug. Repeat for AND logic | `?tag=funny&tag=cats` |
| `date_from` | date | Uploaded on or after this date (`YYYY-MM-DD`) | `?date_from=2024-01-01` |
| `date_to` | date | Uploaded on or before this date (`YYYY-MM-DD`) | `?date_to=2024-12-31` |
| `media_type` | string | `image` or `video` | `?media_type=image` |
| `ordering` | string | Sort order: `-upload_date` (default), `upload_date`, `title`, `-title` | `?ordering=title` |
| `page` | integer | Page number (default: `1`) | `?page=2` |
| `page_size` | integer | Results per page, 1–100 (default: `20`) | `?page_size=50` |

#### Response

```json
{
  "count": 170,
  "page": 1,
  "page_size": 20,
  "next": "http://example.com/api/memes/?page=2",
  "previous": null,
  "results": [
    {
      "id": 42,
      "title": "My Meme",
      "tags": ["funny", "cats"],
      "upload_date": "2024-06-01T10:00:00+00:00",
      "author": "alice",
      "media_type": "image",
      "image_url": "https://example.com/media/memes/user_1/meme.jpg",
      "thumbnail_url": "https://example.com/media/memes/user_1/meme_thumb.jpg",
      "comments": [
        {
          "author": "bob",
          "text": "lol",
          "date": "2024-06-02T08:30:00+00:00"
        }
      ]
    }
  ]
}
```

---

### `GET /api/memes/random/`

Returns a single random meme the authenticated user has access to.  
Accepts all the same filter parameters as `/api/memes/` except `ordering`, `page`, and `page_size`.

#### Response

Same structure as a single item in the `results` array above.

Returns `404` if no memes match the given filters.

---

## Error Responses

| HTTP Status | Cause |
|-------------|-------|
| `401` | Missing, invalid, or revoked token |
| `400` | Invalid parameter value (e.g. bad date format, unknown `media_type`) |
| `404` | No memes found (random endpoint only) |

Error body:

```json
{ "error": "Description of the problem." }
```

---

## Examples

```bash
# List all memes (newest first)
curl -H "Authorization: Bearer TOKEN" https://example.com/api/memes/

# Filter by uploader and tag
curl -H "Authorization: Bearer TOKEN" \
     "https://example.com/api/memes/?username=alice&tag=funny"

# Partial title search, images only, sorted A–Z
curl -H "Authorization: Bearer TOKEN" \
     "https://example.com/api/memes/?title=cat&media_type=image&ordering=title"

# Memes uploaded in 2024, page 2
curl -H "Authorization: Bearer TOKEN" \
     "https://example.com/api/memes/?date_from=2024-01-01&date_to=2024-12-31&page=2"

# Get a random meme
curl -H "Authorization: Bearer TOKEN" https://example.com/api/memes/random/

# Get a random image from a specific user
curl -H "Authorization: Bearer TOKEN" \
     "https://example.com/api/memes/random/?username=alice&media_type=image"
```

---

## Token Management

1. Log in to MemeLord and open **Account → API Tokens** from the navbar.
2. Enter a label and click **Generate token**.
3. Copy the token immediately — it is shown **only once**.
4. Tokens can be **revoked** (deactivated) or **deleted** at any time from the same page.
