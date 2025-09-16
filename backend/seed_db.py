import json
import MySQLdb
import os
from logger import logger
from utils.constants import QUALITY_VALUES
from utils.helpers import clear_forever_cache_keys, is_valid_id
from app import cache

# Load DB config from environment variables
DB_CONFIG = {
    "host": os.environ.get("MYSQL_HOST", "localhost"),
    "user": os.environ.get("MYSQL_USER", "root"),
    "passwd": os.environ.get("MYSQL_PASSWORD", ""),
    "db": os.environ.get("MYSQL_DB", "climate_data")
}

def create_db_and_tables():
    """
    Create the database and all required tables with indexes and constraints for data integrity.
    """
    db = MySQLdb.connect(host=DB_CONFIG["host"], user=DB_CONFIG["user"], passwd=DB_CONFIG["passwd"])
    cursor = db.cursor()
    # Create database if it doesn't exist
    cursor.execute("CREATE DATABASE IF NOT EXISTS climate_data;")
    cursor.execute("USE climate_data;")
    # Create locations table with NOT NULL constraints
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS locations (
            id INT PRIMARY KEY,
            name VARCHAR(255),
            country VARCHAR(255),
            latitude FLOAT,
            longitude FLOAT,
            region VARCHAR(255) NOT NULL,
            INDEX idx_region (region)
        );
    """)
    # Create metrics table with NOT NULL constraints
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS metrics (
            id INT PRIMARY KEY,
            name VARCHAR(255),
            display_name VARCHAR(255),
            unit VARCHAR(50),
            description TEXT NOT NULL,
            INDEX idx_name (name)
        );
    """)
    # Create climate_data table with NOT NULL, CHECK, and foreign key constraints
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS climate_data (
            id INT PRIMARY KEY,
            location_id INT NOT NULL,
            metric_id INT NOT NULL,
            date DATE NOT NULL,
            value FLOAT NOT NULL,
            quality VARCHAR(20) NOT NULL,
            FOREIGN KEY (location_id) REFERENCES locations(id),
            FOREIGN KEY (metric_id) REFERENCES metrics(id),
            CHECK (quality IN ('excellent', 'good', 'questionable', 'poor')),
            INDEX idx_location_id (location_id),
            INDEX idx_metric_id (metric_id),
            INDEX idx_date (date),
            INDEX idx_quality (quality)
        );
    """)
    db.commit()
    cursor.close()
    db.close()

def seed():
    """
    Seed the database tables with data from sample_data.json.
    Skips records with missing or invalid primary/foreign keys and logs warnings/errors.
    """
    try:
        with open('../data/sample_data.json') as f:
            data = json.load(f)
    except Exception as e:
        logger.error(f"Error loading JSON file: {e}")
        return

    db = MySQLdb.connect(**DB_CONFIG)
    cursor = db.cursor()

    # Seed locations table
    for loc in data.get('locations', []):
        id_val = loc.get('id')
        if not is_valid_id(id_val):
            logger.warning(f"Skipping location with invalid id (must be a positive integer): {loc}")
            continue
        if not loc.get('region'):
            logger.warning(f"Skipping location with missing region: {loc}")
            continue
        try:
            cursor.execute(
                "INSERT IGNORE INTO locations (id, name, country, latitude, longitude, region) VALUES (%s, %s, %s, %s, %s, %s)",
                (
                    int(id_val),
                    loc.get('name', None),
                    loc.get('country', None),
                    loc.get('latitude', None),
                    loc.get('longitude', None),
                    loc.get('region')
                )
            )
        except Exception as e:
            logger.error(f"Error inserting location {loc}: {e}")

    # Seed metrics table
    for met in data.get('metrics', []):
        id_val = met.get('id')
        if not is_valid_id(id_val):
            logger.warning(f"Skipping metric with invalid id (must be a positive integer): {met}")
            continue
        try:
            cursor.execute(
                "INSERT IGNORE INTO metrics (id, name, display_name, unit, description) VALUES (%s, %s, %s, %s, %s)",
                (
                    int(id_val),
                    met.get('name', None),
                    met.get('display_name', None),
                    met.get('unit', None),
                    met.get('description', None)
                )
            )
        except Exception as e:
            logger.error(f"Error inserting metric {met}: {e}")

    # Seed climate_data table
    for row in data.get('climate_data', []):
        id_val = row.get('id')
        location_id_val = row.get('location_id')
        metric_id_val = row.get('metric_id')
        # Validate all required IDs and fields
        if not is_valid_id(id_val):
            logger.warning(f"Skipping climate_data with invalid id (must be a positive integer): {row}")
            continue
        if not is_valid_id(location_id_val):
            logger.warning(f"Skipping climate_data with invalid location_id (must be a positive integer): {row}")
            continue
        if not is_valid_id(metric_id_val):
            logger.warning(f"Skipping climate_data with invalid metric_id (must be a positive integer): {row}")
            continue
        if not row.get('date'):
            logger.warning(f"Skipping climate_data with missing date: {row}")
            continue
        if row.get('value') is None:
            logger.warning(f"Skipping climate_data with missing value: {row}")
            continue
        if row.get('quality') not in QUALITY_VALUES:
            logger.warning(f"Skipping climate_data with invalid quality: {row}")
            continue
        try:
            cursor.execute(
                "INSERT IGNORE INTO climate_data (id, location_id, metric_id, date, value, quality) VALUES (%s, %s, %s, %s, %s, %s)",
                (
                    int(id_val),
                    int(location_id_val),
                    int(metric_id_val),
                    row.get('date'),
                    row.get('value'),
                    row.get('quality')
                )
            )
        except Exception as e:
            logger.error(f"Error inserting climate_data {row}: {e}")

    db.commit()
    cursor.close()
    db.close()
    logger.info("Database seeded successfully.")

if __name__ == "__main__":
    clear_forever_cache_keys(cache)
    create_db_and_tables()
    seed()