# Data Mocker API

A lightweight API built with FastAPI that accepts JSON templates and automatically generates randomly populated mock data that adheres to the provided schemas and inferred data types.

## Features
- **Intelligent Inference**: Automatically infers data types based on your JSON keys (e.g., keys containing `name`, `email`, `address`, `price` will generate appropriate mock data using Faker).
- **Multi-Model Support**: Generate mock data for multiple collections at once.
- **Relational Mocking**: Create relational data by referencing fields from previously generated models using `$ref:ModelName.field_name`.

## Requirements
- `uv` (Astral's fast Python package installer and resolver)
- Python 3.12+

## Installation
Run the following command to verify dependencies are installed in your environment:
```bash
uv sync 
# or uv add fastapi uvicorn faker if starting from scratch
```

## Running the API
Start the local development server:
```bash
uv run uvicorn app.main:app --reload
```
The API will be available at `http://127.0.0.1:8000`.

## Usage
Send a `POST` request to `http://127.0.0.1:8000/mock/inferred` or `http://127.0.0.1:8000/mock/explicit` with your payload containing models and their requested counts.

### Single Model Data Mocking (Inferred Types)
```bash
curl -X POST http://127.0.0.1:8000/mock/inferred \
  -H "Content-Type: application/json" \
  -d '{
        "models": {
          "User": {
            "count": 3,
            "template": {
              "user_id": 0,
              "name": "johndoe",
              "email_address": "test@example.com",
              "is_active": true
            }
          }
        }
      }'
```

### Explicit Type Mocking
If you prefer precise control over the generated mock values instead of inferring them, you can construct a template using rigid string definitions and send it to `POST /mock/explicit`. 

Valid types include:
- `DECIMAL{N}` -> Creates a floating point with `N` precision (e.g. `DECIMAL2` becomes `14.50`)
- `INTEGER` -> Creates a random integer.
- `LONG` -> Creates a random long integer (e.g. `287477227047`).
- `TIMESTAMP(format)` -> Creates a date/time string formatted using Python's `strftime` directives (e.g. `TIMESTAMP(%Y-%m-%d)` becomes `2024-08-20`). If no format is provided, defaults to ISO 8601 string.
- `STRING_ALPHA` -> Returns only letters.
- `STRING_NUMERIC` -> Returns only digits.
- `STRING_ALPHA_NUMERIC` -> Returns letters and numbers.
- `STRING` -> Mixed characters including symbols.
- `UUID` -> Generates an MD5 hashed UUID based on the rest of the generated payload for that item.

**Deep Nested Array Behavior:** If you pass an array with a *single* object template, the mocker will automatically generate **3 unique instances** of that mocked inner object.

```bash
curl -X POST http://127.0.0.1:8000/mock/explicit \
  -H "Content-Type: application/json" \
  -d '{
        "models": {
          "Product": {
            "count": 3,
            "template": {
              "id": "UUID",
              "cost": "DECIMAL2",
              "stock": "INTEGER",
              "global_identifier": "LONG",
              "name": "STRING_ALPHA",
              "sku": "STRING_ALPHA_NUMERIC",
              "created_at": "TIMESTAMP(%Y-%m-%dT%H:%M:%S)",
              "related_items": [
                {
                  "item_id": "UUID",
                  "score": "INTEGER"
                }
              ]
            }
          }
        }
      }'
```

### Sample Payload Retrieval
If you want to view a valid body format beforehand, simply call the sample GET endpoints:
- `GET /sample/inferred`
- `GET /sample/explicit`

### BSON Export for MongoDB
Both the inferred and explicit generators support saving data directly to MongoDB's native **BSON** binary format.

To save a BSON file, append `/bson` to either generating endpoint:
- `POST /mock/inferred/bson`
- `POST /mock/explicit/bson`

These endpoints will generate the mocked data, write it to a `.bson` file in the same directory where the API server is running, and return a JSON object containing the absolute path to that file.

```bash
curl -X POST http://127.0.0.1:8000/mock/explicit/bson \
  -H "Content-Type: application/json" \
  -d '{
        "models": {
          "User": {
            "count": 5,
            "template": {
              "id": "UUID",
              "score": "INTEGER"
            }
          }
        }
      }'
```

**Response output:**
```json
{
  "message": "BSON file generated successfully",
  "file_path": "/path/to/data-mocker/mock_explicit_1684342412.bson"
}
```

You can then import this local file directly into your MongoDB cluster using tools like `mongorestore` or `bsondump`!

### Advanced: Related Data Mocking
You can generate multiple collections of mocked data that reference each other. If a field should reference a generated item from another model, use `"$ref:ModelName.field_name"`. 

The API automatically figures out the dependency graph (which models to generate first), and substitutes references with random values plucked from the dependent generated output.

**Request payload:**
```json
{
  "models": {
    "User": {
      "count": 2,
      "template": {
        "user_id": 0,
        "name": "string",
        "email_address": "test@example.com"
      }
    },
    "Order": {
      "count": 5,
      "template": {
        "order_id": 0,
        "user_id": "$ref:User.user_id",
        "total_price": 100.50,
        "status": "string"
      }
    }
  }
}
```

**Response output:**
```json
{
  "User": [
    {
      "user_id": 567003,
      "name": "Carmen Kennedy",
      "email_address": "marthafoster@example.com"
    },
    {
      "user_id": 314566,
      "name": "Joseph Davis",
      "email_address": "ricky60@example.net"
    }
  ],
  "Order": [
    {
      "order_id": 489821,
      "user_id": 314566,
      "total_price": 591.9,
      "status": "since"
    },
    {
      "order_id": 275320,
      "user_id": 567003,
      "total_price": 995.88,
      "status": "area"
    }
  ]
}
```

## Running Tests
To run the automated test suite verifying both basic generation and relational mapping context logic:
```bash
PYTHONPATH=. uv run python tests/test_mock.py
```
