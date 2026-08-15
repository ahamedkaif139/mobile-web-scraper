# Mobile Web Scraper v2

Mobile-friendly Flask scraper based on the original repository.

## Features

- Required URL, item selector and next-page selector
- Normal HTML pagination
- Multiple extraction fields per item
- Text, href, src, arbitrary attribute and raw HTML extraction
- CSV export with UTF-8 BOM
- XLSX export using openpyxl
- JSON export with Unicode preserved
- Result preview
- Progress/status/logs
- Clear HTTP/network/selector errors
- Backward-compatible simple one-column extraction
- Mobile-friendly field builder
- Basic result-theme detection (recipe/product/article/channel)

## Run

```bash
pip install -r requirements.txt
python app.py
```

For Render:

```text
Build: pip install -r requirements.txt
Start: gunicorn app:app --bind 0.0.0.0:$PORT
```

The scraper does not execute JavaScript or infinite-scroll code and does not bypass access controls.
