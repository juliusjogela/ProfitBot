from scraper.donedeal_scraper import extract_listings
from utils.driver_setup import setup_driver
import pandas as pd
import os

def main():
    driver = setup_driver()

    # Search keyword – can be modified as needed
    keyword = "Iphone 15 Pro Max"

    # Extract listings
    print(f"Searching for '{keyword}' on DoneDeal...")
    listings = extract_listings(driver, keyword)

    if listings:
        os.makedirs("data", exist_ok=True)
        df = pd.DataFrame(listings)

        # Save as CSV
        csv_path = os.path.join("data", "listings.csv")
        df.to_csv(csv_path, index=False)

        # Save as Excel
        excel_path = os.path.join("data", "listings.xlsx")
        df.to_excel(excel_path, index=False)

        print(f"✅ Saved {len(listings)} listings to:")
        print(f"    📄 {csv_path}")
        print(f"    📊 {excel_path}")
    else:
        print("⚠️ No listings found.")


if __name__ == "__main__":
    main()
