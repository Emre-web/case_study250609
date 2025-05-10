# -*- coding: utf-8 -*-
import requests
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.models.campground import Base

DATABASE_URL = "postgresql://user:password@postgres:5432/case_study"  # Docker PostgreSQL bağlantısı

def init_db():
    """
    Initialize the database and create tables.
    """
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(engine)
    print("Database initialized and tables created.")

def main():
    print("Hello Smart Maple!")

    url = "https://thedyrt.com/api/v6/locations/search-results?filter%5Bsearch%5D%5Bdrive_time%5D=any&filter%5Bsearch%5D%5Bair_quality%5D=any&filter%5Bsearch%5D%5Belectric_amperage%5D=any&filter%5Bsearch%5D%5Bmax_vehicle_length%5D=any&filter%5Bsearch%5D%5Bprice%5D=any&filter%5Bsearch%5D%5Brating%5D=any&filter%5Bsearch%5D%5Bbbox%5D=-118.001%2C24.942%2C-77.63%2C50.061&sort=recommended&page%5Bnumber%5D=1&page%5Bsize%5D=500"

    response = requests.get(url)

    if response.status_code == 200:
        print(f"Debug: API response received successfully at {datetime.datetime.now()}")  # Debug print with timestamp
        data = response.json()
        locations = data.get("data", [])
        print(f"{len(locations)} kamp alanı bulundu yupiii denedim sanırm oldu.")
    else:
        print(f"Error: {response.status_code}")
        print(f"Debug: Response content at {datetime.datetime.now()}: {response.text}")  # Debug print with timestamp


if __name__ == "__main__":
    init_db()
    main()
