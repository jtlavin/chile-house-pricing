# Portal Inmobiliario Scraper - Technical Documentation

## Overview

This document provides a comprehensive explanation of the `main.py` scraper that extracts real estate listings from Portal Inmobiliario (Chile's largest real estate platform). The scraper is built using Playwright, a modern web automation library that can handle JavaScript-heavy Single Page Applications (SPAs).

## Table of Contents

1. [Core Concepts](#core-concepts)
2. [How Playwright Works](#how-playwright-works)
3. [Code Architecture](#code-architecture)
4. [Key Implementation Details](#key-implementation-details)
5. [What Makes This Scraper Work](#what-makes-this-scraper-work)
6. [Areas for Improvement](#areas-for-improvement)
7. [Next Steps: Individual Listing Data](#next-steps-individual-listing-data)
8. [Building a Housing Price Model](#building-a-housing-price-model)

## Core Concepts

### Web Scraping Challenges

Portal Inmobiliario is a **Single Page Application (SPA)** built with modern JavaScript frameworks. This presents several challenges:

- **Dynamic Content**: Property listings are loaded asynchronously via JavaScript
- **Anti-bot Protection**: The site may have measures to prevent automated access
- **Complex DOM Structure**: Modern CSS class names that may change frequently
- **Pagination**: Results are spread across multiple pages with dynamic URLs

### Why Playwright?

Unlike traditional scrapers using `requests` + `BeautifulSoup`, Playwright:
- **Executes JavaScript**: Can wait for dynamic content to load
- **Real Browser Engine**: Uses actual Chromium, Firefox, or WebKit
- **Anti-Detection**: Better at mimicking real user behavior
- **Modern Selectors**: Supports advanced CSS selectors and element waiting

## How Playwright Works

### Browser Automation Pipeline

```python
async with async_playwright() as p:
    browser = await p.chromium.launch(**browser_options)  # 1. Launch browser
    context = await browser.new_context(user_agent=...)   # 2. Create context
    page = await context.new_page()                       # 3. Create page
    await page.goto(url)                                  # 4. Navigate
    elements = await page.query_selector_all(selector)   # 5. Find elements
    data = await element.inner_text()                     # 6. Extract data
```

### Key Playwright Concepts

1. **Browser Context**: Isolated browsing session (like incognito mode)
2. **Page**: Individual tab/window within a context
3. **Element Handles**: References to DOM elements
4. **Selectors**: CSS/XPath expressions to find elements
5. **Wait Strategies**: Different ways to wait for content (`networkidle`, `domcontentloaded`, etc.)

## Code Architecture

### Class Structure

```python
class PortalInmobiliarioScraper:
    def __init__(self, proxy_list=None)           # Initialize with optional proxies
    async def scrape_listings(self, url, max_pages)  # Main scraping method
    async def extract_listings_from_page(self, page) # Extract data from current page  
    async def has_next_page(self, page)           # Check if more pages exist
    def save_results(self, filename)              # Save to JSON
    def print_summary(self)                       # Display results
```

### Data Flow

1. **Initialize** ’ Set up browser options and proxy rotation
2. **Navigate** ’ Go to search results page
3. **Wait** ’ Allow JavaScript content to load
4. **Extract** ’ Find listing elements and extract data
5. **Paginate** ’ Move to next page if available
6. **Repeat** ’ Continue until all pages scraped
7. **Save** ’ Export results to JSON file

## Key Implementation Details

### 1. Browser Configuration

```python
browser_options = {
    'headless': True,  # Run without GUI
    'args': [
        '--no-sandbox',  # Bypass OS security model
        '--disable-dev-shm-usage',  # Overcome limited resource problems
        '--disable-blink-features=AutomationControlled',  # Hide automation
        '--user-agent=Mozilla/5.0...'  # Realistic user agent
    ]
}
```

**Why this matters**: These options help the scraper appear more like a real browser and less like an automated tool.

### 2. Wait Strategies

```python
# Strategy 1: Wait for DOM to be ready
await page.goto(url, wait_until='domcontentloaded', timeout=60000)

# Strategy 2: Additional wait for JavaScript
await asyncio.sleep(8)  # Give SPA time to render

# Strategy 3: Wait for loading indicators to disappear
for indicator in loading_indicators:
    await page.wait_for_selector(indicator, state='hidden', timeout=5000)
```

**Why multiple strategies**: SPAs load in phases - initial HTML, then JavaScript execution, then API calls for data.

### 3. Robust Element Selection

```python
possible_selectors = [
    'a[href*="MLC"]',      # Most reliable - actual listing links
    '[class*="result"]',    # Generic result containers  
    '[class*="item"]',      # Item containers
    'article',             # Semantic HTML elements
    # ... fallback options
]
```

**Fallback Strategy**: If one selector fails, try others. This handles website changes gracefully.

### 4. Data Validation

```python
# Only accept meaningful titles
if title_text and len(title_text) > 10:
    listing_data['title'] = title_text

# Validate prices contain expected content  
if price_text and ('$' in price_text or 'UF' in price_text or any(char.isdigit() for char in price_text)):
    listing_data['price'] = price_text
```

**Quality Control**: Ensures extracted data is actually meaningful rather than empty or irrelevant text.

## What Makes This Scraper Work

### 1. **Adaptive Element Finding**
The scraper tries multiple strategies to find listings, making it resilient to website changes.

### 2. **Proper Wait Management**  
Instead of racing ahead, it waits for content to actually load before trying to extract data.

### 3. **Anti-Detection Measures**
- Realistic user agents
- Random delays between requests  
- Proper browser fingerprinting

### 4. **Error Handling**
Graceful degradation when elements aren't found, with detailed logging for debugging.

### 5. **Pagination Logic**
Automatically detects and navigates through multiple pages of results.

## Areas for Improvement

### 1. **Enhanced Anti-Detection**
```python
# Current approach
user_agent = random.choice(user_agents)

# Better approach  
- Rotate IP addresses via proxy pools
- Vary request timing patterns
- Implement session management
- Add browser fingerprint randomization
```

### 2. **Better Error Recovery**
```python
# Current: Basic try/catch
try:
    elements = await page.query_selector_all(selector)
except:
    continue

# Better: Specific error handling
try:
    elements = await page.query_selector_all(selector)
except TimeoutError:
    await page.reload()
    continue  
except ElementNotFoundError:
    try_alternative_selector()
```

### 3. **Data Validation & Cleaning**
```python
# Current: Basic text extraction
title = await element.inner_text()

# Better: Structured validation
title = clean_title_text(await element.inner_text())
price = parse_price_to_number(price_text)  
location = standardize_location(location_text)
```

### 4. **Performance Optimization**
- **Concurrent Processing**: Scrape multiple pages simultaneously
- **Intelligent Caching**: Store already-seen listings  
- **Incremental Updates**: Only scrape new listings since last run
- **Database Storage**: Direct database insertion instead of JSON files

### 5. **Configuration Management**
```python
# Current: Hardcoded values
max_pages = 5
wait_time = 8

# Better: Configuration file
config = load_config('scraper_config.yaml')
max_pages = config['pagination']['max_pages']
wait_time = config['timing']['page_load_wait']
```

## Next Steps: Individual Listing Data

Currently, we extract basic information from the search results page. To build a comprehensive housing price model, we need detailed data from individual property pages.

### Current Data Structure
```json
{
  "title": "Departamento En Venta San Carlos De Apoquindo",
  "detail_url": "https://www.portalinmobiliario.com/MLC-1234567-...",
  "selector_used": "a[href*=\"MLC\"]",
  "element_index": 0
}
```

### Enhanced Data Collection Strategy

#### Step 1: Visit Individual Listings
```python
async def scrape_individual_listing(self, listing_url):
    """Extract detailed information from individual property page"""
    await page.goto(listing_url)
    
    property_data = {
        # Basic Info
        'title': await self.extract_title(page),
        'price': await self.extract_price(page),
        'currency': await self.extract_currency(page),
        
        # Property Details  
        'bedrooms': await self.extract_bedrooms(page),
        'bathrooms': await self.extract_bathrooms(page), 
        'total_area': await self.extract_total_area(page),
        'built_area': await self.extract_built_area(page),
        'parking_spots': await self.extract_parking(page),
        
        # Location Data
        'address': await self.extract_address(page),
        'neighborhood': await self.extract_neighborhood(page),
        'comuna': await self.extract_comuna(page),
        'latitude': await self.extract_latitude(page),
        'longitude': await self.extract_longitude(page),
        
        # Property Features
        'property_type': await self.extract_property_type(page),
        'building_age': await self.extract_building_age(page),
        'floor_number': await self.extract_floor(page),
        'total_floors': await self.extract_total_floors(page),
        'orientation': await self.extract_orientation(page),
        
        # Amenities & Features
        'amenities': await self.extract_amenities(page),
        'has_elevator': await self.extract_elevator_info(page),
        'has_parking': await self.extract_parking_info(page),
        'has_storage': await self.extract_storage_info(page),
        
        # Financial Information
        'maintenance_fee': await self.extract_maintenance_fee(page),
        'property_tax': await self.extract_property_tax(page),
        
        # Media
        'image_urls': await self.extract_image_urls(page),
        'video_url': await self.extract_video_url(page),
        
        # Metadata
        'listing_date': await self.extract_listing_date(page),
        'listing_id': await self.extract_listing_id(page),
        'agent_info': await self.extract_agent_info(page)
    }
    
    return property_data
```

#### Step 2: Enhanced Main Scraper
```python
async def scrape_listings_detailed(self, url, max_pages=None):
    """Scrape both listing pages AND individual property details"""
    
    # Phase 1: Get all listing URLs (current implementation)
    listing_urls = await self.scrape_listing_urls(url, max_pages)
    
    # Phase 2: Visit each individual listing
    detailed_properties = []
    for i, listing_url in enumerate(listing_urls):
        print(f"Scraping detailed info {i+1}/{len(listing_urls)}: {listing_url}")
        
        try:
            property_data = await self.scrape_individual_listing(listing_url)
            detailed_properties.append(property_data)
            
            # Rate limiting - be respectful
            await asyncio.sleep(random.uniform(2, 5))
            
        except Exception as e:
            print(f"Error scraping {listing_url}: {e}")
            continue
    
    return detailed_properties
```

## Building a Housing Price Model

With detailed property data, you can build sophisticated pricing models:

### Feature Engineering

#### 1. **Location Features**
```python
# Distance to key landmarks
'distance_to_metro': calculate_distance_to_nearest_metro(lat, lon),
'distance_to_mall': calculate_distance_to_mall(lat, lon),
'distance_to_school': calculate_distance_to_school(lat, lon),

# Neighborhood characteristics
'neighborhood_avg_price': get_neighborhood_avg_price(neighborhood),
'neighborhood_crime_rate': get_crime_statistics(neighborhood),
'walkability_score': calculate_walkability(address)
```

#### 2. **Property Features**
```python  
# Size ratios
'price_per_m2': price / total_area,
'bedroom_to_bathroom_ratio': bedrooms / bathrooms,
'built_to_total_area_ratio': built_area / total_area,

# Quality indicators
'has_premium_amenities': len([a for a in amenities if a in PREMIUM_AMENITIES]),
'building_quality_score': calculate_building_quality_score(building_age, amenities),
'floor_desirability': calculate_floor_score(floor_number, total_floors)
```

#### 3. **Market Features**
```python
# Temporal features
'listing_season': extract_season(listing_date),
'days_on_market': calculate_days_on_market(listing_date),
'market_trend': get_market_trend(neighborhood, listing_date),

# Supply & demand
'neighborhood_inventory': count_similar_properties(neighborhood),
'price_vs_neighborhood_median': price / neighborhood_median_price
```

### Model Architecture Suggestions

#### 1. **Gradient Boosting Models**
```python
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor

# Handle mixed data types well
# Good for feature importance analysis
# Robust to outliers
```

#### 2. **Neural Networks**
```python
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Dense, Embedding, Concatenate

# Embedding layers for categorical features (neighborhood, property_type)
# Dense layers for numerical features  
# Can capture complex non-linear relationships
```

#### 3. **Ensemble Approach**
```python
# Combine multiple models
final_prediction = (
    0.4 * xgboost_prediction + 
    0.3 * neural_network_prediction +
    0.3 * linear_regression_prediction
)
```

### Data Pipeline Recommendations

#### 1. **Data Storage**
```python
# PostgreSQL with spatial extensions
CREATE TABLE properties (
    id SERIAL PRIMARY KEY,
    listing_id VARCHAR UNIQUE,
    price DECIMAL,
    location GEOGRAPHY(POINT, 4326),  -- Lat/lon with spatial indexing
    features JSONB,  -- Flexible feature storage
    scraped_at TIMESTAMP,
    INDEX(location) USING GIST,  -- Spatial queries
    INDEX(price, bedrooms, total_area)  -- Price analysis
);
```

#### 2. **Feature Store**
```python
# Precompute expensive features
CREATE TABLE feature_cache (
    property_id INTEGER,
    feature_name VARCHAR,
    feature_value FLOAT,
    computed_at TIMESTAMP
);
```

#### 3. **Model Training Pipeline**
```python
# Automated retraining
def retrain_model():
    # 1. Load new data since last training
    new_data = load_new_properties(since=last_training_date)
    
    # 2. Feature engineering
    features = engineer_features(new_data)
    
    # 3. Combine with existing data
    all_data = combine_datasets(existing_data, new_data)
    
    # 4. Train model
    model = train_model(all_data)
    
    # 5. Validate performance
    if validate_model(model) > current_model_performance:
        deploy_model(model)
```

### Success Metrics

#### 1. **Model Performance**
- **RMSE**: Root Mean Square Error in price predictions
- **MAPE**: Mean Absolute Percentage Error
- **R²**: Coefficient of determination

#### 2. **Business Metrics**
- **Coverage**: % of listings we can accurately price
- **Freshness**: How quickly we detect price changes
- **Accuracy by Segment**: Performance across different price ranges/neighborhoods

## Conclusion

This scraper provides a solid foundation for real estate data collection. The next phase involves:

1. **Enhancing data collection** to capture detailed property information
2. **Building robust data pipelines** for continuous data ingestion
3. **Developing sophisticated models** that capture market dynamics
4. **Creating monitoring systems** to ensure data quality and model performance

The combination of modern web scraping techniques with machine learning creates powerful opportunities for real estate market analysis and price prediction.