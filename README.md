# Universal Lead Collector - Bahawalpur Edition

This application is a Lead Generation Dashboard designed to identify businesses in Bahawalpur, Punjab, Pakistan that have a phone number but lack a dedicated website.

## Features

- **Lead Collection**: Simulated collection of business leads (Clinics, Retail Stores, Services) in Bahawalpur.
- **Filtering**: Automatically filters for businesses with no website.
- **Dashboard**: Professional web interface to view leads.
- **WhatsApp Integration**: One-click "Send WhatsApp" button with a dynamic, personalized pitch based on business type.
- **Analytics**: Tracks total leads found and leads contacted.

## Installation

1.  Clone the repository.
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

1.  Start the server:
    ```bash
    uvicorn main:app --reload
    ```
2.  Open your browser and navigate to:
    `http://localhost:8000`

## Structure

- `main.py`: FastAPI backend handling API endpoints and serving the dashboard.
- `collector.py`: Logic for collecting leads (currently uses mock data for demonstration).
- `static/`: Contains the HTML, CSS, and JavaScript for the frontend.

## Extending

To use real data from Google Maps:
1.  Obtain a Google Places API Key.
2.  Update `collector.py` to use the `googlemaps` Python client.
3.  Uncomment the integration code in `collector.py`.
