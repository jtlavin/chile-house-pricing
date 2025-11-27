# Web Scraping Mastery: Playwright & SQLite Study Guide

## 🎯 Learning Objectives

By the end of this study guide, you'll understand:
- How browser automation works with Playwright
- Advanced web scraping patterns and strategies
- SQLite database design and optimization
- Async programming patterns in Python
- Data validation and quality control
- Building production-ready scrapers

---

# Part 1: Playwright Fundamentals

## 🌐 What is Playwright?

Playwright is a browser automation library that controls real browsers (Chrome, Firefox, Safari) programmatically. Unlike simple HTTP requests, it can:
- Execute JavaScript
- Wait for dynamic content
- Handle complex interactions
- Take screenshots
- Manage cookies and sessions

### Core Concepts

#### 1. Browser → Context → Page Hierarchy
```python
async with async_playwright() as p:
    browser = await p.chromium.launch()     # 🖥️ Browser process
    context = await browser.new_context()  # 🔒 Isolated session (like incognito)
    page = await context.new_page()        # 📄 Individual tab/page
```

**Why this hierarchy?**
- **Browser**: Heavy to create, reuse when possible
- **Context**: Isolated cookies/localStorage, perfect for different "users"
- **Page**: Lightweight, create many for concurrent scraping

#### 2. Navigation and Waiting
```python
# Different wait strategies
await page.goto(url, wait_until='networkidle')  # Wait until no network activity
await page.goto(url, wait_until='domcontentloaded')  # DOM ready
await page.goto(url, wait_until='load')  # All resources loaded

# Wait for specific elements
await page.wait_for_selector('.price', timeout=10000)
await page.wait_for_selector('.loading', state='hidden')  # Wait for loading to disappear
```

#### 3. Element Selection Strategies
```python
# CSS Selectors (most common)
await page.query_selector('.price')           # First matching element
await page.query_selector_all('.item')       # All matching elements

# Playwright-specific selectors
await page.query_selector('text=Buy Now')    # By text content
await page.query_selector(':has-text("$")')  # Contains text
await page.query_selector('[data-testid="price"]')  # By attributes

# Robust fallback pattern from our scraper
selectors = ['.primary-price', '.price', '[class*="price"]']
for selector in selectors:
    element = await page.query_selector(selector)
    if element:
        price = await element.inner_text()
        break
```

### 🎯 **Challenge 1: Basic Playwright Setup**

Create a simple scraper that:
1. Opens Google
2. Searches for "web scraping"
3. Prints the first 3 result titles

```python
import asyncio
from playwright.async_api import async_playwright

async def google_scraper():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # See browser in action
        page = await browser.new_page()
        
        # Your code here
        # 1. Navigate to Google
        # 2. Find search box and type
        # 3. Submit search
        # 4. Extract results
        
        await browser.close()

# Run it
asyncio.run(google_scraper())
```

<details>
<summary>💡 Solution</summary>

```python
async def google_scraper():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # Navigate to Google
        await page.goto("https://www.google.com")
        
        # Find search box and search
        await page.fill('input[name="q"]', 'web scraping')
        await page.press('input[name="q"]', 'Enter')
        
        # Wait for results
        await page.wait_for_selector('h3')
        
        # Extract first 3 results
        results = await page.query_selector_all('h3')
        for i, result in enumerate(results[:3]):
            title = await result.inner_text()
            print(f"{i+1}. {title}")
        
        await browser.close()
```
</details>

### 🎯 **Challenge 2: Dynamic Content Handling**

Many modern websites load content with JavaScript. Practice with this example:

```python
async def dynamic_content_scraper():
    """
    Scrape a site that loads content dynamically
    Try: https://quotes.toscrape.com/js/
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        await page.goto("https://quotes.toscrape.com/js/")
        
        # Challenge: Extract all quotes and authors
        # Hint: The content loads via JavaScript, so you need to wait
        
        await browser.close()
```

<details>
<summary>💡 Solution</summary>

```python
async def dynamic_content_scraper():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        await page.goto("https://quotes.toscrape.com/js/")
        
        # Wait for quotes to load (they're added by JavaScript)
        await page.wait_for_selector('.quote')
        
        # Extract all quotes
        quotes = await page.query_selector_all('.quote')
        
        for quote in quotes:
            text = await quote.query_selector('.text')
            author = await quote.query_selector('.author')
            
            quote_text = await text.inner_text() if text else "No text"
            author_name = await author.inner_text() if author else "No author"
            
            print(f"{quote_text} — {author_name}")
        
        await browser.close()
```
</details>

---

# Part 2: Web Scraping Architecture

## 🏗️ Building Robust Scrapers

### 1. Configuration-Driven Design

From our Portal Inmobiliario scraper:
```python
@dataclass
class ScrapingConfig:
    min_delay_between_requests: float = 3.0
    max_delay_between_requests: float = 8.0
    max_requests_per_minute: int = 10
    avoid_peak_hours: bool = True
```

**Why use configuration classes?**
- ✅ Easy to modify behavior without changing code
- ✅ Type hints provide IDE support
- ✅ Default values for safety
- ✅ Easy testing with different configs

### 2. Data Models with Validation

```python
@dataclass
class PropertyData:
    title: str = ""
    price: str = ""
    bedrooms: Optional[int] = None
    scraped_at: str = ""
    
    def __post_init__(self):
        if not self.scraped_at:
            self.scraped_at = datetime.now().isoformat()
```

**Key concepts:**
- `Optional[int]` = can be `None` or `int`
- `__post_init__` = runs after object creation
- Type hints help catch bugs early

### 3. Rate Limiting Pattern

```python
class RateLimiter:
    def __init__(self, min_delay: float, max_delay: float):
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.last_request_time = 0
    
    async def wait_if_needed(self):
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        # Calculate random delay
        delay_needed = random.uniform(self.min_delay, self.max_delay)
        
        if time_since_last < delay_needed:
            sleep_time = delay_needed - time_since_last
            print(f"💤 Waiting {sleep_time:.1f}s to be respectful...")
            await asyncio.sleep(sleep_time)
        
        self.last_request_time = time.time()
```

### 🎯 **Challenge 3: Build a Rate-Limited Scraper**

Create a scraper that:
1. Uses a rate limiter
2. Scrapes multiple pages with delays
3. Has configurable limits

```python
import asyncio
import time
import random
from dataclasses import dataclass
from playwright.async_api import async_playwright

@dataclass
class Config:
    min_delay: float = 2.0
    max_delay: float = 5.0
    max_pages: int = 3

class RateLimiter:
    # Implement the rate limiter from above
    pass

async def multi_page_scraper():
    """
    Scrape quotes from multiple pages: https://quotes.toscrape.com/page/1/
    Use rate limiting between pages
    """
    config = Config()
    rate_limiter = RateLimiter(config.min_delay, config.max_delay)
    
    # Your implementation here
    pass
```

### 4. Robust Element Selection

Our scraper uses fallback patterns:
```python
async def extract_with_fallbacks(page, selectors_list, extraction_func):
    """Generic function to try multiple selectors"""
    for selector in selectors_list:
        try:
            element = await page.query_selector(selector)
            if element:
                return await extraction_func(element)
        except Exception:
            continue
    return None

# Usage
price_selectors = ['.primary-price', '.price', '[class*="price"]']
price = await extract_with_fallbacks(
    page, 
    price_selectors, 
    lambda elem: elem.inner_text()
)
```

### 🎯 **Challenge 4: Robust Data Extraction**

Build a function that extracts product information with multiple fallback strategies:

```python
async def extract_product_info(page):
    """
    Extract title, price, and rating with fallbacks
    Test on: https://books.toscrape.com/
    """
    
    # Title fallbacks
    title_selectors = ['h1', '.product_main h1', '[class*="title"]']
    
    # Price fallbacks  
    price_selectors = ['.price_color', '.price', '[class*="price"]']
    
    # Rating fallbacks
    rating_selectors = ['.star-rating', '[class*="star"]', '[class*="rating"]']
    
    # Your implementation:
    # 1. Try each selector list until you find data
    # 2. Return a dictionary with the extracted data
    # 3. Handle cases where data isn't found
    
    return {
        'title': title,
        'price': price,
        'rating': rating
    }
```

---

# Part 3: SQLite Database Integration

## 🗄️ Database Design Fundamentals

### 1. Schema Design

From our scraper's database schema:
```sql
CREATE TABLE IF NOT EXISTS properties (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    listing_id TEXT UNIQUE,                    -- Unique constraint prevents duplicates
    title TEXT,
    price TEXT,
    price_uf REAL,                            -- REAL for decimal numbers
    bedrooms INTEGER,
    latitude REAL,
    longitude REAL,
    amenities TEXT,                           -- JSON string for complex data
    scraped_at TEXT                           -- ISO timestamp as text
);

-- Indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_listing_id ON properties(listing_id);
CREATE INDEX IF NOT EXISTS idx_scraped_at ON properties(scraped_at);
```

**Key Design Decisions:**
- `listing_id TEXT UNIQUE`: Prevents duplicate properties
- `REAL` for numbers with decimals (price, coordinates)
- `TEXT` for JSON data (amenities list)
- Indexes on frequently queried columns

### 2. Python SQLite Patterns

```python
import sqlite3
import json

class PropertyDatabase:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Create tables and indexes"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS properties (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            listing_id TEXT UNIQUE,
            title TEXT,
            price_uf REAL,
            bedrooms INTEGER,
            amenities TEXT,
            scraped_at TEXT
        )
        ''')
        
        # Important: Create indexes for performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_listing_id ON properties(listing_id)')
        
        conn.commit()
        conn.close()
    
    def save_property(self, property_data):
        """Save property with duplicate handling"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Convert list to JSON string
            amenities_json = json.dumps(property_data.amenities)
            
            # INSERT OR REPLACE handles duplicates
            cursor.execute('''
            INSERT OR REPLACE INTO properties (
                listing_id, title, price_uf, bedrooms, amenities, scraped_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                property_data.listing_id,
                property_data.title,
                property_data.price_uf,
                property_data.bedrooms,
                amenities_json,
                property_data.scraped_at
            ))
            
            conn.commit()
        except sqlite3.Error as e:
            print(f"Database error: {e}")
        finally:
            conn.close()  # Always close connections!
```

### 3. Advanced Queries

```python
def get_statistics(self):
    """Get useful statistics from the database"""
    conn = sqlite3.connect(self.db_path)
    cursor = conn.cursor()
    
    # Count total properties
    cursor.execute("SELECT COUNT(*) FROM properties")
    total = cursor.fetchone()[0]
    
    # Average price by bedroom count
    cursor.execute('''
    SELECT bedrooms, AVG(price_uf), COUNT(*) 
    FROM properties 
    WHERE price_uf IS NOT NULL 
    GROUP BY bedrooms 
    ORDER BY bedrooms
    ''')
    price_by_bedrooms = cursor.fetchall()
    
    # Properties scraped in last 24 hours
    cursor.execute('''
    SELECT COUNT(*) FROM properties 
    WHERE scraped_at >= datetime('now', '-1 day')
    ''')
    recent_count = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        'total_properties': total,
        'price_by_bedrooms': price_by_bedrooms,
        'scraped_last_24h': recent_count
    }
```

### 🎯 **Challenge 5: Database Design**

Design a database for a book scraper:

```python
import sqlite3
import json
from dataclasses import dataclass
from typing import List

@dataclass
class Book:
    title: str
    author: str
    price: float
    rating: int  # 1-5 stars
    genres: List[str]
    isbn: str
    scraped_at: str

class BookDatabase:
    def __init__(self, db_path: str):
        self.db_path = db_path
        # Your task: implement this class
    
    def init_database(self):
        """
        Create a books table with:
        - Primary key
        - Unique constraint on ISBN
        - Proper data types
        - Indexes for common queries
        """
        pass
    
    def save_book(self, book: Book):
        """Save book, handle duplicates"""
        pass
    
    def get_books_by_rating(self, min_rating: int):
        """Get all books with rating >= min_rating"""
        pass
    
    def get_average_price_by_genre(self):
        """Get average price for each genre"""
        pass
```

### 🎯 **Challenge 6: Advanced SQL Queries**

Write SQL queries for common scraping scenarios:

```sql
-- 1. Find duplicate properties (same title, different listing_id)
-- Your query here

-- 2. Get properties with specific amenities (pool AND gym)
-- Your query here

-- 3. Find properties that haven't been updated in 30 days
-- Your query here

-- 4. Calculate price per square meter for all properties
-- Your query here

-- 5. Get the most expensive property in each neighborhood
-- Your query here
```

<details>
<summary>💡 Solutions</summary>

```sql
-- 1. Find duplicates
SELECT title, COUNT(*), GROUP_CONCAT(listing_id) 
FROM properties 
GROUP BY title 
HAVING COUNT(*) > 1;

-- 2. Properties with pool AND gym
SELECT title, amenities 
FROM properties 
WHERE amenities LIKE '%"pool"%' 
AND amenities LIKE '%"gym"%';

-- 3. Old properties
SELECT title, scraped_at 
FROM properties 
WHERE scraped_at < datetime('now', '-30 days');

-- 4. Price per square meter
SELECT title, price_uf, total_area, 
       (price_uf / total_area) as price_per_sqm
FROM properties 
WHERE price_uf IS NOT NULL AND total_area IS NOT NULL;

-- 5. Most expensive by neighborhood
SELECT neighborhood, title, price_uf
FROM properties p1
WHERE price_uf = (
    SELECT MAX(price_uf) 
    FROM properties p2 
    WHERE p2.neighborhood = p1.neighborhood
);
```
</details>

---

# Part 4: Advanced Concepts

## 🧮 Regular Expressions for Data Parsing

Regular expressions are crucial for extracting structured data from messy text.

### Common Patterns in Web Scraping

```python
import re

# Price extraction from our scraper
def extract_price_data(text):
    """Extract UF and CLP prices from text"""
    
    # UF pattern: "10,500 UF" or "10.500UF"
    uf_match = re.search(r'([\d,\.]+)\s*UF', text, re.IGNORECASE)
    if uf_match:
        # Clean and convert: "10,500" -> 10500
        uf_price = float(uf_match.group(1).replace(',', '').replace('.', ''))
        return {'price_uf': uf_price, 'currency': 'UF'}
    
    # CLP pattern: "$1,500,000" or "$ 1.500.000"
    clp_match = re.search(r'\$\s*([\d,\.]+)', text)
    if clp_match:
        clp_price = float(clp_match.group(1).replace(',', ''))
        return {'price_clp': clp_price, 'currency': 'CLP'}
    
    return None

# Property details extraction
def extract_property_features(text):
    """Extract bedrooms, bathrooms, area from text"""
    features = {}
    
    # Bedrooms: "3 dormitorios", "4 dorm", "2 bedrooms"
    bedroom_match = re.search(r'(\d+)\s*(?:dormitorio|bedroom|dorm)', text, re.IGNORECASE)
    if bedroom_match:
        features['bedrooms'] = int(bedroom_match.group(1))
    
    # Bathrooms: "2 baños", "3 bath"
    bathroom_match = re.search(r'(\d+)\s*(?:baño|bathroom|bath)', text, re.IGNORECASE)
    if bathroom_match:
        features['bathrooms'] = int(bathroom_match.group(1))
    
    # Area: "150 m2", "200 m²", "120m2"
    area_match = re.search(r'(\d+(?:[,\.]\d+)?)\s*m[²2]', text, re.IGNORECASE)
    if area_match:
        features['area'] = float(area_match.group(1).replace(',', '.'))
    
    return features
```

### 🎯 **Challenge 7: Regex Mastery**

Create regex patterns for these common scraping scenarios:

```python
import re

def extract_all_data(text_samples):
    """
    Extract data from these real-world text samples
    """
    
    samples = [
        "Departamento 3D/2B, 120m2, UF 8.500",
        "Precio: $125.000.000 CLP - 4 dormitorios, 3 baños",  
        "2 bed, 1 bath apartment - 65 square meters",
        "Publicado hace 15 días por Inmobiliaria XYZ",
        "Mantención: $85,000 mensuales",
        "Coordenadas: -33.4151, -70.6074"
    ]
    
    for sample in samples:
        print(f"Text: {sample}")
        
        # Your regex patterns here:
        # 1. Extract bedrooms/bathrooms
        # 2. Extract prices (UF and CLP)
        # 3. Extract area
        # 4. Extract days since posting
        # 5. Extract maintenance fees
        # 6. Extract coordinates
        
        print("---")
```

## 🔄 Async Programming Patterns

Understanding async/await is crucial for efficient scraping.

### Why Async?

```python
# ❌ Synchronous (slow)
def scrape_multiple_pages():
    for url in urls:
        page.goto(url)  # Wait for page to load
        data = extract_data(page)  # Wait for extraction
        save_to_db(data)  # Wait for database write
    # Total time: N pages × (load + extract + save) time

# ✅ Asynchronous (fast)
async def scrape_multiple_pages():
    tasks = []
    for url in urls:
        task = asyncio.create_task(scrape_single_page(url))
        tasks.append(task)
    
    results = await asyncio.gather(*tasks)  # Run concurrently
    # Total time: ≈ max(individual page times)
```

### Async Best Practices

```python
async def scrape_with_semaphore():
    """Limit concurrent requests to be respectful"""
    
    # Only allow 3 concurrent requests
    semaphore = asyncio.Semaphore(3)
    
    async def scrape_one_page(url):
        async with semaphore:  # Acquire semaphore
            async with async_playwright() as p:
                browser = await p.chromium.launch()
                page = await browser.new_page()
                
                await page.goto(url)
                data = await extract_data(page)
                
                await browser.close()
                return data
    
    # Create tasks for all URLs
    tasks = [scrape_one_page(url) for url in urls]
    
    # Wait for all to complete
    results = await asyncio.gather(*tasks)
    return results
```

## 📊 Data Validation Patterns

From our scraper's validation system:

```python
def validate_property_data(property_data):
    """Score data completeness and find issues"""
    score = 0
    max_score = 20
    issues = []
    
    # Core data (5 points each)
    if property_data.price and property_data.currency:
        score += 5
    else:
        issues.append("Missing price information")
    
    if property_data.bedrooms and property_data.bedrooms > 0:
        score += 5
    else:
        issues.append("Missing bedroom count")
    
    # Bonus points for additional data
    if property_data.latitude and property_data.longitude:
        # Validate coordinates are reasonable for Santiago
        if -33.7 <= property_data.latitude <= -33.2:
            score += 1
        else:
            issues.append("Invalid coordinates")
    
    completeness = (score / max_score) * 100
    
    return {
        'score': score,
        'completeness': completeness,
        'issues': issues,
        'is_valid': score >= 10  # At least 50% complete
    }
```

### 🎯 **Challenge 8: Data Validation System**

Build a validation system for book data:

```python
@dataclass
class Book:
    title: str = ""
    author: str = ""
    price: float = 0.0
    rating: int = 0
    isbn: str = ""
    page_count: int = 0
    publication_year: int = 0

def validate_book_data(book: Book):
    """
    Create a validation system that:
    1. Checks required fields are present
    2. Validates data ranges (rating 1-5, reasonable price, etc.)
    3. Validates ISBN format (can be 10 or 13 digits)
    4. Checks publication year is reasonable
    5. Returns a completeness score and issues list
    """
    
    # Your implementation here
    pass
```

---

# Part 5: Practical Integration Exercises

## 🏆 **Final Challenge: Mini E-commerce Scraper**

Build a complete scraper that combines all concepts:

```python
import asyncio
import sqlite3
import json
import re
from dataclasses import dataclass, asdict
from typing import List, Optional
from playwright.async_api import async_playwright

@dataclass
class ScrapingConfig:
    # Add configuration parameters
    pass

@dataclass  
class Product:
    # Define product structure
    pass

class ProductDatabase:
    # Implement database operations
    pass

class RateLimiter:
    # Implement rate limiting
    pass

class EcommerceScraper:
    def __init__(self, config: ScrapingConfig):
        self.config = config
        self.rate_limiter = RateLimiter(config.min_delay, config.max_delay)
        self.db = ProductDatabase(config.database_path)
        self.products = []
    
    async def scrape_product_list(self, url: str):
        """Scrape product listing page"""
        pass
    
    async def scrape_product_details(self, product_url: str):
        """Scrape individual product page"""
        pass
    
    async def extract_product_data(self, page, url: str):
        """Extract all product information"""
        pass
    
    def validate_product(self, product: Product):
        """Validate product data quality"""
        pass
    
    def save_results(self):
        """Save to database and JSON"""
        pass

# Test your scraper on: https://books.toscrape.com/
async def main():
    config = ScrapingConfig(
        min_delay=2.0,
        max_delay=4.0,
        max_products=10,
        database_path="books.db"
    )
    
    scraper = EcommerceScraper(config)
    await scraper.scrape_product_list("https://books.toscrape.com/")
    scraper.save_results()
```

## 🔍 **Debugging Common Issues**

### Issue 1: Elements Not Found
```python
# ❌ Fragile
element = await page.query_selector('.price')
price = await element.inner_text()  # Crashes if element is None

# ✅ Robust
element = await page.query_selector('.price')
if element:
    price = await element.inner_text()
else:
    price = "Price not found"
    print("Warning: Price element not found")
```

### Issue 2: Dynamic Content Not Loading
```python
# ❌ Too fast
await page.goto(url)
data = await extract_data(page)  # Data might not be loaded yet

# ✅ Wait properly
await page.goto(url)
await page.wait_for_selector('.content', timeout=10000)
# Or wait for loading indicator to disappear
await page.wait_for_selector('.loading', state='hidden')
data = await extract_data(page)
```

### Issue 3: Rate Limiting Detection
```python
async def handle_rate_limiting(page):
    """Detect and handle rate limiting"""
    
    # Check for common rate limiting indicators
    page_content = await page.content()
    
    rate_limit_indicators = [
        'too many requests',
        'rate limit',
        'please wait',
        'captcha',
        '429'
    ]
    
    for indicator in rate_limit_indicators:
        if indicator.lower() in page_content.lower():
            print(f"⚠️ Rate limiting detected: {indicator}")
            print("Increasing delay and retrying...")
            await asyncio.sleep(30)  # Wait 30 seconds
            return True
    
    return False
```

## 📚 **Further Learning Resources**

### Books
- "Web Scraping with Python" by Ryan Mitchell
- "Effective Python" by Brett Slatkin
- "Python Tricks" by Dan Bader

### Documentation
- [Playwright Python Docs](https://playwright.dev/python/)
- [SQLite Python Tutorial](https://docs.python.org/3/library/sqlite3.html)
- [Python Regex Guide](https://docs.python.org/3/library/re.html)

### Practice Sites
- [Quotes to Scrape](https://quotes.toscrape.com/) - Basic scraping
- [Books to Scrape](https://books.toscrape.com/) - E-commerce practice
- [Scrape This Site](https://scrapethissite.com/) - Various challenges

### Tools
- **Browser DevTools**: Essential for finding selectors
- **Regex101.com**: Test regex patterns
- **DB Browser for SQLite**: Visualize database contents
- **Postman**: Test API endpoints

---

## 🎯 **Self-Assessment Checklist**

After completing this guide, you should be able to:

- [ ] Set up Playwright and navigate pages
- [ ] Handle dynamic content and wait strategies  
- [ ] Build robust element selection with fallbacks
- [ ] Implement respectful rate limiting
- [ ] Design efficient database schemas
- [ ] Write complex SQL queries for data analysis
- [ ] Use regex for data extraction and cleaning
- [ ] Validate and clean scraped data
- [ ] Handle errors gracefully in production code
- [ ] Build a complete scraper from scratch

**Next Steps:**
1. Complete all coding challenges
2. Build your own scraper for a site you're interested in
3. Add monitoring and alerting to your scrapers
4. Learn about distributed scraping with multiple machines
5. Explore headless browser alternatives (Selenium, Requests-HTML)

Remember: **Always scrape responsibly!** Respect robots.txt, implement delays, and consider the impact on the websites you're scraping.