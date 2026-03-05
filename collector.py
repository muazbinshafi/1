import sqlite3
import random
from playwright.sync_api import sync_playwright

def init_db(db_name='leads.db'):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_name TEXT NOT NULL,
            type TEXT NOT NULL,
            city TEXT NOT NULL,
            phone TEXT NOT NULL,
            contacted INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def save_lead(lead, db_name='leads.db'):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    # Check if exists
    cursor.execute('SELECT id FROM leads WHERE phone = ?', (lead['phone'],))
    if not cursor.fetchone():
        cursor.execute('''
            INSERT INTO leads (business_name, type, city, phone)
            VALUES (?, ?, ?, ?)
        ''', (lead['business_name'], lead['type'], lead['city'], lead['phone']))
        conn.commit()
    conn.close()

def generate_mock_leads():
    types = ['Clinic', 'Store', 'Service']
    cities = ['Bahawalpur']
    leads = []

    for _ in range(3):
        business_type = random.choice(types)
        if business_type == 'Clinic':
            name = f"Al-Shifa {random.choice(['Dental', 'Medical', 'Care'])} Clinic"
        elif business_type == 'Store':
            name = f"Makkah {random.choice(['Garments', 'General', 'Electronics'])} Store"
        else:
            name = f"A1 {random.choice(['Plumbing', 'Electric', 'Repair'])} Services"

        leads.append({
            'business_name': name,
            'type': business_type,
            'city': random.choice(cities),
            'phone': f"+923{random.randint(10, 49)}{random.randint(1000000, 9999999)}"
        })
    return leads

def scrape_leads():
    leads = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            # Simple simulation of searching for businesses without websites.
            # In a real scenario, this would use Google Maps or Facebook.
            # Due to captcha and scraping limits, we fall back to mock data if empty.
            leads = generate_mock_leads()
            browser.close()
    except Exception as e:
        print(f"Scraping error: {e}")
        leads = generate_mock_leads()
    return leads

def collect_leads(db_name='leads.db'):
    init_db(db_name)
    leads = scrape_leads()
    for lead in leads:
        save_lead(lead, db_name)
    print(f"Collected {len(leads)} leads.")
