# Portal Inmobiliario Respectful Scraper - Usage Guide

## 🚀 Quick Start

### Basic Demo (Recommended First Step)
```bash
# Run the safe demo with only 3 properties
uv run main.py --demo
```

### Interactive Mode
```bash
# Run interactive mode with options
uv run main.py
```

## 📋 Usage Modes

### 1. Demo Mode (`--demo`)
**Safest option for testing**
- Scrapes only 3 properties
- 5-10 second delays between requests
- Very conservative rate limiting
- Perfect for testing and learning

### 2. Interactive Mode (default)
When you run `uv run main.py`, you'll get these options:

**Option 1: Basic Scraping**
- Extracts listing URLs and titles only
- Fast and lightweight
- Good for getting property links

**Option 2: Detailed Scraping**  
- Extracts comprehensive property data
- Visits individual property pages
- Respectful rate limiting (4-8 second delays)
- Limited to 10 properties by default

**Option 3: Combined Scraping**
- First collects all listing URLs
- Then extracts detailed data from each
- Most comprehensive but takes longer

## 🛠 Configuration Options

### ScrapingConfig Parameters

```python
config = ScrapingConfig(
    # Rate Limiting (be respectful!)
    min_delay_between_requests=4.0,    # Minimum seconds between requests
    max_delay_between_requests=8.0,    # Maximum seconds between requests  
    max_requests_per_minute=8,         # Requests per minute limit
    
    # Safety Limits
    max_listings_per_session=10,       # Max properties to process
    max_pages_per_session=2,           # Max search result pages
    
    # Time Restrictions
    avoid_peak_hours=True,             # Avoid 9 AM - 6 PM
    peak_start_hour=9,                 # Peak hours start
    peak_end_hour=18,                  # Peak hours end
    
    # Data Collection
    extract_coordinates=True,          # Get latitude/longitude
    save_images=False,                 # Save image URLs (disabled for privacy)
    validate_data=True,                # Clean and validate extracted data
    
    # Storage
    use_database=True,                 # Save to SQLite database
    batch_save_size=5,                 # Save every N properties
    database_path="properties.db"      # Database file name
)
```

### Recommended Settings by Use Case

#### **Learning/Testing (Safest)**
```python
ScrapingConfig(
    min_delay_between_requests=5.0,
    max_delay_between_requests=10.0,
    max_requests_per_minute=6,
    max_listings_per_session=5,
    max_pages_per_session=1
)
```

#### **Small Research Project** 
```python
ScrapingConfig(
    min_delay_between_requests=4.0,
    max_delay_between_requests=8.0,
    max_requests_per_minute=8,
    max_listings_per_session=50,
    max_pages_per_session=3
)
```

#### **Larger Data Collection (Use with Caution)**
```python
ScrapingConfig(
    min_delay_between_requests=3.0,
    max_delay_between_requests=6.0,
    max_requests_per_minute=10,
    max_listings_per_session=100,
    max_pages_per_session=5,
    avoid_peak_hours=True  # Important!
)
```

## 📊 Data Structure

### PropertyData Fields

The scraper extracts the following data for each property:

#### Core Information
- `listing_id`: Unique MercadoLibre ID
- `title`: Property title
- `url`: Link to property page
- `price`: Raw price string
- `price_uf`: Price in UF (Chilean accounting units)
- `price_clp`: Price in Chilean pesos
- `currency`: Currency type (UF/CLP)

#### Property Details  
- `bedrooms`: Number of bedrooms
- `bathrooms`: Number of bathrooms
- `total_area`: Total area in m²
- `built_area`: Built area in m²
- `parking_spots`: Number of parking spaces

#### Location
- `address`: Full address
- `neighborhood`: Neighborhood name
- `comuna`: Comuna (district)
- `latitude` / `longitude`: GPS coordinates

#### Building Features
- `building_age`: Age in years
- `total_floors`: Total floors in building
- `has_elevator`: Elevator availability
- `floor_number`: Property floor

#### Amenities
- `amenities`: List of amenities (pool, gym, security, etc.)
- `has_pool` / `has_gym` / `has_security`: Boolean flags

#### Metadata
- `listing_date`: When property was listed
- `days_on_market`: Days since listing
- `agent_info`: Real estate agent/agency
- `scraped_at`: When data was collected

## 💾 Data Storage

### SQLite Database
- **File**: `properties.db`
- **Table**: `properties`  
- **Features**: Automatic deduplication, spatial indexing, fast queries

### JSON Files
- **Batches**: `detailed_properties_batch_YYYYMMDD_HHMMSS.json`
- **Complete**: Use `scraper.save_all_detailed_results(filename)`

### Example Database Queries
```bash
# View all properties
sqlite3 properties.db "SELECT title, bedrooms, total_area, price FROM properties;"

# Average price by bedrooms
sqlite3 properties.db "SELECT bedrooms, AVG(price_uf) FROM properties WHERE price_uf IS NOT NULL GROUP BY bedrooms;"

# Properties with specific amenities
sqlite3 properties.db "SELECT title, amenities FROM properties WHERE amenities LIKE '%pool%';"
```

## 🔍 Data Quality & Validation

### Quality Scoring
Each property gets a completeness score (0-100%):
- **90-100%**: Excellent - All core data present
- **70-89%**: Good - Most data present
- **50-69%**: Fair - Core data present
- **Below 50%**: Poor - Missing critical information

### Data Cleaning
The scraper automatically:
- Normalizes price formats
- Validates area ranges (20-1000 m²)
- Checks coordinates are in Santiago area
- Standardizes amenity names
- Removes duplicate amenities

## ⚡ Performance & Respectful Usage

### Built-in Protections
1. **Rate Limiting**: Automatic delays between requests
2. **Peak Hour Avoidance**: Reduces load during business hours
3. **Error Handling**: Graceful failure handling
4. **Progress Saving**: Automatic incremental saves
5. **Connection Management**: Proper browser cleanup

### Monitoring
The scraper provides real-time feedback:
- ✅ Successful extractions
- ⚠️ Data quality warnings  
- ❌ Failed requests
- 📊 Progress updates
- 💤 Delay notifications
- 💾 Save confirmations

### Best Practices
1. **Start small**: Always test with demo mode first
2. **Monitor success rates**: Watch for high failure rates (>30%)
3. **Respect peak hours**: Avoid 9 AM - 6 PM Chilean time
4. **Check data quality**: Review completeness scores
5. **Save progress**: Use batch saving for large collections

## 🔧 Advanced Usage

### Custom Extraction
```python
# Create custom scraper with specific config
config = ScrapingConfig(
    min_delay_between_requests=6.0,
    max_listings_per_session=20,
    extract_coordinates=True,
    save_images=True  # Only if you need images
)

scraper = PortalInmobiliarioScraper(config=config)

# Run detailed scraping
results = await scraper.scrape_detailed_listings(
    url="https://www.portalinmobiliario.com/venta/departamento/las-condes-santiago-metropolitana",
    max_pages=3,
    max_listings=15
)

# Save and analyze
scraper.save_all_detailed_results("custom_results.json")
scraper.print_detailed_summary()
```

### Database Analysis
```python
# Get database statistics
stats = scraper.get_database_stats()
print(f"Total properties: {stats['total_properties']}")
print(f"Average price: {stats['average_price_uf']} UF")
print(f"Completeness rates: {stats['completeness_rate']}")
```

### Data Validation
```python
# Validate individual property
validation = scraper.validate_property_data(property)
print(f"Quality score: {validation['completeness_percentage']}%")
print(f"Issues: {validation['issues']}")
```

## 🛡️ Ethical Considerations

### Do's ✅
- Use reasonable delays (minimum 3-4 seconds)
- Limit concurrent requests (max 1)
- Avoid peak business hours when possible
- Monitor for blocking/errors and adapt
- Respect robots.txt when possible
- Use data for legitimate research/analysis

### Don'ts ❌ 
- Don't hammer the server with rapid requests
- Don't ignore error rates and continue aggressively
- Don't scrape during high-traffic periods unnecessarily
- Don't use data for harmful or commercial competitive purposes
- Don't redistribute or resell the scraped data

### Legal Notes
- This tool is for educational and research purposes
- Users are responsible for compliance with local laws
- Respect the website's terms of service
- Consider reaching out to Portal Inmobiliario for official API access for large-scale needs

## 🆘 Troubleshooting

### Common Issues

#### "High failure rate detected"
**Cause**: Too many requests failing (>30%)
**Solution**: 
- Increase delays in config
- Check if site structure changed
- Reduce max_requests_per_minute

#### "Peak hours" delays
**Cause**: Running during 9 AM - 6 PM
**Solution**:
- Run during off-peak hours
- Set `avoid_peak_hours=False` if needed

#### Missing data in results
**Cause**: Website structure changed
**Solution**:
- Check debug output for selector issues
- Update selectors in extraction methods
- Report issue with current working examples

#### Database locked errors
**Cause**: Multiple instances running
**Solution**:
- Ensure only one scraper instance runs at a time
- Close database connections properly

### Getting Help
1. Check the console output for specific error messages
2. Review the debug HTML files created
3. Start with demo mode to isolate issues
4. Reduce limits and increase delays if encountering blocks

## 📈 Building Your Housing Price Model

Once you have quality data, you can:

1. **Feature Engineering**: Create price per m², bedroom ratios, etc.
2. **Location Analysis**: Use coordinates for distance-based features
3. **Market Trends**: Track price changes over time
4. **Predictive Modeling**: Use XGBoost, neural networks, etc.
5. **Validation**: Compare predictions with actual listing prices

The structured data from this scraper provides an excellent foundation for machine learning models in real estate price prediction.