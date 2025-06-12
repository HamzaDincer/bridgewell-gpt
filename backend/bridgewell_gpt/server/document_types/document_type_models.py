from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# Pydantic model matching the frontend DocumentType interface
class DocumentTypeResponse(BaseModel):
    id: int # Or str
    title: str
    uploaded: int
    reviewPending: int = Field(alias="review_pending") # Keep alias if frontend expects camelCase
    approved: int
    setupRequired: bool = Field(alias="setup_required") # Keep alias if frontend expects camelCase
    documents: List["DocumentResponse"] = [] # Add documents list

    class Config:
        from_attributes = True # Or orm_mode=True for older Pydantic 
        allow_population_by_field_name = True # Allows using snake_case internally

# Request model for creating a new type
class DocumentTypeCreate(BaseModel):
    title: str = Field(..., min_length=1, description="The title of the new document type")

    class Config:
        schema_extra = {
            "example": {
                "title": "Contracts"
            }
        } 

# Document models
class DocumentCreate(BaseModel):
    doc_id: str = Field(..., description="The ID of the document to associate")
    doc_name: str = Field(..., description="The name of the document")

class DocumentResponse(BaseModel):
    id: str
    name: str
    date_added: datetime
    phase: Optional[str] = None  # Add phase for granular status

    class Config:
        from_attributes = True
        allow_population_by_field_name = True 