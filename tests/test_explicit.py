import json
import re
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_explicit_mock_generation():
    payload = {
        "models": {
            "Product": {
                "count": 2,
                "template": {
                    "id": "UUID",
                    "cost": "DECIMAL2",
                    "stock": "DECIMAL0",
                    "name": "STRING_ALPHA",
                    "sku": "STRING_ALPHA_NUMERIC",
                    "barcode": "STRING_NUMERIC",
                    "secret": "STRING",
                    "fixed_val": 100,
                    "created_at": "TIMESTAMP(%Y-%m-%d)",
                    "updated_at": "TIMESTAMP",
                    "views": "INTEGER",
                    "global_id": "LONG",
                    "related_items": [
                        {
                            "item_id": "UUID",
                            "score": "INTEGER"
                        }
                    ]
                }
            }
        }
    }

    response = client.post("/mock/explicit", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    
    print("Explicit Response JSON:")
    print(json.dumps(data, indent=2))
    
    assert "Product" in data
    products = data["Product"]
    assert len(products) == 2
    
    for product in products:
        # Check UUID format
        assert re.match(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", product["id"])
        
        # Check Decimal Types
        assert isinstance(product["cost"], float)
        assert len(str(product["cost"]).split(".")[1]) <= 2
        assert isinstance(product["stock"], float)
        
        # Check STRING_ALPHA
        assert product["name"].isalpha()
        
        # Check STRING_ALPHA_NUMERIC
        assert product["sku"].isalnum()
        
        # Check STRING_NUMERIC
        assert product["barcode"].isdigit()
        
        # Check STRING (includes punctuation)
        assert isinstance(product["secret"], str)
        
        # Check literal pass-through
        assert product["fixed_val"] == 100
        
        # Check TIMESTAMP logic
        assert re.match(r"^\d{4}-\d{2}-\d{2}$", product["created_at"])  # %Y-%m-%d format
        assert "T" in product["updated_at"]  # ISO format
        
        # Check Integer/Long formatting
        assert isinstance(product["views"], int)
        assert isinstance(product["global_id"], int)
        assert product["global_id"] >= 1000000000
        
        # Check Deep Object Arrays
        assert isinstance(product["related_items"], list)
        assert len(product["related_items"]) == 3
        for item in product["related_items"]:
            assert "item_id" in item
            assert "score" in item
            assert isinstance(item["score"], int)
            assert re.match(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", item["item_id"])

def test_sample_endpoints():
    res1 = client.get("/sample/inferred")
    assert res1.status_code == 200
    assert "models" in res1.json()
    
    res2 = client.get("/sample/explicit")
    assert res2.status_code == 200
    assert "models" in res2.json()

if __name__ == "__main__":
    test_explicit_mock_generation()
    test_sample_endpoints()
    print("\n✅ All explicit tests passed!")
