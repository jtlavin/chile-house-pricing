import asyncio
import json
import random
from playwright.async_api import async_playwright
import time
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import sqlite3
import os
from dataclasses import dataclass, asdict

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

class RateLimiter:
    """Manages respectful rate limiting"""
    def __init__(self, config: ScrapingConfig):
        self.config = config
        self.request_times = []
        self.last_request_time = 0
        
    async def wait_if_needed(self):
        """Wait if we need to respect rate limits"""
        current_time = time.time()
        
        # Check if we're in peak hours and should avoid scraping
        if self.config.avoid_peak_hours:
            current_hour = datetime.now().hour
            if self.config.peak_start_hour <= current_hour <= self.config.peak_end_hour:
                print("⏰ Avoiding peak hours (9 AM - 6 PM). Consider running during off-peak times.")
                await asyncio.sleep(60)  # Wait 1 minute during peak hours
        
        # Remove old request times (older than 1 minute)
        minute_ago = current_time - 60
        self.request_times = [t for t in self.request_times if t > minute_ago]
        
        # Check requests per minute limit
        if len(self.request_times) >= self.config.max_requests_per_minute:
            sleep_time = 60 - (current_time - self.request_times[0])
            if sleep_time > 0:
                print(f"⏳ Rate limit reached. Waiting {sleep_time:.1f}s...")
                await asyncio.sleep(sleep_time)
        
        # Ensure minimum delay between requests
        time_since_last = current_time - self.last_request_time
        min_delay = random.uniform(
            self.config.min_delay_between_requests,
            self.config.max_delay_between_requests
        )
        
        if time_since_last < min_delay:
            sleep_time = min_delay - time_since_last
            print(f"💤 Respectful delay: {sleep_time:.1f}s")
            await asyncio.sleep(sleep_time)
        
        # Record this request
        self.request_times.append(time.time())
        self.last_request_time = time.time()

class PortalInmobiliarioScraper:
    def __init__(self, proxy_list=None, config: Optional[ScrapingConfig] = None):
        """
        Initialize scraper with optional proxy list and configuration
        proxy_list format: [{'server': 'ip:port', 'username': 'user', 'password': 'pass'}, ...]
        """
        self.proxy_list = proxy_list or []
        self.config = config or ScrapingConfig()
        self.rate_limiter = RateLimiter(self.config)
        self.results = []
        self.detailed_properties = []
        
        # Initialize database if configured
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
    
    def save_property_to_db(self, property_data: PropertyData):
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
        
    async def scrape_listings(self, url, max_pages=None):
        """Scrape all listings from the given URL"""
        
        # Setup browser with proxy if available
        browser_options = {
            'headless': True,  # Set to True to avoid GUI issues
            'args': [
                '--no-sandbox', 
                '--disable-dev-shm-usage',
                '--disable-blink-features=AutomationControlled',
                '--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            ]
        }
        
        # Add proxy if available
        if self.proxy_list:
            proxy = random.choice(self.proxy_list)
            browser_options['proxy'] = proxy
            
        async with async_playwright() as p:
            try:
                browser = await p.chromium.launch(**browser_options)
            except Exception as e:
                print(f"Failed to launch browser: {e}")
                print("Please run: playwright install")
                return []
            
            # Create context with user agent rotation
            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
            ]
            
            context = await browser.new_context(
                user_agent=random.choice(user_agents),
                viewport={'width': 1920, 'height': 1080}
            )
            
            page = await context.new_page()
            
            try:
                current_page = 1
                
                while True:
                    print(f"Scraping page {current_page}...")
                    
                    # Navigate to page with longer timeout and different wait strategy
                    try:
                        if current_page == 1:
                            print(f"Navigating to: {url}")
                            await page.goto(url, wait_until='domcontentloaded', timeout=60000)
                        else:
                            # Navigate to specific page
                            page_url = f"{url}/_Desde_{(current_page-1)*48 + 1}"
                            print(f"Navigating to: {page_url}")
                            await page.goto(page_url, wait_until='domcontentloaded', timeout=60000)
                        
                        # Wait a bit for dynamic content to load
                        await asyncio.sleep(3)
                        
                    except Exception as e:
                        print(f"Navigation error: {e}")
                        print("Trying with different wait strategy...")
                        try:
                            if current_page == 1:
                                await page.goto(url, wait_until='load', timeout=30000)
                            else:
                                page_url = f"{url}/_Desde_{(current_page-1)*48 + 1}"
                                await page.goto(page_url, wait_until='load', timeout=30000)
                            await asyncio.sleep(5)
                        except Exception as e2:
                            print(f"Second navigation attempt failed: {e2}")
                            break
                    
                    # Debug: Save page content
                    if current_page == 1:
                        content = await page.content()
                        with open('debug_page.html', 'w', encoding='utf-8') as f:
                            f.write(content)
                        print("Page content saved to debug_page.html")
                    
                    # Wait longer for dynamic content to load and try different strategies
                    print("Waiting for page content to load...")
                    await asyncio.sleep(8)  # Give more time for SPA to load
                    
                    # Check if we hit a captcha or blocking page
                    page_title = await page.title()
                    page_url = page.url
                    print(f"Page title: {page_title}")
                    print(f"Current URL: {page_url}")
                    
                    # Look for any signs of content loading
                    loading_indicators = [
                        '.loader', '.loading', '.spinner', 
                        '[class*="loading"]', '[class*="spinner"]'
                    ]
                    
                    for indicator in loading_indicators:
                        try:
                            await page.wait_for_selector(indicator, state='hidden', timeout=5000)
                            print(f"✅ Loading indicator {indicator} disappeared")
                        except:
                            pass
                    
                    # Try to find any property/listing containers with broader selectors
                    modern_selectors = [
                        '[class*="result"]', 
                        '[class*="item"]',
                        '[class*="card"]',
                        '[class*="listing"]',
                        '[class*="property"]',
                        'article',
                        '[data-testid*="result"]',
                        '[data-testid*="item"]',
                        'div[class*="MLC"]',  # MercadoLibre listings often have MLC in class names
                        'a[href*="MLC"]'  # Links to individual properties
                    ]
                    
                    found_elements = False
                    for selector in modern_selectors:
                        try:
                            elements = await page.query_selector_all(selector)
                            if len(elements) > 5:  # Need reasonable number of elements
                                print(f"✅ Found {len(elements)} elements with selector: {selector}")
                                found_elements = True
                                break
                        except Exception as e:
                            continue
                    
                    if not found_elements:
                        print("❌ No listing elements found - checking if this is a blocking page")
                        
                        # Check for captcha or other blocking mechanisms
                        blocking_indicators = [
                            'captcha', 'blocked', 'security', 'challenge',
                            'robot', 'automation', 'bot'
                        ]
                        
                        page_content = await page.content()
                        lower_content = page_content.lower()
                        
                        for indicator in blocking_indicators:
                            if indicator in lower_content:
                                print(f"⚠️ Detected possible blocking: {indicator}")
                        
                        # Save more detailed debug info
                        with open('debug_full_content.html', 'w', encoding='utf-8') as f:
                            f.write(page_content)
                        print("Full page content saved to debug_full_content.html")
                        break
                    
                    # Extract listings from current page
                    listings = await self.extract_listings_from_page(page)
                    
                    if not listings:
                        print("No listings found on this page")
                        break
                        
                    self.results.extend(listings)
                    print(f"Found {len(listings)} listings on page {current_page}")
                    
                    # Check if we've reached max pages
                    if max_pages and current_page >= max_pages:
                        break
                    
                    # Check if there's a next page
                    has_next = await self.has_next_page(page)
                    if not has_next:
                        print("No more pages available")
                        break
                    
                    current_page += 1
                    
                    # Random delay between pages
                    await asyncio.sleep(random.uniform(2, 5))
                    
            except Exception as e:
                print(f"Error during scraping: {e}")
            finally:
                await browser.close()
                
        return self.results
    
    async def extract_listings_from_page(self, page):
        """Extract listing data from current page"""
        listings = []
        
        # Try multiple selectors to find listings - updated for modern SPA
        possible_selectors = [
            'a[href*="MLC"]',  # Links to individual properties (most reliable)
            '[class*="result"]', 
            '[class*="item"]',
            '[class*="card"]',
            '[class*="listing"]',
            'article',
            'div[class*="MLC"]',
            '[data-testid*="result"]',
            '[data-testid*="item"]',
            '.ui-search-result',
            '.ui-search-results__item', 
            '.ui-search-item'
        ]
        
        listing_elements = []
        used_selector = None
        
        for selector in possible_selectors:
            try:
                elements = await page.query_selector_all(selector)
                if elements:
                    listing_elements = elements
                    used_selector = selector
                    print(f"✅ Using selector: {selector} - Found {len(elements)} elements")
                    break
            except:
                continue
        
        if not listing_elements:
            print("❌ No listing elements found with any selector")
            # Let's see what elements are actually on the page
            all_elements = await page.query_selector_all('div[class*="result"], div[class*="listing"], div[class*="item"], div[class*="card"], div[class*="posting"]')
            print(f"Found {len(all_elements)} potential listing elements")
            if all_elements:
                for i, elem in enumerate(all_elements[:3]):  # Check first 3
                    class_name = await elem.get_attribute('class')
                    print(f"Element {i}: class='{class_name}'")
            return []
        
        print(f"Processing {len(listing_elements)} listings...")
        
        for i, element in enumerate(listing_elements):
            try:
                listing_data = {}
                
                # Debug: Let's see what's in this element
                element_text = await element.inner_text()
                element_html = await element.inner_html()
                if i < 3:  # Only debug first 3 elements
                    print(f"  DEBUG Element {i+1}:")
                    print(f"    Text: {element_text[:100]}")
                    print(f"    HTML: {element_html[:200]}")
                
                # More flexible title extraction - updated for modern site
                title_selectors = [
                    'a[href*="MLC"]',  # The link itself often contains the title
                    'h2', 'h3', 'h4',  # Common heading tags
                    '[class*="title"]',
                    '[data-testid*="title"]',
                    '.ui-search-item__title',
                    '.ui-search-item__title a',
                    'span', 'div',  # Fallback to any text content
                    '*'  # Last resort - any text in the element
                ]
                
                for selector in title_selectors:
                    title_element = await element.query_selector(selector)
                    if title_element:
                        title_text = (await title_element.inner_text()).strip()
                        if title_text and len(title_text) > 10:  # Must be substantial text
                            listing_data['title'] = title_text
                            break
                
                # If no title from specific selectors, use element's own text
                if not listing_data.get('title') and element_text:
                    if len(element_text.strip()) > 10:
                        listing_data['title'] = element_text.strip()
                
                # More flexible price extraction - updated for modern site
                price_selectors = [
                    '[class*="price"]',
                    '[class*="money"]',
                    '[class*="amount"]',
                    '[data-testid*="price"]',
                    '.andes-money-amount__fraction',
                    '.price-tag-fraction',
                    '.price',
                    'span',  # Check all spans for price content
                    'div'   # Check all divs for price content
                ]
                
                for selector in price_selectors:
                    price_element = await element.query_selector(selector)
                    if price_element:
                        price_text = (await price_element.inner_text()).strip()
                        # Check if this looks like a price (contains $ or numbers with UF/CLP)
                        if price_text and (
                            '$' in price_text or 
                            'UF' in price_text or 
                            'CLP' in price_text or
                            any(char.isdigit() for char in price_text)
                        ):
                            listing_data['price'] = price_text
                            break
                
                # Currency
                currency_selectors = [
                    '.andes-money-amount__currency-symbol',
                    '.currency',
                    'span[class*="currency"]'
                ]
                
                for selector in currency_selectors:
                    currency_element = await element.query_selector(selector)
                    if currency_element:
                        listing_data['currency'] = (await currency_element.inner_text()).strip()
                        break
                
                # Location
                location_selectors = [
                    '.ui-search-item__location',
                    '.location',
                    '[data-testid="location"]',
                    'span[class*="location"]'
                ]
                
                for selector in location_selectors:
                    location_element = await element.query_selector(selector)
                    if location_element:
                        listing_data['location'] = (await location_element.inner_text()).strip()
                        break
                
                # Link to detail page
                link_selectors = [
                    '.ui-search-item__group--title a',
                    'a[href*="MLC"]',
                    'a',
                    '[data-testid="item-link"]'
                ]
                
                for selector in link_selectors:
                    link_element = await element.query_selector(selector)
                    if link_element:
                        href = await link_element.get_attribute('href')
                        if href and ('MLC' in href or 'departamento' in href):
                            listing_data['detail_url'] = href
                            break
                
                # If the element itself is a link, get its href
                if not listing_data.get('detail_url'):
                    href = await element.get_attribute('href')
                    if href and 'MLC' in href:
                        listing_data['detail_url'] = href
                
                # Add debug info
                listing_data['selector_used'] = used_selector
                listing_data['element_index'] = i
                
                # If we found any data, add it
                if listing_data.get('title') or listing_data.get('price') or listing_data.get('detail_url'):
                    listings.append(listing_data)
                    print(f"  ✅ Extracted listing {i+1}: {listing_data.get('title', 'No title')[:50]}")
                else:
                    print(f"  ❌ No data found for element {i+1}")
                    
            except Exception as e:
                print(f"Error extracting listing {i}: {e}")
                continue
                
        return listings
    
    async def has_next_page(self, page):
        """Check if there's a next page available"""
        try:
            # Look for pagination or "next" button
            next_button = await page.query_selector('.andes-pagination__button--next:not([disabled])')
            return next_button is not None
        except:
            return False
    
    def save_results(self, filename='portal_inmobiliario_listings.json'):
        """Save results to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        print(f"Results saved to {filename}")
    
    async def scrape_detailed_listings(self, url, max_pages=None, max_listings=None):
        """Scrape listings and extract detailed data from individual pages"""
        print("🚀 Starting detailed listing scraping with respectful practices...")
        
        # First get all listing URLs using existing method
        print("📋 Phase 1: Getting listing URLs...")
        basic_listings = await self.scrape_listings(url, max_pages)
        
        if not basic_listings:
            print("❌ No listings found to process")
            return []
        
        # Limit the number of listings if specified
        if max_listings:
            basic_listings = basic_listings[:max_listings]
            print(f"📊 Limited to {len(basic_listings)} listings for respectful scraping")
        
        print(f"🔍 Phase 2: Extracting detailed data from {len(basic_listings)} individual listings...")
        
        # Process individual listings with respectful rate limiting
        detailed_properties = []
        failed_count = 0
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            page = await context.new_page()
            
            try:
                for i, listing in enumerate(basic_listings, 1):
                    detail_url = listing.get('detail_url', '')
                    if not detail_url:
                        print(f"⚠️  Listing {i}: No detail URL found")
                        failed_count += 1
                        continue
                    
                    # Clean up URL (remove tracking parameters)
                    clean_url = detail_url.split('#')[0].split('?')[0]
                    
                    print(f"🏠 Scraping {i}/{len(basic_listings)}: {listing.get('title', 'Unknown')[:50]}...")
                    
                    # Respectful rate limiting
                    await self.rate_limiter.wait_if_needed()
                    
                    try:
                        property_data = await self.scrape_individual_listing(page, clean_url, listing)
                        if property_data:
                            detailed_properties.append(property_data)
                            self.detailed_properties.append(property_data)
                            
                            # Save to database if configured
                            if self.config.use_database:
                                self.save_property_to_db(property_data)
                            
                            # Batch save to JSON
                            if len(detailed_properties) % self.config.batch_save_size == 0:
                                self.save_detailed_results_batch(detailed_properties[-self.config.batch_save_size:])
                                
                        else:
                            failed_count += 1
                            
                    except Exception as e:
                        print(f"❌ Error scraping listing {i}: {str(e)[:100]}")
                        failed_count += 1
                        
                        # If too many failures, might be blocked
                        if failed_count > len(basic_listings) * 0.3:  # More than 30% failure rate
                            print("⚠️  High failure rate detected. Possible blocking or site changes.")
                            break
                        
                        continue
                    
                    # Progress update
                    if i % 10 == 0:
                        success_rate = ((i - failed_count) / i) * 100
                        print(f"📊 Progress: {i}/{len(basic_listings)} ({success_rate:.1f}% success rate)")
            
            finally:
                await browser.close()
        
        # Save remaining results
        if detailed_properties:
            remaining = len(detailed_properties) % self.config.batch_save_size
            if remaining > 0:
                self.save_detailed_results_batch(detailed_properties[-remaining:])
        
        success_count = len(detailed_properties)
        print(f"\n✅ Detailed scraping completed!")
        print(f"📈 Successfully scraped: {success_count}/{len(basic_listings)} listings")
        print(f"⚠️  Failed: {failed_count} listings")
        print(f"💾 Saved to database: {self.config.database_path if self.config.use_database else 'Disabled'}")
        
        return detailed_properties
    
    async def scrape_individual_listing(self, page, url: str, basic_listing: Dict) -> Optional[PropertyData]:
        """Extract detailed information from individual property page"""
        try:
            # Navigate to property page
            await page.goto(url, wait_until='domcontentloaded', timeout=30000)
            await asyncio.sleep(2)  # Allow dynamic content to load
            
            # Extract listing ID from URL
            listing_id_match = re.search(r'MLC-(\d+)', url)
            listing_id = listing_id_match.group(1) if listing_id_match else ""
            
            # Initialize property data
            property_data = PropertyData(
                listing_id=listing_id,
                title=basic_listing.get('title', ''),
                url=url
            )
            
            # Extract financial data
            await self.extract_financial_data(page, property_data)
            
            # Extract property details
            await self.extract_property_details(page, property_data)
            
            # Extract location data
            await self.extract_location_data(page, property_data)
            
            # Extract building features
            await self.extract_building_features(page, property_data)
            
            # Extract amenities
            await self.extract_amenities_data(page, property_data)
            
            # Extract media URLs
            if self.config.save_images:
                await self.extract_media_data(page, property_data)
            
            # Extract metadata
            await self.extract_metadata(page, property_data)
            
            # Clean and validate data if configured
            if self.config.validate_data:
                property_data = self.clean_property_data(property_data)
                validation = self.validate_property_data(property_data)
                
                if not validation['is_valid']:
                    print(f"⚠️  Property {property_data.listing_id} has low data quality ({validation['completeness_percentage']:.1f}%)")
                    for issue in validation['issues']:
                        print(f"    - {issue}")
            
            return property_data
            
        except Exception as e:
            print(f"❌ Error extracting data from {url}: {str(e)[:100]}")
            return None
    
    async def extract_financial_data(self, page, property_data: PropertyData):
        """Extract price and financial information"""
        try:
            # Price selectors
            price_selectors = [
                '.andes-money-amount__fraction',
                '[class*="price"]',
                '.price-tag-fraction',
                'span:has-text("UF")',
                'span:has-text("$")'
            ]
            
            for selector in price_selectors:
                try:
                    price_element = await page.query_selector(selector)
                    if price_element:
                        price_text = await price_element.inner_text()
                        if price_text and ('UF' in price_text or '$' in price_text or any(c.isdigit() for c in price_text)):
                            property_data.price = price_text.strip()
                            
                            # Parse UF and CLP values
                            uf_match = re.search(r'([\d,\.]+)\s*UF', price_text)
                            if uf_match:
                                property_data.price_uf = float(uf_match.group(1).replace(',', '').replace('.', ''))
                                property_data.currency = 'UF'
                            
                            clp_match = re.search(r'\$\s*([\d,\.]+)', price_text)
                            if clp_match:
                                property_data.price_clp = float(clp_match.group(1).replace(',', ''))
                                if not property_data.currency:
                                    property_data.currency = 'CLP'
                            break
                except:
                    continue
            
            # Maintenance fee
            maintenance_selectors = [
                'text=Gastos comunes',
                '[class*="maintenance"]',
                ':has-text("gastos comunes")'
            ]
            
            for selector in maintenance_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        # Look for nearby price information
                        parent = await element.query_selector('xpath=..')
                        if parent:
                            text = await parent.inner_text()
                            maintenance_match = re.search(r'\$\s*([\d,\.]+)', text)
                            if maintenance_match:
                                property_data.maintenance_fee = maintenance_match.group(0)
                                break
                except:
                    continue
                    
        except Exception as e:
            print(f"⚠️  Error extracting financial data: {e}")
    
    async def extract_property_details(self, page, property_data: PropertyData):
        """Extract bedrooms, bathrooms, area, etc."""
        try:
            # Look for attribute containers
            attribute_selectors = [
                '.andes-table tbody tr',
                '[class*="attribute"]',
                '.ui-pdp-container .ui-pdp-attributes',
                '[class*="specs"] div',
                '.property-features li'
            ]
            
            for selector in attribute_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    for element in elements:
                        text = await element.inner_text()
                        text = text.lower()
                        
                        # Bedrooms
                        bedroom_match = re.search(r'(\d+)\s*(?:dormitorio|bedroom|dorm)', text)
                        if bedroom_match and not property_data.bedrooms:
                            property_data.bedrooms = int(bedroom_match.group(1))
                        
                        # Bathrooms  
                        bathroom_match = re.search(r'(\d+)\s*(?:baño|bathroom|bath)', text)
                        if bathroom_match and not property_data.bathrooms:
                            property_data.bathrooms = int(bathroom_match.group(1))
                        
                        # Total area
                        area_match = re.search(r'(\d+(?:[,\.]\d+)?)\s*m[²2]?\s*(?:total|const)', text)
                        if area_match and not property_data.total_area:
                            property_data.total_area = float(area_match.group(1).replace(',', '.'))
                        
                        # Built area
                        built_match = re.search(r'(\d+(?:[,\.]\d+)?)\s*m[²2]?\s*(?:útil|built)', text)
                        if built_match and not property_data.built_area:
                            property_data.built_area = float(built_match.group(1).replace(',', '.'))
                        
                        # Parking
                        parking_match = re.search(r'(\d+)\s*(?:estacionamiento|parking|garage)', text)
                        if parking_match and not property_data.parking_spots:
                            property_data.parking_spots = int(parking_match.group(1))
                        
                except:
                    continue
            
            # Try alternative selectors for specific attributes
            if not property_data.bedrooms:
                bedroom_elements = await page.query_selector_all('text=/\\d+ dorm/')
                if bedroom_elements:
                    for elem in bedroom_elements:
                        text = await elem.inner_text()
                        match = re.search(r'(\d+)', text)
                        if match:
                            property_data.bedrooms = int(match.group(1))
                            break
                            
        except Exception as e:
            print(f"⚠️  Error extracting property details: {e}")
    
    async def extract_location_data(self, page, property_data: PropertyData):
        """Extract address, neighborhood, coordinates"""
        try:
            # Address
            address_selectors = [
                '[class*="address"]',
                '[class*="location"]', 
                '.ui-pdp-color--BLACK:has-text("Las Condes")',
                'text=/.*Las Condes.*/'
            ]
            
            for selector in address_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        address = await element.inner_text()
                        if address and len(address) > 5:
                            property_data.address = address.strip()
                            
                            # Extract neighborhood and comuna
                            if 'Las Condes' in address:
                                property_data.comuna = 'Las Condes'
                            
                            # Extract neighborhood (usually first part)
                            parts = address.split(',')
                            if len(parts) > 1:
                                property_data.neighborhood = parts[0].strip()
                            break
                except:
                    continue
            
            # Coordinates (if available in map data)
            if self.config.extract_coordinates:
                try:
                    # Look for map or coordinate data
                    map_selectors = [
                        '[data-lat]',
                        '[data-longitude]',
                        'script:has-text("lat")',
                        '.map-container'
                    ]
                    
                    for selector in map_selectors:
                        try:
                            element = await page.query_selector(selector)
                            if element:
                                # Try to extract coordinates from attributes or script
                                lat_attr = await element.get_attribute('data-lat')
                                lng_attr = await element.get_attribute('data-lng') or await element.get_attribute('data-longitude')
                                
                                if lat_attr and lng_attr:
                                    property_data.latitude = float(lat_attr)
                                    property_data.longitude = float(lng_attr)
                                    break
                                
                                # Try from script content
                                if element.tag_name == 'SCRIPT':
                                    script_content = await element.inner_text()
                                    lat_match = re.search(r'lat["\']?\s*:\s*([+-]?\d+\.?\d*)', script_content)
                                    lng_match = re.search(r'(?:lng|lon)["\']?\s*:\s*([+-]?\d+\.?\d*)', script_content)
                                    
                                    if lat_match and lng_match:
                                        property_data.latitude = float(lat_match.group(1))
                                        property_data.longitude = float(lng_match.group(1))
                                        break
                        except:
                            continue
                except:
                    pass
                    
        except Exception as e:
            print(f"⚠️  Error extracting location data: {e}")
    
    async def extract_building_features(self, page, property_data: PropertyData):
        """Extract building age, floors, elevator info"""
        try:
            # Look for building information
            all_text = await page.inner_text('body')
            
            # Building age
            age_match = re.search(r'(\d{4})\s*(?:año|year)', all_text.lower())
            if age_match:
                year_built = int(age_match.group(1))
                current_year = datetime.now().year
                if year_built > 1900 and year_built <= current_year:
                    property_data.building_age = current_year - year_built
            
            # Floor information
            floor_match = re.search(r'piso\s*(\d+)|floor\s*(\d+)', all_text.lower())
            if floor_match:
                property_data.floor_number = int(floor_match.group(1) or floor_match.group(2))
            
            # Elevator
            if re.search(r'ascensor|elevator', all_text.lower()):
                property_data.has_elevator = True
            elif re.search(r'sin ascensor|no elevator', all_text.lower()):
                property_data.has_elevator = False
                
        except Exception as e:
            print(f"⚠️  Error extracting building features: {e}")
    
    async def extract_amenities_data(self, page, property_data: PropertyData):
        """Extract amenities and features"""
        try:
            all_text = await page.inner_text('body')
            lower_text = all_text.lower()
            
            amenities = []
            
            # Common amenities to check for
            amenity_keywords = {
                'piscina': 'pool',
                'gimnasio': 'gym', 
                'seguridad': 'security',
                'portero': 'doorman',
                'jardin': 'garden',
                'terraza': 'terrace',
                'balcon': 'balcony',
                'bodega': 'storage',
                'quincho': 'bbq area',
                'sala multiuso': 'multipurpose room',
                'salon de eventos': 'event room'
            }
            
            for spanish, english in amenity_keywords.items():
                if spanish in lower_text:
                    amenities.append(english)
                    
                    # Set specific boolean flags
                    if english == 'pool':
                        property_data.has_pool = True
                    elif english == 'gym':
                        property_data.has_gym = True
                    elif english in ['security', 'doorman']:
                        property_data.has_security = True
            
            property_data.amenities = amenities
            
        except Exception as e:
            print(f"⚠️  Error extracting amenities: {e}")
    
    async def extract_media_data(self, page, property_data: PropertyData):
        """Extract image and video URLs"""
        try:
            # Images
            image_selectors = [
                '.ui-pdp-gallery img',
                '[class*="gallery"] img',
                '.property-images img',
                'img[src*="http"]'
            ]
            
            image_urls = []
            for selector in image_selectors:
                try:
                    images = await page.query_selector_all(selector)
                    for img in images[:10]:  # Limit to first 10 images
                        src = await img.get_attribute('src')
                        if src and src.startswith('http') and src not in image_urls:
                            image_urls.append(src)
                    if image_urls:
                        break
                except:
                    continue
            
            property_data.image_urls = image_urls
            
            # Video (YouTube or other)
            video_selectors = [
                'iframe[src*="youtube"]',
                'iframe[src*="vimeo"]',
                'video source'
            ]
            
            for selector in video_selectors:
                try:
                    video = await page.query_selector(selector)
                    if video:
                        src = await video.get_attribute('src')
                        if src:
                            property_data.video_url = src
                            break
                except:
                    continue
                    
        except Exception as e:
            print(f"⚠️  Error extracting media data: {e}")
    
    async def extract_metadata(self, page, property_data: PropertyData):
        """Extract listing date, agent info, etc."""
        try:
            all_text = await page.inner_text('body')
            
            # Listing date
            date_patterns = [
                r'publicado hace (\d+) (?:día|day)s?',
                r'publicado hace (\d+) (?:mes|month)s?',
                r'publicado hace (\d+) (?:año|year)s?'
            ]
            
            for pattern in date_patterns:
                match = re.search(pattern, all_text.lower())
                if match:
                    property_data.listing_date = f"hace {match.group(1)} {pattern.split('(')[1].split(')')[0]}"
                    
                    # Calculate days on market
                    if 'día' in pattern or 'day' in pattern:
                        property_data.days_on_market = int(match.group(1))
                    elif 'mes' in pattern or 'month' in pattern:
                        property_data.days_on_market = int(match.group(1)) * 30
                    elif 'año' in pattern or 'year' in pattern:
                        property_data.days_on_market = int(match.group(1)) * 365
                    break
            
            # Agent/Agency info
            agent_selectors = [
                '[class*="seller"]',
                '[class*="agent"]',
                '.ui-box-component:has-text("Inmobiliaria")'
            ]
            
            for selector in agent_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        agent_text = await element.inner_text()
                        if agent_text and len(agent_text) < 200:
                            property_data.agent_info = agent_text.strip()
                            break
                except:
                    continue
                    
        except Exception as e:
            print(f"⚠️  Error extracting metadata: {e}")
    
    def save_detailed_results_batch(self, properties: List[PropertyData]):
        """Save batch of detailed results to JSON"""
        if not properties:
            return
            
        filename = f"detailed_properties_batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        properties_dict = [asdict(prop) for prop in properties]
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(properties_dict, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Saved batch of {len(properties)} properties to {filename}")
    
    def save_all_detailed_results(self, filename='detailed_properties_complete.json'):
        """Save all detailed results to a single JSON file"""
        if not self.detailed_properties:
            print("⚠️  No detailed properties to save")
            return
        
        properties_dict = [asdict(prop) for prop in self.detailed_properties]
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(properties_dict, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Saved {len(self.detailed_properties)} detailed properties to {filename}")
    
    def validate_property_data(self, property_data: PropertyData) -> dict:
        """Validate and score property data completeness"""
        validation_score = 0
        max_score = 20  # Total possible points
        issues = []
        
        # Core data validation (5 points each)
        if property_data.price and property_data.currency:
            validation_score += 5
        else:
            issues.append("Missing price information")
        
        if property_data.bedrooms and property_data.bedrooms > 0:
            validation_score += 5
        else:
            issues.append("Missing bedroom count")
            
        if property_data.total_area and property_data.total_area > 0:
            validation_score += 5
        else:
            issues.append("Missing area information")
            
        if property_data.address or property_data.neighborhood:
            validation_score += 5
        else:
            issues.append("Missing location information")
        
        # Additional data (bonus points)
        if property_data.bathrooms:
            validation_score += 1
        if property_data.parking_spots:
            validation_score += 1
        if property_data.latitude and property_data.longitude:
            validation_score += 1
        if property_data.amenities:
            validation_score += 1
        if property_data.agent_info:
            validation_score += 1
        
        completeness_percentage = (validation_score / max_score) * 100
        
        return {
            'score': validation_score,
            'max_score': max_score,
            'completeness_percentage': completeness_percentage,
            'issues': issues,
            'is_valid': validation_score >= 10  # At least 50% complete
        }
    
    def clean_property_data(self, property_data: PropertyData) -> PropertyData:
        """Clean and standardize property data"""
        # Clean price data
        if property_data.price:
            # Remove extra whitespace and normalize
            property_data.price = re.sub(r'\s+', ' ', property_data.price.strip())
        
        # Clean and validate area data
        if property_data.total_area:
            # Ensure reasonable area (between 20 and 1000 m2 for apartments)
            if property_data.total_area < 20 or property_data.total_area > 1000:
                print(f"⚠️  Unusual area detected: {property_data.total_area} m2")
        
        # Clean address
        if property_data.address:
            property_data.address = property_data.address.strip().title()
        
        # Clean neighborhood
        if property_data.neighborhood:
            property_data.neighborhood = property_data.neighborhood.strip().title()
        
        # Validate coordinates (Santiago area roughly)
        if property_data.latitude and property_data.longitude:
            # Santiago is roughly between -33.7 to -33.2 latitude, -71.0 to -70.3 longitude
            if not (-33.7 <= property_data.latitude <= -33.2 and -71.0 <= property_data.longitude <= -70.3):
                print(f"⚠️  Coordinates outside Santiago area: {property_data.latitude}, {property_data.longitude}")
        
        # Validate bedrooms and bathrooms
        if property_data.bedrooms and property_data.bedrooms > 10:
            print(f"⚠️  Unusual bedroom count: {property_data.bedrooms}")
        
        if property_data.bathrooms and property_data.bathrooms > 8:
            print(f"⚠️  Unusual bathroom count: {property_data.bathrooms}")
        
        # Clean amenities (remove duplicates, standardize)
        if property_data.amenities:
            property_data.amenities = list(set([amenity.strip().lower() for amenity in property_data.amenities if amenity.strip()]))
        
        return property_data
    
    def get_database_stats(self) -> dict:
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
    
    def print_detailed_summary(self):
        """Print comprehensive summary of detailed scraping results"""
        print(f"\n=== DETAILED SCRAPING SUMMARY ===")
        
        if not self.detailed_properties:
            print("No detailed properties scraped yet.")
            return
        
        total = len(self.detailed_properties)
        print(f"Total detailed properties scraped: {total}")
        
        # Validation statistics
        validation_scores = []
        valid_properties = 0
        
        for prop in self.detailed_properties:
            validation = self.validate_property_data(prop)
            validation_scores.append(validation['completeness_percentage'])
            if validation['is_valid']:
                valid_properties += 1
        
        avg_completeness = sum(validation_scores) / len(validation_scores)
        print(f"Average data completeness: {avg_completeness:.1f}%")
        print(f"Valid properties (>50% complete): {valid_properties}/{total} ({valid_properties/total*100:.1f}%)")
        
        # Property statistics
        prices = [p.price_uf for p in self.detailed_properties if p.price_uf and p.price_uf > 0]
        if prices:
            print(f"Price range (UF): {min(prices):,.0f} - {max(prices):,.0f}")
            print(f"Average price (UF): {sum(prices)/len(prices):,.0f}")
        
        areas = [p.total_area for p in self.detailed_properties if p.total_area and p.total_area > 0]
        if areas:
            print(f"Area range (m²): {min(areas):.0f} - {max(areas):.0f}")
            print(f"Average area (m²): {sum(areas)/len(areas):.0f}")
        
        bedrooms = [p.bedrooms for p in self.detailed_properties if p.bedrooms]
        if bedrooms:
            from collections import Counter
            bedroom_counts = Counter(bedrooms)
            print(f"Bedroom distribution: {dict(bedroom_counts)}")
        
        # Database statistics
        if self.config.use_database:
            db_stats = self.get_database_stats()
            if db_stats:
                print(f"\n=== DATABASE STATISTICS ===")
                print(f"Total properties in database: {db_stats['total_properties']}")
                print(f"Properties scraped in last 24h: {db_stats['scraped_last_24h']}")
                if db_stats['average_price_uf']:
                    print(f"Database average price (UF): {db_stats['average_price_uf']:,.0f}")
                if db_stats['average_area_m2']:
                    print(f"Database average area (m²): {db_stats['average_area_m2']:.0f}")
        
        print(f"\n💾 Data saved to:")
        if self.config.use_database:
            print(f"  - Database: {self.config.database_path}")
        print(f"  - JSON batches: detailed_properties_batch_*.json")
        print(f"  - Complete file: Use save_all_detailed_results() method")
    
    def print_summary(self):
        """Print summary of scraped data"""
        print(f"\n=== SCRAPING SUMMARY ===")
        print(f"Total listings found: {len(self.results)}")
        
        if self.results:
            print(f"\nSample listing:")
            sample = self.results[0]
            for key, value in sample.items():
                print(f"  {key}: {value}")

async def main():
    """
    Demonstrates both basic and detailed scraping with respectful practices
    """
    print("🏠 Portal Inmobiliario Respectful Scraper")
    print("=" * 50)
    
    # Configuration for respectful scraping
    config = ScrapingConfig(
        # Rate limiting - be very respectful
        min_delay_between_requests=4.0,  # Minimum 4 seconds between requests
        max_delay_between_requests=8.0,  # Maximum 8 seconds
        max_requests_per_minute=8,       # Only 8 requests per minute
        
        # Limits for testing - keep small for safety
        max_listings_per_session=10,     # Only process 10 listings for testing
        max_pages_per_session=2,         # Only 2 pages for testing
        
        # Time restrictions
        avoid_peak_hours=True,           # Avoid 9 AM - 6 PM
        
        # Data settings
        extract_coordinates=True,        # Get latitude/longitude if available
        save_images=False,               # Don't save images in testing
        use_database=True,               # Use SQLite database
        batch_save_size=5                # Save every 5 properties
    )
    
    # URL to scrape
    url = "https://www.portalinmobiliario.com/venta/departamento/san-carlos-de-apoquindo-las-condes-santiago-metropolitana"
    
    # Initialize scraper with configuration
    print("🔧 Initializing scraper with respectful configuration...")
    scraper = PortalInmobiliarioScraper(config=config)
    
    # Ask user what type of scraping to perform
    print("\n📋 Choose scraping mode:")
    print("1. Basic scraping (listing URLs and titles only)")
    print("2. Detailed scraping (full property data from individual pages)")
    print("3. Both (basic first, then detailed)")
    
    choice = input("Enter your choice (1-3): ").strip()
    
    if choice == "1":
        print("\n🚀 Starting BASIC scraping...")
        results = await scraper.scrape_listings(url, max_pages=config.max_pages_per_session)
        scraper.save_results()
        scraper.print_summary()
        print(f"\n✅ Basic scraping completed! Found {len(results)} listings.")
        
    elif choice == "2":
        print("\n🚀 Starting DETAILED scraping...")
        detailed_results = await scraper.scrape_detailed_listings(
            url, 
            max_pages=config.max_pages_per_session,
            max_listings=config.max_listings_per_session
        )
        scraper.save_all_detailed_results()
        scraper.print_detailed_summary()
        print(f"\n✅ Detailed scraping completed! Processed {len(detailed_results)} properties.")
        
    elif choice == "3":
        print("\n🚀 Starting COMBINED scraping (basic + detailed)...")
        
        # Phase 1: Basic scraping
        print("📋 Phase 1: Basic listing collection...")
        basic_results = await scraper.scrape_listings(url, max_pages=config.max_pages_per_session)
        scraper.save_results("basic_listings.json")
        
        if basic_results:
            print(f"✅ Found {len(basic_results)} basic listings")
            
            # Phase 2: Detailed scraping (limited for safety)
            print("\n🔍 Phase 2: Detailed property extraction...")
            detailed_results = await scraper.scrape_detailed_listings(
                url, 
                max_pages=config.max_pages_per_session,
                max_listings=min(config.max_listings_per_session, len(basic_results))
            )
            
            scraper.save_all_detailed_results("complete_property_data.json")
            scraper.print_detailed_summary()
            print(f"\n✅ Complete scraping finished!")
            print(f"📊 Basic listings: {len(basic_results)}")
            print(f"📊 Detailed properties: {len(detailed_results)}")
        else:
            print("❌ No basic listings found, skipping detailed scraping.")
    
    else:
        print("❌ Invalid choice. Running basic scraping as default.")
        results = await scraper.scrape_listings(url, max_pages=2)
        scraper.save_results()
        scraper.print_summary()

async def demo_detailed_scraping():
    """
    Demo function specifically for detailed scraping with minimal impact
    """
    print("🏠 DEMO: Detailed Property Scraping")
    print("=" * 40)
    print("⚠️  This demo will scrape only 3 properties to demonstrate the functionality")
    
    # Very conservative configuration for demo
    demo_config = ScrapingConfig(
        min_delay_between_requests=5.0,  # 5-10 seconds between requests
        max_delay_between_requests=10.0,
        max_requests_per_minute=6,       # Very conservative
        max_listings_per_session=3,      # Only 3 properties
        max_pages_per_session=1,         # Only 1 page
        avoid_peak_hours=True,
        use_database=True,
        extract_coordinates=True,
        save_images=False
    )
    
    url = "https://www.portalinmobiliario.com/venta/departamento/san-carlos-de-apoquindo-las-condes-santiago-metropolitana"
    
    scraper = PortalInmobiliarioScraper(config=demo_config)
    
    print("🚀 Starting respectful detailed scraping demo...")
    detailed_properties = await scraper.scrape_detailed_listings(url, max_pages=1, max_listings=3)
    
    if detailed_properties:
        print(f"\n✅ Demo completed! Successfully scraped {len(detailed_properties)} properties.")
        
        # Show sample property data
        print(f"\n📋 Sample Property Data:")
        sample = detailed_properties[0]
        print(f"  Title: {sample.title}")
        print(f"  Price: {sample.price}")
        print(f"  Bedrooms: {sample.bedrooms}")
        print(f"  Area: {sample.total_area} m²")
        print(f"  Location: {sample.address}")
        print(f"  Amenities: {', '.join(sample.amenities) if sample.amenities else 'None listed'}")
        
        # Validation
        validation = scraper.validate_property_data(sample)
        print(f"  Data completeness: {validation['completeness_percentage']:.1f}%")
        
        scraper.save_all_detailed_results("demo_detailed_properties.json")
        scraper.print_detailed_summary()
    else:
        print("❌ Demo failed - no properties were scraped")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        # Run minimal demo
        asyncio.run(demo_detailed_scraping())
    else:
        # Run full interactive version
        asyncio.run(main())