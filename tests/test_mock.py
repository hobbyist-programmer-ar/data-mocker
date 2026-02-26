import json
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_mock_generation():
    payload = {
        "models": {
            "User": {
                "count": 2,
                "template": {
                    "user_id": 0,
                    "name": "johndoe",
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

    response = client.post("/mock/inferred", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert "User" in data
    assert "Order" in data
    assert len(data["User"]) == 2
    assert len(data["Order"]) == 5
    
    # Verify Relationships
    generated_user_ids = [u["user_id"] for u in data["User"]]
    for order in data["Order"]:
        assert order["user_id"] in generated_user_ids

def test_bson_generation():
    import bson
    import os
    payload = {
        "models": {
            "User": {
                "count": 2,
                "template": {
                    "user_id": 0,
                    "name": "string"
                }
            }
        }
    }
    response = client.post("/mock/inferred/bson", json=payload)
    assert response.status_code == 200
    
    # Check that it returns a JSON response with file_path
    data = response.json()
    assert "file_path" in data
    assert "successfully" in data["message"]
    
    file_path = data["file_path"]
    assert os.path.exists(file_path)
    
    # Read and decode the BSON file
    with open(file_path, "rb") as f:
        raw_data = f.read()
    
    decoded_data = bson.BSON.decode(raw_data)
    
    assert "User" in decoded_data
    assert len(decoded_data["User"]) == 2
    assert isinstance(decoded_data["User"][0]["user_id"], int)
    
    # Clean up
    os.remove(file_path)

if __name__ == "__main__":
    test_mock_generation()
    test_bson_generation()
    print("\n✅ All tests passed!")
