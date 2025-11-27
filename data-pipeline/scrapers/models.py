from dataclasses import dataclass, asdict
from typing import List, Optional
from datetime import datetime


@dataclass
class ScrapingConfig:
    """Configuration for respectful web scraping"""
    # Rate limiting
    min_delay_between_requests: float = 3.0
    max_delay_between_requests: float = 8.0
    max_requests_per_minute: int = 10
    max_concurrent_requests: int = 1

    # Respectful limits
    max_listings_per_session: int = 100
    max_pages_per_session: int = 10
    max_retries_per_listing: int = 3

    # Time restrictions (avoid peak hours)
    avoid_peak_hours: bool = True
    peak_start_hour: int = 9  # 9 AM
    peak_end_hour: int = 18   # 6 PM

    # Data extraction
    save_images: bool = False
    extract_coordinates: bool = True
    validate_data: bool = True

    # Storage
    batch_save_size: int = 50
    use_database: bool = True
    database_path: str = "properties.db"


@dataclass
class PropertyData:
    """Structure for individual property data"""
    # Basic info
    listing_id: str = ""
    title: str = ""
    url: str = ""

    # Financial
    price: str = ""
    price_uf: Optional[float] = None
    price_clp: Optional[float] = None
    currency: str = ""
    maintenance_fee: str = ""

    # Property details
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    total_area: Optional[float] = None
    built_area: Optional[float] = None
    parking_spots: Optional[int] = None

    # Location
    address: str = ""
    neighborhood: str = ""
    comuna: str = ""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    floor_number: Optional[int] = None

    # Building features
    building_age: Optional[int] = None
    total_floors: Optional[int] = None
    has_elevator: Optional[bool] = None
    orientation: str = ""

    # Amenities
    amenities: List[str] = None
    has_pool: Optional[bool] = None
    has_gym: Optional[bool] = None
    has_security: Optional[bool] = None

    # Media
    image_urls: List[str] = None
    video_url: str = ""

    # Metadata
    listing_date: str = ""
    days_on_market: Optional[int] = None
    agent_info: str = ""
    scraped_at: str = ""

    def __post_init__(self):
        if self.amenities is None:
            self.amenities = []
        if self.image_urls is None:
            self.image_urls = []
        if not self.scraped_at:
            self.scraped_at = datetime.now().isoformat()
