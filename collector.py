import asyncio
import logging
from playwright.async_api import async_playwright
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# List of areas/regions in Bahawalpur for search queries
BAHAWALPUR_AREAS = [
    "Model Town",
    "Satellite Town",
    "Dubai Chowk",
    "University Chowk",
    "Fareed Gate",
    "One Unit Chowk"
]

# Business types to search for
BUSINESS_TYPES = [
    {"type": "Clinic", "search": "clinic OR hospital OR doctor"},
    {"type": "Store", "search": "retail OR store OR shop OR supermarket"},
    {"type": "Service", "search": "service OR repair OR salon OR plumber"}
]

async def scrape_google_maps_leads(business_type, location):
    """
    Attempt to scrape Google Maps using Playwright.
    This is a simplified example. In reality, scraping Google Maps is complex,
    requires handling infinite scrolling, and is prone to blocking.
    """
    leads = []
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            search_query = f"{business_type['search']} in {location}, Bahawalpur"
            url = f"https://www.google.com/maps/search/{search_query.replace(' ', '+')}"

            logger.info(f"Navigating to: {url}")
            await page.goto(url, timeout=60000)
            await page.wait_for_timeout(5000) # Wait for results to load

            # This relies on Google Maps structure, which changes often.
            # We look for business listing elements.
            # If the scraper fails to find elements or times out, it will return what it has or fallback.
            elements = await page.query_selector_all('div.Nv254.txPEJf.QYnjxc.vY6njf.g1s6te')

            for el in elements[:5]: # Try to get up to 5 per query
                name_el = await el.query_selector('div.qBF1Pd.fontHeadlineSmall')
                name = await name_el.inner_text() if name_el else "Unknown Business"

                # If there is a website button, skip it
                website_el = await el.query_selector('a[data-value="Website"]')
                if website_el:
                    continue

                # Try to extract phone number (format varies)
                # This is a very rough heuristic
                phone = ""
                text_content = await el.inner_text()
                # Basic check for a Pakistani phone number format
                if "03" in text_content or "+92" in text_content:
                    # In a real scenario, use regex to properly extract phone numbers
                    import re
                    match = re.search(r'(\+92\s?\d{3}\s?\d{7}|03\d{2}\s?\d{7})', text_content)
                    if match:
                        phone = match.group(1)

                if phone:
                    leads.append({
                        "business_name": name,
                        "type": business_type["type"],
                        "city": "Bahawalpur",
                        "phone": phone
                    })

            await browser.close()
            return leads
    except Exception as e:
        logger.error(f"Scraping failed: {e}")
        return []

def generate_mock_leads():
    """Fallback mechanism to generate mock data if scraper fails or for testing."""
    mock_names = {
        "Clinic": ["Al-Shifa Clinic", "Bahawalpur Care Center", "City Health Clinic", "Family Medical Center"],
        "Store": ["Madina Mart", "Awami Super Store", "Punjab Traders", "BWP Electronics"],
        "Service": ["A-One Auto Repair", "Quick Fix Plumbing", "City Cleaners", "New Look Salon"]
    }

    business = random.choice(BUSINESS_TYPES)
    b_type = business["type"]
    name = random.choice(mock_names[b_type])
    area = random.choice(BAHAWALPUR_AREAS)

    # Generate a random Pakistani mobile number
    phone = f"+923{random.randint(0,4)}{random.randint(0,9)}{random.randint(1000000,9999999)}"

    return [{
        "business_name": f"{name} ({area})",
        "type": b_type,
        "city": "Bahawalpur",
        "phone": phone
    }]

def collect_leads_sync():
    """
    Synchronous wrapper to run the async scraping process.
    If scraping yields no results (which is likely without complex bypassing),
    it falls back to mock data to ensure the system keeps working.
    """
    logger.info("Starting lead collection process...")
    leads = []

    # Attempt real scraping (might fail or return empty due to anti-bot measures)
    # To prevent long delays in regular execution, we might just rely on mock data mostly,
    # but the prompt asks for a scraper with fallback.
    try:
        business = random.choice(BUSINESS_TYPES)
        location = random.choice(BAHAWALPUR_AREAS)
        scraped = asyncio.run(scrape_google_maps_leads(business, location))
        if scraped:
            logger.info(f"Successfully scraped {len(scraped)} leads.")
            leads.extend(scraped)
    except Exception as e:
        logger.error(f"Error running async scraper: {e}")

    if not leads:
        logger.info("Scraping returned no leads. Falling back to mock data.")
        leads = generate_mock_leads()

    return leads
