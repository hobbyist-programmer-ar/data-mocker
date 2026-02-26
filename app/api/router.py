from fastapi import APIRouter, HTTPException, Body, Response
from typing import Any, Dict, List
from pydantic import BaseModel, Field
import bson
from app.core.generator import generate_mock_models
from app.core.explicit_generator import generate_explicit_models

router = APIRouter()

class ModelConfig(BaseModel):
    count: int = Field(gt=0, le=10000, description="Number of mocked json objects to generate")
    template: Dict[str, Any] = Field(description="Sample JSON template to infer structure and types from")

class MockRequest(BaseModel):
    models: Dict[str, ModelConfig] = Field(..., description="Dictionary mapping model names to their configurations")

@router.post("/mock/inferred", response_model=Dict[str, List[Dict[str, Any]]])
async def generate_mock_data(request: MockRequest = Body(...)):
    """
    Generate mock data based on provided JSON templates using heuristic inference and cross-references.
    """
    if not request.models:
        raise HTTPException(status_code=400, detail="Models dictionary cannot be empty")
        
    try:
        configs = {name: {"count": conf.count, "template": conf.template} for name, conf in request.models.items()}
        result = generate_mock_models(configs)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/mock/inferred/bson")
async def generate_mock_data_bson(request: MockRequest = Body(...)):
    """
    Generate mock data based on provided JSON templates using heuristic inference and cross-references.
    Returns the payload as a BSON binary encoded file.
    """
    if not request.models:
        raise HTTPException(status_code=400, detail="Models dictionary cannot be empty")
        
    try:
        configs = {name: {"count": conf.count, "template": conf.template} for name, conf in request.models.items()}
        result = generate_mock_models(configs)
        bson_data = bson.BSON.encode(result)
        return Response(content=bson_data, media_type="application/bson")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/mock/explicit", response_model=Dict[str, List[Dict[str, Any]]])
async def generate_explicit_mock_data(request: MockRequest = Body(...)):
    """
    Generate mock data strictly adhering to explicitly defined string format rules (e.g. DECIMAL2).
    """
    if not request.models:
        raise HTTPException(status_code=400, detail="Models dictionary cannot be empty")
        
    try:
        configs = {name: {"count": conf.count, "template": conf.template} for name, conf in request.models.items()}
        result = generate_explicit_models(configs)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/mock/explicit/bson")
async def generate_explicit_mock_data_bson(request: MockRequest = Body(...)):
    """
    Generate mock data strictly adhering to explicitly defined string format rules (e.g. DECIMAL2).
    Returns the payload as a BSON binary encoded file.
    """
    if not request.models:
        raise HTTPException(status_code=400, detail="Models dictionary cannot be empty")
        
    try:
        configs = {name: {"count": conf.count, "template": conf.template} for name, conf in request.models.items()}
        result = generate_explicit_models(configs)
        bson_data = bson.BSON.encode(result)
        return Response(content=bson_data, media_type="application/bson")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/sample/inferred", response_model=Dict[str, Any])
async def get_sample_inferred_payload():
    """Returns a sample payload using heuristic type inference and relational data mapping."""
    return {
      "models": {
        "User": {
          "count": 2,
          "template": {
            "user_id": 0,
            "name": "string",
            "email_address": "test@example.com",
            "is_active": True
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

@router.get("/sample/explicit", response_model=Dict[str, Any])
async def get_sample_explicit_payload():
    """Returns a sample payload using the explicit string type generator functionality."""
    return {
      "models": {
        "Product": {
          "count": 3,
          "template": {
            "id": "UUID",
            "cost": "DECIMAL2",
            "name": "STRING_ALPHA",
            "sku": "STRING_ALPHA_NUMERIC",
            "secret_code": "STRING",
            "created_at": "TIMESTAMP(%Y-%m-%dT%H:%M:%S)",
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
