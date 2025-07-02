import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from scraper.donedeal_scraper import extract_listings
from selenium.webdriver.chrome.webdriver import WebDriver
from utils.driver_setup import setup_driver

def test_extract_listings_runs_quickly():
    driver: WebDriver = setup_driver()
    listings = extract_listings(driver, "coat", max_pages=2)

    assert isinstance(listings, list)
    assert all(isinstance(item, dict) for item in listings)

    if listings:
        required_keys = {"title", "price", "location", "url"}
        assert required_keys.issubset(listings[0].keys())

    driver.quit()
