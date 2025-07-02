from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import random

def extract_listings(driver, keyword, max_pages=None):
    listings = []
    seen_urls = set()
    page_num = 0

    keyword_encoded = keyword.replace(" ", "+")
    base_url = f"https://www.donedeal.ie/all?words={keyword_encoded}"

    while True:
        if max_pages is not None and page_num >= max_pages:
            print("📦 Reached max page limit.")
            break

        start = page_num * 30
        page_url = f"{base_url}&start={start}" if start > 0 else base_url
        print(f"📄 Scraping page {page_num + 1} → {page_url}")

        driver.get(page_url)

        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "ul[data-testid='card-list']"))
            )
        except TimeoutException:
            print("⏰ Timeout on page load.")
            break

        listing_elements = driver.find_elements(By.CSS_SELECTOR, "ul[data-testid='card-list'] li a")
        if not listing_elements:
            print("⚠️ No listings found — stopping.")
            break

        new_listings = 0

        for element in listing_elements:
            try:
                title = element.find_element(By.CSS_SELECTOR, "p[class*='Title']").text
            except NoSuchElementException:
                title = "N/A"

            try:
                price = element.find_element(By.CSS_SELECTOR, "div[class*='Price']").text
            except NoSuchElementException:
                price = "N/A"

            meta_items = element.find_elements(By.CSS_SELECTOR, "li[class*='MetaInfoItem']")
            location = meta_items[1].text if len(meta_items) > 1 else "N/A"

            link = element.get_attribute("href")
            full_link = f"https://www.donedeal.ie{link}" if link and link.startswith("/") else link or "N/A"

            if full_link not in seen_urls:
                listings.append({
                    "title": title,
                    "price": price,
                    "location": location,
                    "url": full_link
                })
                seen_urls.add(full_link)
                new_listings += 1

        if new_listings == 0:
            print("✅ No new listings found — assumed last page.")
            break

        page_num += 1
        time.sleep(random.uniform(1, 2))

    return listings
