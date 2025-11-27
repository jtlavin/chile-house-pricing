import asyncio
import random
import time
from datetime import datetime
from .models import ScrapingConfig


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
