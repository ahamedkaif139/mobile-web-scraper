import csv
import io
import threading
import time
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from flask import Flask, jsonify, render_template, request, send_file

app = Flask(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

state = {
    "running": False,
    "stop_requested": False,
    "page": 0,
    "items": 0,
    "logs": [],
    "results": [],
    "error": None,
}

lock = threading.Lock()


def log(message):
    with lock:
        state["logs"].append(message)
        state["logs"] = state["logs"][-100:]


def get_soup(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")
    except Exception as e:
        log(f"Error fetching {url}: {e}")
        return None


def extract_data(soup, item_selector, field_mode, field_selector):
    data = []
    items = soup.select(item_selector)

    for item in items:
        if field_mode == "text":
            value = item.get_text(" ", strip=True)
        elif field_mode == "link":
            value = item.get("href", "")
            if value:
                value = urljoin(requested_base_url(), value)
        elif field_mode == "attribute":
            value = item.get(field_selector, "")
        else:
            value = item.get_text(" ", strip=True)

        if value:
            data.append([value])

    return data


def requested_base_url():
    # Only used as a fallback for converting relative links.
    with lock:
        return state.get("base_url", "")


def get_next_page(soup, current_url, next_selector):
    next_btn = soup.select_one(next_selector)

    if next_btn and next_btn.get("href"):
        return urljoin(current_url, next_btn["href"])

    return None


def scraper_thread(config):
    try:
        url = config["start_url"]
        max_pages = config["max_pages"]
        delay = config["delay"]
        item_selector = config["item_selector"]
        next_selector = config["next_selector"]
        field_mode = config["field_mode"]
        field_selector = config["field_selector"]

        with lock:
            state["base_url"] = url
            state["results"] = []
            state["logs"] = []
            state["page"] = 0
            state["items"] = 0
            state["error"] = None
            state["running"] = True
            state["stop_requested"] = False

        page = 1

        while url and page <= max_pages:
            with lock:
                if state["stop_requested"]:
                    log("Stopped by user.")
                    break
                state["page"] = page

            log(f"Scraping page {page}: {url}")

            soup = get_soup(url)
            if not soup:
                break

            page_data = extract_data(
                soup,
                item_selector,
                field_mode,
                field_selector
            )

            with lock:
                state["results"].extend(page_data)
                state["items"] = len(state["results"])

            log(f"Found {len(page_data)} items")

            next_url = get_next_page(soup, url, next_selector)
            if not next_url:
                log("No next page found. Scraping complete.")
                break

            url = next_url
            page += 1

            if page <= max_pages:
                time.sleep(delay)

        log(f"Finished. Total items: {state['items']}")

    except Exception as e:
        with lock:
            state["error"] = str(e)
        log(f"Fatal error: {e}")
    finally:
        with lock:
            state["running"] = False


@app.route("/")
def index():
    return render_template("index.html")


@app.post("/start")
def start():
    if not request.is_json:
        return jsonify({"error": "JSON required"}), 400

    data = request.get_json()

    start_url = str(data.get("start_url", "")).strip()
    item_selector = str(data.get("item_selector", "")).strip()
    next_selector = str(data.get("next_selector", "")).strip()

    if not start_url or not item_selector or not next_selector:
        return jsonify({"error": "URL, item selector and next selector are required."}), 400

    parsed = urlparse(start_url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return jsonify({"error": "Enter a valid http:// or https:// URL."}), 400

    try:
        max_pages = max(1, min(int(data.get("max_pages", 100)), 1000))
        delay = max(0.5, min(float(data.get("delay", 1.5)), 60))
    except ValueError:
        return jsonify({"error": "Invalid page limit or delay."}), 400

    with lock:
        if state["running"]:
            return jsonify({"error": "A scraper is already running."}), 409

    config = {
        "start_url": start_url,
        "item_selector": item_selector,
        "next_selector": next_selector,
        "max_pages": max_pages,
        "delay": delay,
        "field_mode": data.get("field_mode", "text"),
        "field_selector": str(data.get("field_selector", "")).strip(),
    }

    thread = threading.Thread(target=scraper_thread, args=(config,), daemon=True)
    thread.start()

    return jsonify({"ok": True})


@app.post("/stop")
def stop():
    with lock:
        if state["running"]:
            state["stop_requested"] = True
            return jsonify({"ok": True, "message": "Stop requested."})
    return jsonify({"ok": True, "message": "No scraper is running."})


@app.get("/status")
def status():
    with lock:
        return jsonify({
            "running": state["running"],
            "page": state["page"],
            "items": state["items"],
            "logs": list(state["logs"][-50:]),
            "error": state["error"],
        })


@app.get("/download")
def download():
    with lock:
        rows = list(state["results"])

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Title"])
    writer.writerows(rows)

    mem = io.BytesIO(output.getvalue().encode("utf-8-sig"))
    mem.seek(0)

    return send_file(
        mem,
        mimetype="text/csv",
        as_attachment=True,
        download_name="output.csv",
    )


if __name__ == "__main__":
    # Render provides PORT. 0.0.0.0 is required for external access.
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, threaded=True)
