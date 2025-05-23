from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ValidationError, HttpUrl
import logging

class CampgroundLinks(BaseModel):
    self: HttpUrl

class Campground(BaseModel):
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
        # Preprocessing: Ensure 'links' field is valid
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
