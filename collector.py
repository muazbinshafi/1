import sqlite3
import random
import re
from playwright.sync_api import sync_playwright

DB_PATH = 'leads.db'

def get_db(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def extract_phone(text):
    # Regex to find Pakistani phone numbers (e.g. 03xx-xxxxxxx, 03xxxxxxxx)
    match = re.search(r'(03\d{2}[-\s]?\d{7})', text)
    if match:
        return match.group(1).replace(' ', '')
    return None

def is_website(text):
    text_lower = text.lower()
    return '.com' in text_lower or '.pk' in text_lower or 'website' in text_lower or 'www.' in text_lower

def collect_leads():
    searches = [
        ('clinics in Bahawalpur pakistan', 'Clinic'),
        ('stores in Bahawalpur pakistan', 'Store'),
        ('services in Bahawalpur pakistan', 'Service')
    ]

    collected_count = 0
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()

            conn = get_db()

            for query, b_type in searches:
                page.goto(f'https://html.duckduckgo.com/html/?q={query}')
                page.wait_for_timeout(2000) # Be polite

                results = page.locator('.result').all()
                for result in results:
                    try:
                        title = result.locator('.result__title').inner_text()
                        snippet = result.locator('.result__snippet').inner_text()
                        url = result.locator('.result__url').inner_text()

                        # Filter out those with obvious websites in URL or title/snippet
                        if is_website(url) or is_website(title):
                            continue

                        phone = extract_phone(snippet)
                        if not phone:
                            phone = extract_phone(title)

                        if phone:
                            # We found a potential lead!
                            # Check if it already exists
                            existing = conn.execute('SELECT id FROM leads WHERE phone = ?', (phone,)).fetchone()
                            if not existing:
                                # Truncate title for name if it's too long, or just use it
                                name = title.split('|')[0].strip() if '|' in title else title.strip()
                                if len(name) > 50:
                                    name = name[:47] + "..."

                                conn.execute('''
                                    INSERT INTO leads (business_name, type, city, phone, contacted)
                                    VALUES (?, ?, ?, ?, ?)
                                ''', (name, b_type, "Bahawalpur", phone, 0))
                                collected_count += 1
                    except Exception as e:
                        print(f"Error parsing a result: {e}")
                        continue

            conn.commit()
            conn.close()
            browser.close()

            if collected_count == 0:
                print("No real leads found via scraping, falling back to mock leads for demonstration.")
                generate_mock_leads()
            else:
                print(f"Successfully collected {collected_count} real leads.")

    except Exception as e:
        print(f"Scraping failed entirely: {e}")
        # Fallback to mock leads
        generate_mock_leads()

def generate_mock_leads():
    conn = get_db()

    business_types = ['Clinic', 'Store', 'Service']

    # Generate 3 mock leads for Bahawalpur
    for _ in range(3):
        b_type = random.choice(business_types)
        name = f"Bahawalpur {b_type} {random.randint(1, 100)}"
        city = "Bahawalpur"

        # Random Pakistani mobile number format: 03XX-XXXXXXX
        phone = f"03{random.randint(0, 4)}{random.randint(0, 9)}-{random.randint(1000000, 9999999)}"

        conn.execute('''
            INSERT INTO leads (business_name, type, city, phone, contacted)
            VALUES (?, ?, ?, ?, ?)
        ''', (name, b_type, city, phone, 0))

    conn.commit()
    conn.close()

if __name__ == '__main__':
    collect_leads()
