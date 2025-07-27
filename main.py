from scraper.donedeal_scraper import extract_listings
from utils.driver_setup import setup_driver
from utils.clean_listings import clean_listings
import pandas as pd
import os
import time
import random

def main():
    driver = setup_driver()
    keyword = "jordans"  # Change this to your desired search term
    print(f"🔍 Searching for '{keyword}' on DoneDeal...")
    
    try:
        listings = extract_listings(driver, keyword) # Runs the scraper
        if listings:
            df = pd.DataFrame(listings)
            os.makedirs("sheets", exist_ok=True)
            
            # Save raw data
            raw_excel_path = os.path.join("sheets", f"{keyword}_raw_listings.xlsx")
            df.to_excel(raw_excel_path, index=False) # Saves the raw listings to an excel file
            print(f"✅ Saved {len(listings)} raw listings to {raw_excel_path}")
            
            # Clean the data using the cleaning function
            print(f"\n🧹 Cleaning listings for '{keyword}'...")
            cleaned_df = clean_listings(df, keyword, f"{keyword}_cleaned_listings.xlsx")
            
            if len(cleaned_df) > 0:
                print(f"📊 Raw data columns: {list(df.columns)}")
                print(f"🎯 Final result: {len(cleaned_df)} relevant listings found!")
                
                # Show top 5 cheapest items
                print(f"\n💰 Top 5 cheapest {keyword} listings:")
                for i in range(min(5, len(cleaned_df))):
                    item = cleaned_df.iloc[i]
                    print(f"  {i+1}. {item['title']} - {item['price_formatted']} ({item['location']})")
                    
            else:
                print("⚠️ No relevant listings found after cleaning.")
                
        else:
            print("⚠️ No listings found.")
            
    except Exception as e:
        print(f"❌ Error during scraping: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Close the driver
        driver.quit()
        print(f"\n✅ ProfitBot scraping complete for '{keyword}'!")
        print(f"📁 Check the 'sheets' folder for:")
        print(f"   • {keyword}_raw_listings.xlsx (all scraped data)")
        print(f"   • {keyword}_cleaned_listings.xlsx (filtered & relevant only)")

if __name__ == "__main__":
    main()
