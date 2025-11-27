import asyncio
from ..scrapers import PortalInmobiliarioScraper, ScrapingConfig


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
