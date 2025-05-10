# -*- coding: utf-8 -*-
import requests
import datetime
from sqlalchemy import Column, String, Float, Integer, Boolean, JSON, DateTime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import inspect  # Import inspect for table existence check
from src.models.campground import Base, Campground, CampgroundORM  # Import CampgroundORM for validation
from pydantic import ValidationError  # Import ValidationError for handling validation exceptions
import html  # Import html module for escaping special characters

DATABASE_URL = "postgresql://user:password@postgres:5432/case_study"  # Docker PostgreSQL bağlantısı

def init_db():
    """
    Initialize the database and create tables if they do not exist.
    """
    engine = create_engine(DATABASE_URL)
    inspector = inspect(engine)  # Use inspect to check table existence
    if not inspector.has_table("campgrounds"):  # Check if the table exists
        Base.metadata.create_all(engine)  # Create tables only if they do not exist
        print("Database initialized and tables created.")
    else:
        print("Database already initialized. Skipping table creation.")

def test_db_connection():
    """
    Test the database connection and check if tables exist.
    """
    engine = create_engine(DATABASE_URL)
    with engine.connect() as connection:
        result = connection.execute("SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname = 'public';")
        tables = [row[0] for row in result]
        if "campgrounds" in tables:
            print("Table 'campgrounds' exists in the database.")
        else:
            print("Table 'campgrounds' does not exist. Check your database initialization.")

def sanitize_data(data):
    """
    Sanitize data to handle special characters.
    """
    if isinstance(data, str):
        return html.escape(data)  # Escape special characters in strings
    elif isinstance(data, dict):
        return {key: sanitize_data(value) for key, value in data.items()}  # Recursively sanitize dictionaries
    elif isinstance(data, list):
        return [sanitize_data(item) for item in data]  # Recursively sanitize lists
    return data  # Return data as-is for other types

def insert_campground_to_db(session, validated_campground):
    """
    Insert validated campground data into the database.
    If the record already exists, update it dynamically for all columns.
    """
    try:
        # Prepare data for database insertion
        db_data = CampgroundORM.prepare_data_for_db(validated_campground)
        db_data = sanitize_data(db_data)  # Sanitize data to handle special characters

        # Check if the campground already exists
        existing_campground = session.query(CampgroundORM).filter_by(id=db_data["id"]).first()

        if existing_campground:
            print(f"Step 4: Campground already exists. Updating record...")
            # Dynamically update all columns
            for key, value in db_data.items():
                if hasattr(existing_campground, key):
                    setattr(existing_campground, key, value)
            print(f"Step 5: Campground successfully updated: {validated_campground.name}")
        else:
            print(f"Step 4: Campground does not exist. Adding new record...")
            new_campground = CampgroundORM(**db_data)
            session.add(new_campground)
            print(f"Step 5: New campground successfully added: {validated_campground.name}")

        session.commit()
    except Exception as e:
        session.rollback()
        print(f"Error inserting/updating campground {validated_campground.name}: {e}")

def main():
    """
    Main function to scrape, validate, and store campground data.
    """
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    url = "https://thedyrt.com/api/v6/locations/search-results?filter%5Bsearch%5D%5Bdrive_time%5D=any&filter%5Bsearch%5D%5Bair_quality%5D=any&filter%5Bsearch%5D%5Belectric_amperage%5D=any&filter%5Bsearch%5D%5Bmax_vehicle_length%5D=any&filter%5Bsearch%5D%5Bprice%5D=any&filter%5Bsearch%5D%5Brating%5D=any&filter%5Bsearch%5D%5Bbbox%5D=-118.001%2C24.942%2C-77.63%2C50.061&sort=recommended&page%5Bnumber%5D=1&page%5Bsize%5D=500"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Check total count from API response
        total_count = data.get("meta", {}).get("total_count", len(data.get("data", [])))
        print(f"Total campgrounds available in API: {total_count}")

        locations = data.get("data", [])

        if not locations:
            print("No campgrounds found.")
            return

        # Fetch all existing campground IDs from the database
        existing_ids = {campground.id for campground in session.query(CampgroundORM.id).all()}

        for index, location in enumerate(locations, start=1):
            print() if index > 1 else None

            kamp_adi = location.get("attributes", {}).get("name", "Unknown Name")
            kamp_adi = sanitize_data(kamp_adi)  # Sanitize campground name
            print(f"{index}. --- Processing campground: {kamp_adi} ---")

            raw_data = {
                "id": location.get("id"),
                "type": location.get("type"),
                "links": location.get("links", {}),
                **location.get("attributes", {}),
                "index": index
            }
            raw_data = sanitize_data(raw_data)  # Sanitize raw data

            try:
                # Step 1: Validate the raw data
                print("Step 1: Validating raw data...")
                validated_campground = Campground.validate_api_data(raw_data)
                print("Step 2: Validation successful.")

                # Step 3: Save the validated data to the database
                print("Step 3: Saving to the database...")
                insert_campground_to_db(session, validated_campground)

            except ValidationError:
                print("Step 2: Validation failed. Skipping this campground.")
            except Exception as e:
                print(f"Unexpected error while processing campground: {e}")

        print("All campgrounds have been processed.")
        print(f"Processed {len(locations)} out of {total_count} campgrounds.")
    except requests.RequestException as e:
        print("HTTP Request failed:", e)
    except Exception as e:
        print("Unexpected error:", e)
    finally:
        session.close()

if __name__ == "__main__":
    init_db()  # Initialize the database without resetting
    main()
