from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, HttpUrl, ValidationError
from sqlalchemy import Column, String, Float, Boolean, Integer, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class CampgroundLinks(BaseModel):

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
    photo_url: Optional[HttpUrl] = Field(None, alias="photo-url")
    photo_urls: List[HttpUrl] = Field([], alias="photo-urls")
    photos_count: int = Field(0, alias="photos-count")
    rating: Optional[float] = None
    reviews_count: int = Field(0, alias="reviews-count")
    slug: Optional[str] = Field(None, alias="slug")
    price_low: Optional[float] = Field(None, alias="price-low")
    price_high: Optional[float] = Field(None, alias="price-high")
    availability_updated_at: Optional[datetime] = Field(
        None, alias="availability-updated-at"
    )
    # address: Optinal[str] = "" For bonus point

    @classmethod
    def validate_api_data(cls, raw_data: dict):
        """
        Validates raw data from the API against the Campground model.
        Includes preprocessing and detailed error handling.
        """
        print("\n--- Starting validation process for a campground ---")

        # Preprocessing: Remove undefined or invalid 'links' field
        if not raw_data.get("links") or not isinstance(raw_data["links"], dict):
            print("Preprocessing: 'links' field is missing or invalid. Removing it from raw data.")
            raw_data.pop("links", None)

        # Preprocessing: Ensure all required fields are present with default values if missing
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
                print(f"Preprocessing: Missing field '{field}'. Setting default value: {default_value}")
                raw_data[field] = default_value

        try:
            print("Step 1: Parsing raw data into Campground model...")
            validated_data = cls(**raw_data)
            print(f"Step 2: Validation successful for Campground ID: {validated_data.id}, Name: {validated_data.name}")
            return validated_data
        except ValidationError as e:
            print("Step 2: Validation failed!")
            print("Validation Errors (detailed):")
            for error in e.errors():
                print(f"Field: {error['loc']}")
                print(f"  Expected Type: {error['type']}")
                print(f"  Error Message: {error['msg']}")
                print("-------------------------")
            raise e


class CampgroundORM(Base):
    """
    SQLAlchemy ORM model for the Campground table.
    """
    __tablename__ = "campgrounds"

    id = Column(String, primary_key=True)
    type = Column(String, nullable=False)
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


# Example usage for testing with API data
if __name__ == "__main__":
    import requests

    # Replace with your API endpoint or scraper logic
    api_url = "https://example.com/api/campgrounds"
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        api_data = response.json()

        # Validate each campground in the API response
        for campground_data in api_data:
            try:
                Campground.validate_api_data(campground_data)
            except ValidationError:
                print("Invalid data encountered. Skipping...")
    except requests.RequestException as e:
        print(f"Failed to fetch data from API: {e}")
