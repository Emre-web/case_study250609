# -*- coding: utf-8 -*-
import requests
import datetime
from sqlalchemy import Column, String, Float, Integer, Boolean, JSON, DateTime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.models.campground import Base, Campground  # Import Campground model for validation
from pydantic import ValidationError  # Import ValidationError for handling validation exceptions

DATABASE_URL = "postgresql://user:password@postgres:5432/case_study"  # Docker PostgreSQL bağlantısı

def init_db():
    """
    Initialize the database and create tables.
    """
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(engine)
    print("Database initialized and tables created.")

def log_campground_data(validated_campground):
    """
    Log validated campground data in a structured format.
    """
    print("\n--- Validated Campground ---")
    for key, value in validated_campground.dict().items():
        print(f"{key}: {value}")
    print("----------------------------\n")

def main():
    url = "https://thedyrt.com/api/v6/locations/search-results?filter%5Bsearch%5D%5Bdrive_time%5D=any&filter%5Bsearch%5D%5Bair_quality%5D=any&filter%5Bsearch%5D%5Belectric_amperage%5D=any&filter%5Bsearch%5D%5Bmax_vehicle_length%5D=any&filter%5Bsearch%5D%5Bprice%5D=any&filter%5Bsearch%5D%5Brating%5D=any&filter%5Bsearch%5D%5Bbbox%5D=-118.001%2C24.942%2C-77.63%2C50.061&sort=recommended&page%5Bnumber%5D=1&page%5Bsize%5D=500"

    response = requests.get(url)

    if response.status_code == 200:
        print(f"Debug: API response received successfully at {datetime.datetime.now()}")  # Debug print with timestamp
        data = response.json()
        locations = data.get("data", [])
        
        if locations:
            for index, location in enumerate(locations, start=1):  # Process all locations
                print(f"Processing campground #{index}")  # Display the index in the terminal
                attributes = location.get("attributes", {})
                raw_data = {
                    "id": location.get("id"),
                    "type": location.get("type"),
                    "links": {"self": location.get("links", {}).get("self")},
                    **attributes,
                    "index": index  # Add index to raw data for validation
                }
                try:
                    # Validate the raw data using Campground model
                    validated_campground = Campground.validate_api_data(raw_data)
                    log_campground_data(validated_campground)  # Log validated data
                except ValidationError as e:
                    print(f"\n--- Validation Error for campground #{index} ---")  # Include index in error message
                    for error in e.errors():
                        print(f"Field: {error['loc']}")
                        print(f"  Expected Type: {error['type']}")
                        print(f"  Error Message: {error['msg']}")
                        print("-------------------------")
        else:
            print("No campgrounds found.")
    else:
        print(f"Error: {response.status_code}")
        print(f"Debug: Response content at {datetime.datetime.now()}: {response.text}")  # Debug print with timestamp

""
if __name__ == "__main__":
    init_db()
    main()
