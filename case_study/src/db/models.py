from sqlalchemy import Column, String, Float, Boolean, Integer, DateTime, JSON
from src.db.base import Base
from pydantic import HttpUrl
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ValidationError, HttpUrl
import logging

class CampgroundORM(Base):
    __tablename__ = "campgrounds"
    id = Column(String, primary_key=True)
    type = Column(String, nullable=False)
    links = Column(JSON, nullable=True)
    name = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    region_name = Column(String, nullable=False)
    administrative_area = Column(String, nullable=True)
    nearest_city_name = Column(String, nullable=True)
    accommodation_type_names = Column(JSON, nullable=False, default=[])
    bookable = Column(Boolean, nullable=False, default=False)
    camper_types = Column(JSON, nullable=False, default=[])
    operator = Column(String, nullable=True)
    photo_url = Column(String, nullable=True)
    photo_urls = Column(JSON, nullable=False, default=[])
    photos_count = Column(Integer, nullable=False, default=0)
    rating = Column(Float, nullable=True)
    reviews_count = Column(Integer, nullable=False, default=0)
    slug = Column(String, nullable=True)
    price_low = Column(Float, nullable=True)
    price_high = Column(Float, nullable=True)
    availability_updated_at = Column(DateTime, nullable=True)

    @staticmethod
    def prepare_data_for_db(validated_campground):
        data = validated_campground.dict()
        def convert_to_serializable(obj):
            if isinstance(obj, HttpUrl):
                return str(obj)
            elif isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, dict):
                return {k: convert_to_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_to_serializable(item) for item in obj]
            return obj
        data = convert_to_serializable(data)
        return data

class CampgroundLinks(BaseModel):
    """
    Links model to store the full JSON structure as-is.
    """
    self: HttpUrl

class Campground(BaseModel):
    """
    Base pydantic model, these are the required fields for parsing.
    """
    id: str
    type: str
    links: CampgroundLinks
    name: str
    latitude: float
    longitude: float
    region_name: str = Field(..., alias="region-name")
    administrative_area: Optional[str] = Field(None, alias="administrative-area")
    nearest_city_name: Optional[str] = Field(None, alias="nearest-city-name")
    accommodation_type_names: List[str] = Field([], alias="accommodation-type-names")
    bookable: bool = False
    camper_types: List[str] = Field([], alias="camper-types")
    operator: Optional[str] = None
    photo_url: Optional[str] = Field(None, alias="photo-url")
    photo_urls: List[str] = Field([], alias="photo-urls")
    photos_count: int = Field(0, alias="photos-count")
    rating: Optional[float] = None
    reviews_count: int = Field(0, alias="reviews-count")
    slug: Optional[str] = Field(None, alias="slug")
    price_low: Optional[float] = Field(None, alias="price-low")
    price_high: Optional[float] = Field(None, alias="price-high")
    availability_updated_at: Optional[datetime] = Field(None, alias="availability-updated-at")

    @classmethod
    def validate_api_data(cls, raw_data: dict):
        if "links" in raw_data and isinstance(raw_data["links"], dict):
            try:
                raw_data["links"] = CampgroundLinks(**raw_data["links"])
            except ValidationError as e:
                raw_data.pop("links", None)
        required_fields_with_defaults = {
            "bookable": False,
            "accommodation-type-names": [],
            "camper-types": [],
            "photo-urls": [],
            "photos-count": 0,
            "reviews-count": 0,
        }
        for field, default_value in required_fields_with_defaults.items():
            if field not in raw_data:
                raw_data[field] = default_value
        try:
            validated_data = cls(**raw_data)
            return validated_data
        except ValidationError as e:
            logger = logging.getLogger(__name__)
            logger.warning(f"Validation failed for data: {raw_data} | Errors: {e.errors()}")
            raise e
