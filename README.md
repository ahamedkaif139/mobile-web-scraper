# Mobile Python Web Scraper

A mobile-friendly Flask interface around the original requests + BeautifulSoup pagination scraper.

## Run locally

pip install -r requirements.txt
python app.py

## Render

Create a Render Web Service from this GitHub repository.

Build:
pip install -r requirements.txt

Start:
gunicorn app:app --bind 0.0.0.0:$PORT

The free plan is suitable for testing. Do not use it as a permanent high-volume scraping service.

## Usage

1. Enter a page URL.
2. Enter the CSS selector for each item.
3. Enter the CSS selector for the next-page link.
4. Set maximum pages and delay.
5. Choose text, href, or an HTML attribute.
6. Start scraping.
7. Download output.csv when finished.

Only scrape sites you are permitted to access and respect their robots.txt, terms, rate limits, and applicable law.
