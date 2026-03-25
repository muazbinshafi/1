import re
import urllib.parse
from playwright.sync_api import sync_playwright

def collect_leads():
    """
    Scrapes DuckDuckGo HTML search for businesses in Bahawalpur
    that have a phone number but lack a website.
    """
    leads = []
    queries = [
        ("Clinic in Bahawalpur", "Clinic"),
        ("Retail Store in Bahawalpur", "Store"),
        ("Service in Bahawalpur", "Service")
    ]

    try:
        with sync_playwright() as p:
            # use chromium headless
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            for query, biz_type in queries:
                encoded_query = urllib.parse.quote(query)
                url = f"https://html.duckduckgo.com/html/?q={encoded_query}"

                try:
                    page.goto(url, timeout=30000)

                    # wait for results
                    page.wait_for_selector(".result", timeout=10000)

                    results = page.locator(".result").all()

                    for result in results:
                        try:
                            # get the title text
                            title = result.locator(".result__title").inner_text().strip()

                            # get the snippet text
                            snippet = result.locator(".result__snippet").inner_text().strip()

                            # Check if the result has a website url listed. We'll approximate this by checking
                            # the result url, and whether the snippet mentions common local directories
                            # instead of a dedicated business website.
                            # Also check for a phone number.
                            url_text = result.locator(".result__url").inner_text().strip()

                            # Extract phone number from snippet using regex
                            phone_match = re.search(r'(\+92\s?\d{3}\s?\d{7}|0\d{3}\s?\d{7}|\d{4}\s?\d{7})', snippet)

                            if phone_match:
                                phone = phone_match.group(1)

                                # A heuristic to identify if they lack a dedicated website:
                                # if the URL points to a directory like facebook, instagram, olx, justdial, etc.
                                # or if it's a very generic page. We want businesses that don't have their *own* website.
                                # For simplicity, we can consider it a lead if they have a phone number.
                                # In a real scenario we'd check if the domain is a known directory.
                                is_directory = any(domain in url_text.lower() for domain in ['facebook', 'instagram', 'linkedin', 'yellowpages', 'yelp', 'justdial', 'olx', 'zameen', 'marham', 'instacare', 'oladoc'])

                                if is_directory or 'http' not in url_text:
                                    # We have a lead!
                                    lead = {
                                        "business_name": title,
                                        "type": biz_type,
                                        "city": "Bahawalpur",
                                        "phone": phone
                                    }
                                    leads.append(lead)
                        except Exception as e:
                            # Skip this result on error
                            continue

                except Exception as e:
                    print(f"Error scraping query '{query}': {e}")

            browser.close()

    except Exception as e:
        print(f"Playwright error: {e}")

    return leads

def generate_mock_leads():
    """
    Fallback function to generate mock leads data for Bahawalpur.
    """
    return [
        {
            "business_name": "Al-Shifa Clinic",
            "type": "Clinic",
            "city": "Bahawalpur",
            "phone": "+923001234567"
        },
        {
            "business_name": "Bahawalpur General Store",
            "type": "Store",
            "city": "Bahawalpur",
            "phone": "03001234568"
        },
        {
            "business_name": "A-One Plumbers",
            "type": "Service",
            "city": "Bahawalpur",
            "phone": "03001234569"
        },
        {
            "business_name": "City Medical Center",
            "type": "Clinic",
            "city": "Bahawalpur",
            "phone": "+923019876543"
        },
        {
            "business_name": "Super Electronics & Repair",
            "type": "Service",
            "city": "Bahawalpur",
            "phone": "03019876544"
        }
    ]
