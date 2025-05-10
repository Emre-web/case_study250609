from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, ValidationError, HttpUrl
from sqlalchemy import Column, String, Float, Boolean, Integer, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
import logging

# Configure logging for validation errors
logging.basicConfig(
    filename="validation_errors.log",
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

Base = declarative_base()


class CampgroundLinks(BaseModel):
    """
    Links model to store the full JSON structure as-is.
    """
    self: HttpUrl  # Keep the 'self' field as an HttpUrl for validation


class Campground(BaseModel):
    """
    Base pydantic model, these are the required fields for parsing.
    """
    id: str
    type: str
    links: CampgroundLinks  # Store the full links structure
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
    availability_updated_at: Optional[datetime] = Field(
        None, alias="availability-updated-at"
    )

    @classmethod
    def validate_api_data(cls, raw_data: dict):
        """
        Validates raw data from the API against the Campground model.
        Includes preprocessing and detailed error handling.
        """
        # Preprocessing: Ensure 'links' field is valid
        if "links" in raw_data and isinstance(raw_data["links"], dict):
            try:
                raw_data["links"] = CampgroundLinks(**raw_data["links"])  # Validate links as CampgroundLinks model
            except ValidationError as e:
                raw_data.pop("links", None)  # Remove invalid links field

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
                raw_data[field] = default_value

        try:
            validated_data = cls(**raw_data)
            return validated_data
        except ValidationError as e:
            logging.error(f"Validation failed for data: {raw_data}")
            logging.error(f"Errors: {e.errors()}")
            raise e


class CampgroundORM(Base):
    """
    SQLAlchemy ORM model for the Campground table.
    """
    __tablename__ = "campgrounds"

    id = Column(String, primary_key=True)
    type = Column(String, nullable=False)
    links = Column(JSON, nullable=True)  # Store links as JSON to preserve full structure
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
        """
        Prepare validated campground data for database insertion.
        Converts non-serializable fields (e.g., HttpUrl, datetime) to serializable formats.
        """
        data = validated_campground.dict()

        # Convert all HttpUrl and datetime fields to serializable formats
        def convert_to_serializable(obj):
            if isinstance(obj, HttpUrl):
                return str(obj)  # Convert HttpUrl to string
            elif isinstance(obj, datetime):
                return obj.isoformat()  # Convert datetime to ISO 8601 string
            elif isinstance(obj, dict):
                return {k: convert_to_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_to_serializable(item) for item in obj]
            return obj

        data = convert_to_serializable(data)
        return data


# Example usage for testing with API data
if __name__ == "__main__":
    import requests

    # Replace with your API endpoint or scraper logic
    api_url = "https://example.com/api/campgrounds"
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        try:
            api_data = response.json()
        except ValueError:
            print("Error: API response is not valid JSON.")
            logging.error("API response is not valid JSON.")
            api_data = []

        # Validate and save each campground in the API response
        total_count = len(api_data)
        for index, campground_data in enumerate(api_data, start=1):
            print(f"\n--- Processing campground {index}/{total_count} ---")
            try:
                validated_campground = Campground.validate_api_data(campground_data)
                # Simulate saving to the database
                print(f"Saving campground {index}/{total_count} to the database...")
                # Example: CampgroundORM.prepare_data_for_db(validated_campground) (actual DB save logic here)
                print(f"Successfully saved campground {index}/{total_count}: {validated_campground.id}, Name: {validated_campground.name}")
            except ValidationError:
                print(f"Invalid data encountered for campground {index}. Skipping...")
        
        print("\nAll campgrounds processed and saved successfully.")
    except requests.RequestException as e:
        print(f"Failed to fetch data from API: {e}")
        logging.error(f"Failed to fetch data from API: {e}")
