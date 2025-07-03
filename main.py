from scraper.donedeal_scraper import extract_listings
from utils.driver_setup import setup_driver
from utils.clean_listings import clean_listings
import pandas as pd
import os

def main():
    driver = setup_driver()

    keyword = "Iphone 16"         # Change this to your desired search term

    print(f"🔍 Searching for '{keyword}' on DoneDeal...") #Webscraper will extract listings
    listings = extract_listings(driver, keyword)

    if listings:
        os.makedirs("sheets", exist_ok=True)
        df = pd.DataFrame(listings)

        csv_path = os.path.join("sheets", "listings.csv")        # Save raw CSV
        df.to_csv(csv_path, index=False)

        print(f"✅ Saved raw listings to:")
        print(f"    📄 {csv_path}")

        # Clean the CSV file with keywords and save cleaned version
        clean_listings("listings.csv", keywords=[keyword], output_filename="cleaned_listings.xlsx")
    else:
        print("⚠️ No listings found.")


if __name__ == "__main__":
    main()
