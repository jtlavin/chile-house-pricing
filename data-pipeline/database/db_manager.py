import sqlite3
import json
import os
from typing import Optional
from ..scrapers.models import PropertyData, ScrapingConfig


class DatabaseManager:
    """Manages SQLite database operations for property storage"""

    def __init__(self, config: ScrapingConfig):
        self.config = config
        if self.config.use_database:
            self.init_database()

    def init_database(self):
        """Initialize SQLite database for property storage"""
        conn = sqlite3.connect(self.config.database_path)
        cursor = conn.cursor()

        # Create properties table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS properties (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            listing_id TEXT UNIQUE,
            title TEXT,
            url TEXT,
            price TEXT,
            price_uf REAL,
            price_clp REAL,
            currency TEXT,
            maintenance_fee TEXT,
            bedrooms INTEGER,
            bathrooms INTEGER,
            total_area REAL,
            built_area REAL,
            parking_spots INTEGER,
            address TEXT,
            neighborhood TEXT,
            comuna TEXT,
            latitude REAL,
            longitude REAL,
            floor_number INTEGER,
            building_age INTEGER,
            total_floors INTEGER,
            has_elevator BOOLEAN,
            orientation TEXT,
            amenities TEXT,
            has_pool BOOLEAN,
            has_gym BOOLEAN,
            has_security BOOLEAN,
            image_urls TEXT,
            video_url TEXT,
            listing_date TEXT,
            days_on_market INTEGER,
            agent_info TEXT,
            scraped_at TEXT
        )
        ''')

        # Create index on listing_id for faster lookups
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_listing_id ON properties(listing_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_scraped_at ON properties(scraped_at)')

        conn.commit()
        conn.close()
        print(f"✅ Database initialized at {self.config.database_path}")

    def save_property(self, property_data: PropertyData):
        """Save a property to the database"""
        if not self.config.use_database:
            return

        conn = sqlite3.connect(self.config.database_path)
        cursor = conn.cursor()

        # Convert lists to JSON strings
        amenities_json = json.dumps(property_data.amenities) if property_data.amenities else "[]"
        images_json = json.dumps(property_data.image_urls) if property_data.image_urls else "[]"

        try:
            cursor.execute('''
            INSERT OR REPLACE INTO properties (
                listing_id, title, url, price, price_uf, price_clp, currency, maintenance_fee,
                bedrooms, bathrooms, total_area, built_area, parking_spots,
                address, neighborhood, comuna, latitude, longitude, floor_number,
                building_age, total_floors, has_elevator, orientation,
                amenities, has_pool, has_gym, has_security,
                image_urls, video_url, listing_date, days_on_market, agent_info, scraped_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                property_data.listing_id, property_data.title, property_data.url,
                property_data.price, property_data.price_uf, property_data.price_clp,
                property_data.currency, property_data.maintenance_fee,
                property_data.bedrooms, property_data.bathrooms, property_data.total_area,
                property_data.built_area, property_data.parking_spots,
                property_data.address, property_data.neighborhood, property_data.comuna,
                property_data.latitude, property_data.longitude, property_data.floor_number,
                property_data.building_age, property_data.total_floors, property_data.has_elevator,
                property_data.orientation, amenities_json, property_data.has_pool,
                property_data.has_gym, property_data.has_security,
                images_json, property_data.video_url, property_data.listing_date,
                property_data.days_on_market, property_data.agent_info, property_data.scraped_at
            ))
            conn.commit()
        except sqlite3.Error as e:
            print(f"❌ Database error: {e}")
        finally:
            conn.close()

    def get_stats(self) -> dict:
        """Get statistics from the database"""
        if not self.config.use_database or not os.path.exists(self.config.database_path):
            return {}

        conn = sqlite3.connect(self.config.database_path)
        cursor = conn.cursor()

        try:
            # Basic counts
            cursor.execute("SELECT COUNT(*) FROM properties")
            total_properties = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM properties WHERE price_uf IS NOT NULL")
            properties_with_price = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM properties WHERE bedrooms IS NOT NULL")
            properties_with_bedrooms = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM properties WHERE total_area IS NOT NULL")
            properties_with_area = cursor.fetchone()[0]

            # Average values
            cursor.execute("SELECT AVG(price_uf) FROM properties WHERE price_uf IS NOT NULL AND price_uf > 0")
            avg_price_uf = cursor.fetchone()[0]

            cursor.execute("SELECT AVG(total_area) FROM properties WHERE total_area IS NOT NULL AND total_area > 0")
            avg_area = cursor.fetchone()[0]

            # Recent scraping activity
            cursor.execute("SELECT COUNT(*) FROM properties WHERE scraped_at >= datetime('now', '-1 day')")
            scraped_last_24h = cursor.fetchone()[0]

            stats = {
                'total_properties': total_properties,
                'properties_with_price': properties_with_price,
                'properties_with_bedrooms': properties_with_bedrooms,
                'properties_with_area': properties_with_area,
                'average_price_uf': round(avg_price_uf, 2) if avg_price_uf else None,
                'average_area_m2': round(avg_area, 2) if avg_area else None,
                'scraped_last_24h': scraped_last_24h,
                'completeness_rate': {
                    'price': (properties_with_price / total_properties * 100) if total_properties else 0,
                    'bedrooms': (properties_with_bedrooms / total_properties * 100) if total_properties else 0,
                    'area': (properties_with_area / total_properties * 100) if total_properties else 0
                }
            }

            return stats

        except sqlite3.Error as e:
            print(f"❌ Database error getting stats: {e}")
            return {}
        finally:
            conn.close()
