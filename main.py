#!/usr/bin/env python
import os
import sys
import hashlib
import requests
import warnings
from datetime import datetime
from thunderautomation.crew import Thunderautomation

warnings.filterwarnings("ignore", category=SyntaxWarning)

def fetch_html(url: str) -> str:
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        return response.text
    except Exception as e:
        raise RuntimeError(f"❌ Failed to fetch HTML from URL: {url} | Reason: {e}")

def run():
    url = "https://ourworldindata.org/artificial-intelligence#all-charts"

    # Auto-generate a unique folder name from the URL
    url_hash = hashlib.sha256(url.encode()).hexdigest()[:10]
    folder = os.path.join("screenshots", url_hash)

    # Fetch HTML content for agent context
    html = fetch_html(url)

    inputs = {
        "url": url,
        "folder": folder,
        "html": html,
        "url_hash": url_hash

    }

    try:
        Thunderautomation().crew().kickoff(inputs=inputs)
    except Exception as e:
        raise Exception(f"❌ Crew run failed: {e}")

if __name__ == "__main__":
    run()
