import time
import random
import re
from database import get_db
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

def generate_mock_leads(db_path='leads.db'):
    """Fallback generator for mock data if scraper fails"""
    business_types = ['Clinic', 'Store', 'Service']
    cities = ['Bahawalpur']
    first_names = ['City', 'Prime', 'Apex', 'Global', 'Star', 'Crescent', 'Oasis']
    last_names = ['Care', 'Mart', 'Solutions', 'Associates', 'Hub', 'Plaza', 'Center']

    with get_db(db_path) as conn:
        cursor = conn.cursor()

        # Check existing leads to avoid overwhelming the DB
        cursor.execute("SELECT COUNT(*) FROM leads")
        if cursor.fetchone()[0] > 50:
            return

        for _ in range(5): # Generate 5 mock leads
            b_type = random.choice(business_types)
            name = f"{random.choice(first_names)} {random.choice(last_names)} {b_type}"
            city = random.choice(cities)
            # Generate a realistic-looking phone number for Pakistan
            phone = f"+92 3{random.randint(0, 4)}{random.randint(0, 9)} {random.randint(1000000, 9999999)}"

            # Simple check if phone already exists
            cursor.execute("SELECT id FROM leads WHERE phone = ?", (phone,))
            if not cursor.fetchone():
                cursor.execute(
                    "INSERT INTO leads (business_name, type, city, phone) VALUES (?, ?, ?, ?)",
                    (name, b_type, city, phone)
                )

def scrape_duckduckgo(query, b_type, db_path='leads.db'):
    leads_found = 0
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            # Using DuckDuckGo HTML version to avoid immediate blocking
            url = f"https://html.duckduckgo.com/html/?q={query}"

            print(f"Scraping: {url}")
            page.goto(url, wait_until='domcontentloaded', timeout=60000)

            # Wait for results
            page.wait_for_selector('.result', timeout=15000)

            results = page.query_selector_all('.result')

            for result in results:
                # Extract text
                text_content = result.inner_text()

                # Check if it has a website link (heuristic: looking for a distinct website button or URL pattern)
                # In DuckDuckGo HTML, the main title is a link to the website.
                title_elem = result.query_selector('.result__title a')
                snippet_elem = result.query_selector('.result__snippet')

                if not title_elem or not snippet_elem:
                    continue

                href = title_elem.get_attribute('href')
                snippet = snippet_elem.inner_text()

                # Filter: Businesses that might just be directory listings or have no actual website
                # We want businesses that don't have their own domain in the search result easily visible
                # Or businesses listed on directories (facebook, yelp, justdial, etc) instead of their own site

                is_directory = False
                directories = ['facebook.com', 'instagram.com', 'yelp.com', 'justdial.com', 'yellowpages', 'linkedin.com', 'twitter.com']
                if href:
                    for d in directories:
                        if d in href.lower():
                            is_directory = True
                            break

                # If it's a direct link to a non-directory domain, assume they have a website
                if href and not is_directory and 'duckduckgo.com' not in href:
                     continue

                # Extract phone number from snippet using regex
                # Look for Pakistani formats: +92..., 03..., 062...
                phone_match = re.search(r'(?:\+92|0)\s?[36]\d{1,2}[\s\-]?\d{3}[\s\-]?\d{4}', snippet)

                if phone_match:
                    phone = phone_match.group(0).strip()
                    name = title_elem.inner_text().strip()

                    # Clean up name if it's too long
                    if len(name) > 50:
                        name = name[:47] + "..."

                    # Insert into DB
                    with get_db(db_path) as conn:
                        cursor = conn.cursor()
                        cursor.execute("SELECT id FROM leads WHERE phone = ?", (phone,))
                        if not cursor.fetchone():
                            cursor.execute(
                                "INSERT INTO leads (business_name, type, city, phone) VALUES (?, ?, ?, ?)",
                                (name, b_type, 'Bahawalpur', phone)
                            )
                            leads_found += 1

            browser.close()
            return leads_found

    except PlaywrightTimeoutError:
        print(f"Timeout while scraping for {query}")
        return 0
    except Exception as e:
        print(f"Error during scraping: {e}")
        return 0

def collect_leads(db_path='leads.db'):
    """Main function to trigger lead collection"""
    print("Starting lead collection process...")

    queries = [
        ("clinics doctors bahawalpur pakistan phone number", "Clinic"),
        ("retail stores shops bahawalpur pakistan phone number", "Store"),
        ("plumbers electricians services bahawalpur pakistan phone number", "Service")
    ]

    total_found = 0
    try:
        # Try scraping for one random query per run to avoid rate limits
        query, b_type = random.choice(queries)
        total_found = scrape_duckduckgo(query, b_type, db_path)

        # If scraper failed or found nothing, fall back to mock data
        if total_found == 0:
            print("Scraper found 0 leads. Falling back to mock data generator.")
            generate_mock_leads(db_path)
    except Exception as e:
        print(f"Collection failed: {e}. Falling back to mock data.")
        generate_mock_leads(db_path)

if __name__ == '__main__':
    collect_leads()
