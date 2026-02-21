# Universal Lead Collector 🚀

A powerful lead generation dashboard designed to identify businesses in **Bahawalpur** (Clinics, Stores, Services) that lack websites but have phone numbers.

## Features
- **Smart Search:** Finds local businesses missing a digital presence.
- **Auto-Filtering:** Keeps only high-quality leads (Phone ✅, Website ❌).
- **One-Click Outreach:** Pre-filled, personalized WhatsApp messages based on business type.
- **Auto-Replenish:** Automatically collects more leads when the list runs low.
- **Analytics:** Tracks total leads found and contacted.

## Setup
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

2. Run the application:
   ```bash
   python run.py
   ```

3. Open your browser:
   Navigate to `http://localhost:5000`

## Usage
- **Refresh List:** Updates the table.
- **Scrape New Leads:** Manually triggers the collector (also runs automatically daily).
- **Send WhatsApp:** Opens WhatsApp Web with a custom pitch. The lead is automatically marked as contacted and removed from the active list.
