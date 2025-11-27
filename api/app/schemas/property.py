from pydantic import BaseModel, Field
from typing import Optional, List


class PropertyInput(BaseModel):
    """Input schema for property prediction"""
    bedrooms: int = Field(..., ge=1, le=10, description="Number of bedrooms")
    bathrooms: int = Field(..., ge=1, le=8, description="Number of bathrooms")
    total_area: float = Field(..., gt=20, lt=1000, description="Total area in m²")
    parking_spots: Optional[int] = Field(None, ge=0, le=5, description="Number of parking spots")
    comuna: str = Field(..., description="Comuna/district in Santiago")
    has_pool: Optional[bool] = Field(False, description="Has swimming pool")
    has_gym: Optional[bool] = Field(False, description="Has gym")
    has_security: Optional[bool] = Field(False, description="Has security")
    building_age: Optional[int] = Field(None, ge=0, le=100, description="Building age in years")
    floor_number: Optional[int] = Field(None, ge=1, le=50, description="Floor number")

    class Config:
        json_schema_extra = {
            "example": {
                "bedrooms": 3,
                "bathrooms": 2,
                "total_area": 85.0,
                "parking_spots": 1,
                "comuna": "Las Condes",
                "has_pool": True,
                "has_gym": True,
                "has_security": True,
                "building_age": 5,
                "floor_number": 10
            }
        }


class PredictionOutput(BaseModel):
    """Output schema for price prediction"""
    predicted_price_uf: float = Field(..., description="Predicted price in UF")
    predicted_price_clp: Optional[float] = Field(None, description="Predicted price in CLP (if UF conversion available)")
    confidence_interval: Optional[dict] = Field(None, description="Confidence interval for prediction")
    model_version: str = Field(..., description="Model version used")

    class Config:
        json_schema_extra = {
            "example": {
                "predicted_price_uf": 8500.0,
                "predicted_price_clp": 255000000,
                "confidence_interval": {
                    "lower": 7500.0,
                    "upper": 9500.0
                },
                "model_version": "v1.0"
            }
        }
