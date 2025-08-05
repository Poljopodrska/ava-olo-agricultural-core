from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/api/v1/fields", tags=["fields"])

class FieldCreate(BaseModel):
    name: str
    size: float
    crop: str
    polygon: Optional[List[List[float]]] = None

# Mock field data
fields = [
    {
        "id": 1,
        "name": "North Field",
        "size": 10.5,
        "crop": "wheat",
        "polygon": [[42.6977, 23.3219], [42.6978, 23.3220], [42.6979, 23.3221]]
    },
    {
        "id": 2,
        "name": "South Field", 
        "size": 8.2,
        "crop": "corn",
        "polygon": [[42.6970, 23.3210], [42.6971, 23.3211], [42.6972, 23.3212]]
    }
]

@router.get("")
async def get_fields(farmer_id: int = 1):
    """Get farmer fields"""
    return JSONResponse(content={
        "fields": fields,
        "farmer_id": farmer_id,
        "total": len(fields)
    })

@router.get("/{field_id}")
async def get_field(field_id: int):
    """Get specific field"""
    for field in fields:
        if field["id"] == field_id:
            return JSONResponse(content=field)
    
    return JSONResponse(content={
        "error": "Field not found"
    }, status_code=404)

@router.post("")
async def create_field(field: FieldCreate, farmer_id: int = 1):
    """Create new field"""
    new_field = {
        "id": len(fields) + 1,
        "name": field.name,
        "size": field.size,
        "crop": field.crop,
        "polygon": field.polygon or [],
        "farmer_id": farmer_id
    }
    fields.append(new_field)
    
    return JSONResponse(content={
        "success": True,
        "field": new_field
    })

@router.get("/debug/edi-kante")
async def debug_edi_kante():
    """Debug endpoint for Edi Kante field display"""
    return JSONResponse(content={
        "message": "Edi Kante fields debug",
        "fields": [
            {
                "id": 999,
                "name": "Edi Kante Test Field",
                "size": 15.5,
                "crop": "tomatoes",
                "status": "debug_mode"
            }
        ]
    })