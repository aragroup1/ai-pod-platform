from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict
from pydantic import BaseModel, Field

router = APIRouter()

class ProviderCreate(BaseModel):
    name: str
    display_name: str
    api_key: str
    template: str
    base_url: str

@router.get("/providers")
async def get_providers():
    """Get all AI providers"""
    return {"providers": [], "total": 0}

@router.post("/providers")
async def create_provider(provider: ProviderCreate):
    """Add new AI provider"""
    return {"message": "Provider added", "name": provider.name}
